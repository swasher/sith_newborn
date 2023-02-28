import pytz
import time

from itertools import chain
from django.http import JsonResponse
from django.db.models import Value, IntegerField, CharField
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.conf import settings
import django.utils.timezone as tz

import cloudinary
from .models import Component
from .models import Computer
from .forms import RenameForm



@login_required()
def grid(request):
    context = RequestContext(request)

    all = Component.objects.only('name', 'breadcrumbs', 'sparetype__name', 'brand__name', 'model',
                                 'manufacturing_date', 'assembled__country',
                                 'store__name', 'purchase_date', 'price_usd')\
        .prefetch_related('sparetype', 'brand', 'assembled', 'store')\
        .annotate(parentid=F('container__id'), parentkind=F('container__kind'))

    computers = Computer.objects.defer('installation_date', 'speccy')\
        .annotate(parentid=F('parent__id'))

    # девайсы - это отдельно стоящее, т.е. не входящие в состав Компьютеров (рабочих мест)
    # оборудование. Такое, как например, сетевые принтеры, комнатные коммутаторы, точки доступа и др.
    devices = Component.objects.filter(container__kind='ROOM')\
        .annotate(parentid=F('container__id'))

    todo_computers = Computer.objects.filter(notice__icontains='TODO:')
    for i in todo_computers:
        i.todo = '\n'.join([n for n in i.notice.split('\n') if 'TODO' in n])

    todo_components = Component.objects.filter(description__icontains='TODO:')
    for i in todo_components:
        i.todo = '\n'.join([n for n in i.description.split('\n') if 'TODO' in n])

    todo_items = chain(todo_computers, todo_components)


    return render_to_response('grid.html', {'all': all,
                                            'computers': computers,
                                            'devices': devices,
                                            'todo': todo_items,
                                            },
                              context)


@login_required()
def old_rename(request):
    context = RequestContext(request)
    errors = []
    debug = []
    form = {}

    if request.POST:

        form['old_key'] = request.POST.get('old_key')
        form['new_key'] = request.POST.get('new_key')

        if not form['old_key']:
            errors.append('Заполните old_key')
        if not form['new_key']:
            errors.append('Заполните new_key')
        if not errors:
            old_key = form['old_key']
            new_key = form['new_key']

            components = Component.objects.all()

            for component in components:
                if old_key in component.data:
                    component.data[new_key] = component.data.pop(old_key)
                    debug.append(component.name)
                    component.save()

            return HttpResponse("""{} -> {}: Renaming OK! Data: {} <p>
            <a href="/rename/">Еще переименовать</a>
            <a href="/">Закончить</a>
            """.format(old_key, new_key, debug))

    return render_to_response('rename.html', {'errors': errors, 'form':form}, context)


@login_required()
def rename(request):
    context = RequestContext(request)
    errors = []
    renamed = []

    if request.method == 'POST':

        form = RenameForm(request.POST)

        if form.is_valid():

            #form['sparetype'] = request.POST.get('sparetype')
            #form['old_key'] = request.POST.get('old_key')
            #form['new_key'] = request.POST.get('new_key')

            if not errors:
                sparetype = int(request.POST.get('sparetype')) # request.POST.get('sparetype') возвращает pk(int) Компонента, а form.cleaned_data['sparetype'] возвращает verbose_name(str)
                old_key = form.cleaned_data['old_key']
                new_key = form.cleaned_data['new_key']

                components = Component.objects.filter(sparetype__pk=sparetype)

                for component in components:
                    if old_key in component.data:
                        component.data[new_key] = component.data.pop(old_key)
                        renamed.append(component.name)
                        component.save()
    else:
        form = RenameForm()

    return render_to_response('rename.html', {'form': form, 'renamed': renamed}, context)


def photos(request):
    context = RequestContext(request)
    c = Component.objects.all()
    return render_to_response('photo.html', {'c': c}, context)


def get_limits():
    c = cloudinary.api.resources()
    rate_limit_remaining = int(c.rate_limit_remaining)
    rate_limit_reset_struct = c.rate_limit_reset_at  # see format there https://docs.python.org/2/library/email.util.html#email.utils.parsedate

    local_timezone = pytz.timezone(settings.TIME_ZONE)

    seconds = time.mktime(rate_limit_reset_struct)
    date_obj = datetime.fromtimestamp(seconds)
    utc = tz.make_aware(date_obj, pytz.utc)
    local = utc.astimezone(local_timezone)

    if rate_limit_remaining in range(100, 501):
        btn_color = 'btn-default'
    elif rate_limit_remaining in range(50, 99):
        btn_color = 'btn-warning'
    else:
        btn_color = 'btn-danger'

    results = {'rate_limit_remaining': rate_limit_remaining,
               'rate_limit_reset': local,
               'btn_color': btn_color}
    return JsonResponse(results)

#
# deprecated
#
# def create_init_component_breadcrumbs(request):
#     for component in Component.objects.all():
#         if component.container.kind == 'PC':
#             parent = ' > '.join(component.container.get_ancestors(include_self=False).values_list('name', flat=True))
#             pc = component.container.name.split(' ', 1)[0]
#             if parent:
#                 pc = ' > ' + pc
#             component.parent = parent + pc
#         else:
#             component.parent = ' > '.join(
#                 component.container.get_ancestors(include_self=True).values_list('name', flat=True))
#
#         component.save()
#
#     return redirect('grid')

#
# deprecated
#
# def create_init_computer_breadcrumbs(request):
#     for computer in Computer.objects.all():
#         if computer.parent:
#             computer.breadcrumbs = ' > '.join(computer.parent.get_ancestors(include_self=True).values_list('name', flat=True))
#         else:
#             computer.breadcrumbs = ''
#         computer.save()
#
#     return redirect('grid')