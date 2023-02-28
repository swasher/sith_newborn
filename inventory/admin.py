import urllib.parse
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.html import format_html
from mptt.admin import MPTTModelAdmin
from inventory.models import Store, Container, Computer
from inventory.models import Component
from inventory.models import SpareType
from inventory.models import Property
from inventory.models import Manufacture
from inventory.models import Image
from inventory.models import Country
from inventory.models import History
from .forms import ImageForm, ComputerForm
from .utils import add_months


class ComputerAdminInline(admin.StackedInline):
    model = Container
    fields = ['name']
    template = "admin/inventory/component/edit_inline/stacked.html"
    max_num = 1
    extra = 0
    show_change_link = True
    verbose_name = "Компьютер"
    verbose_name_plural = "Компьютеры"

    def get_queryset(self, request):
        """
        Эта функция ограничивает отображаемые инлайн-объекты. Только kind='PC'
        """
        qs = super(ComputerAdminInline, self).get_queryset(request)
        return qs.filter(kind='PC')


class ComponentAdminInline(admin.StackedInline):
    model = Component
    fields = ['name']
    template = "admin/inventory/component/edit_inline/stacked.html"
    max_num = 1
    extra = 0
    show_change_link = True
    #can_delete = True
    verbose_name = "Устройство"
    verbose_name_plural = "Устройства"
    ordering = ['sparetype', 'name']

    # def has_add_permission(self, request, obj=None):
    #     return False

    # def has_delete_permission(self, request, obj=None):
    #     return False


class ComponentAdminInline2(ComponentAdminInline):
    show_container = True

    class Meta:
        ordering = ['sparetype.name']


class ContainerMPTTAdmin(MPTTModelAdmin):
    # specify pixel amount for this ModelAdmin only:
    mptt_level_indent = 20
    #list_display = ['name', 'kind']

    def get_queryset(self, request):
        qs = super(ContainerMPTTAdmin, self).get_queryset(request)
        return qs.exclude(kind='PC')

    inlines = [ComputerAdminInline, ComponentAdminInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Контейнер 'Помещение' не может иметь родительского контейнера 'Компьютер'.
        Удаляем из списка возможных родителей 'Компьютеры' на странице редактирования Помещений.
        """
        if db_field.name == 'parent':
            kwargs["queryset"] = Container.objects.exclude(kind='PC')
            return super(ContainerMPTTAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def response_change(self, request, obj):
        """
        Эта функция выполняется при нажатии на  кнопку ADD COMPONENT TO THIS ROOM в
        форме редактирования Помещения.
        Просто создает новый Компонент, который имеет родителем текущее Помещение
        """
        if "_add_component" in request.POST:
            app = self.model._meta.app_label
            new_instance = 'component'
            parent_model = 'container'
            parent_pk = obj._get_pk_val()

            url = reverse('admin:{}_{}_add'.format(app, new_instance))
            redirect_url = '{}?{}={}'.format(url, parent_model, parent_pk)
            return HttpResponseRedirect(redirect_url)
        else:
            return super(ContainerMPTTAdmin, self).response_change(request, obj)


class ComputerMPTTAdmin(admin.ModelAdmin):
    inlines = (ComponentAdminInline, )
    readonly_fields  = ['price', 'ram']
    list_display = ['name', 'breadcrumbs', 'get_cpu', 'ram']
    form = ComputerForm

    # DEPRECATED
    # def get_changeform_initial_data(self, request):
    #     """
    #     Начальное значение для имени Компьютера, для случая, если пользователь не загружает speccy, а
    #     добавляет Компьютер вручную
    #     """
    #     initial = {'name': Computer.default_name(self)}
    #     return initial

    def get_form(self, request, obj=None, **kwargs):
        """
        Эта функция позволяет выводить разные наборы полей для создания и для редактирования объекта Компьютер
        """
        # Proper kwargs are form, fields, exclude, formfield_callback
        if obj: # obj is not None, so this is a "change already exist" page
            #kwargs['exclude'] = ['kind', 'speccy']
            kwargs['fields'] = ['name', 'notice', 'parent', 'os', 'ram', 'installation_date', 'price']
        else: # obj is None, so this is an "add new" page
            kwargs['fields'] = ['name', 'notice', 'parent', 'speccy']

        form = super(ComputerMPTTAdmin, self).get_form(request, obj, **kwargs)
        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Контейнер 'Компьютер' не может иметь родительским контейнером 'Компьютер'.
        Удаляем из списка возможных родителей 'Компьютеры' на странице редактирования компьютеров.
        """
        if db_field.name == 'parent':
            kwargs["queryset"] = Container.objects.exclude(kind='PC')
            return super(ComputerMPTTAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def response_change(self, request, obj):
        """
        Эта функция выполняется при нажатии на  кнопку ADD COMPONENT TO THIS CONTAINER в
        форме редактирования Компьютера.
        Просто создает новый Компонент, который имеет родителем текущий Компьютер
        """
        if "_add_component" in request.POST:
            app = self.model._meta.app_label
            new_instance = 'component'
            parent_model = 'container'
            parent_pk = obj._get_pk_val()

            url = reverse('admin:{}_{}_add'.format(app, new_instance))
            redirect_url = '{}?{}={}'.format(url, parent_model, parent_pk)
            return HttpResponseRedirect(redirect_url)
        else:
            return super(ComputerMPTTAdmin, self).response_change(request, obj)

    def save_model(self, request, obj, form, change):

        # TODO DEPRECATED

        if 'speccy' in form.changed_data and Component.objects.filter(container=obj.pk).exists():
            messages.add_message(request, messages.WARNING, 'Невозможно объеденить компоненты с уже имеющимися.'
                                                            'Загрузите speccy файл в новый компьютер')
            obj.speccy = None
        super(ComputerMPTTAdmin, self).save_model(request, obj, form, change)


class PropertyAdminInline(admin.TabularInline):
    model = Property


class SpareTypeAdmin(admin.ModelAdmin):
    inlines = (PropertyAdminInline, ComponentAdminInline2)
    #fields = ['name']


class ImagesAdminInline(admin.StackedInline):
    model = Image
    #max_num = 3
    extra = 0
    #fields = ( 'image_tag', )
    #readonly_fields = ('metatag_caption',)
    #fields = ['picture', 'component']
    form = ImageForm
    template = "admin/inventory/image/edit_inline/tabular-inline-for-cloudinary-images.html"
    # Целиком инлайн рисуется в stacked.html или tabular.html, но сами строки - admin/includes/fieldset.html


class HistoryInline(admin.TabularInline):
    model = History
    extra = 0
    can_delete = False
    readonly_fields = ['date', 'full_path',]
    fields = ['date', 'full_path']
    max_num = 0

    def full_path(self, instance):
        queryset = instance.container.get_ancestors(include_self=True)
        return ' > '.join([ancestor.name for ancestor in queryset])

    full_path.short_description = "Расположение"


class ComponentAdmin(admin.ModelAdmin):

    parent_fk = None
    save_as = True

    list_display = ['name', 'sparetype', 'container']  # это поля в виде списка
    # fields = ['link_to_parent_computer', 'name', 'container', 'sparetype', 'brand', 'model', 'manufacturing_date',
    #           'assembled', 'store', 'purchase_date', ('price_uah', 'iscash'), 'invoice', 'warranty', 'serialnumber',
    #           'description', 'product_page', 'data']
    #             # это поля для формы редактирования. Перечисление всех полей необходимо для того,
    #             # чтобы поле link_to_parent_computer было в начале списка.

    fieldsets = (
        ('Данные о изделии', {
            'fields': ('link_to_parent_computer', 'name', 'container', 'sparetype', 'brand', 'model', 'manufacturing_date',
              'assembled', 'serialnumber', 'description', 'product_page',)
        }),
        ('Данные о приобретении', {
            'fields': ('store', 'purchase_date', ('price_uah', 'iscash'), 'invoice', 'warranty', 'data')
        })
    )

    readonly_fields = ['link_to_parent_computer']
    ordering = ['sparetype']
    inlines = [ImagesAdminInline, HistoryInline]

    class Media:
        css = {"all": ("hide_inline_object_name.css",)}

    """
    В django 1.10 есть специальное свойсво sava_as_continue, возможно получится его использовать, чтобы не городить огород
    def change_view(self, request, object_id, form_url='', extra_context=None):
        # Кастомная логика для случая, если пользователь нажал save_as. Нужно сделать редирект на
        # владельца и изменение имени Компонента.
        if '_saveasnew' in request.POST:
            # custom logic for save as new
            #pass
            #super(ComponentAdmin, self).change_view(request, object_id, form_url, extra_context)
            #parent_fk = Component.objects.get(pk=object_id).container_id
            #url = reverse('admin:inventory_computer_change', args=(parent_fk,))
            #return HttpResponseRedirect(url)
            pass

        super(ComponentAdmin, self).change_view(request, object_id, form_url, extra_context)
    """

    def delete_view(self, request, object_id, extra_context=None):
        """ См. response_delete
        """
        self.parent_fk = Component.objects.get(pk=object_id).container_id
        return super(ComponentAdmin, self).delete_view(request, object_id, extra_context)

    def response_delete(self, request, obj_display, obj_id):
        """ После удаление Компонента производит редирект к родительскому Компьютеру, вместо общего списка Компонентов.
        Для определения родительского Компьютера (ведь в этот момент дочернего Компонента уже не существует),
        служит функция delete_view (см. выше)
        """
        url = reverse('admin:inventory_computer_change', args=(self.parent_fk,))
        return HttpResponseRedirect(url)

    def response_change(self, request, obj):
        """
        Эта функция выполняется при нажатии на кнопку (одну из нескольких) в форме редактирования комплектующего.
        Какая кнопка была нажата, проверяется по `_load_??? in request.POST`
        """
        def return_url(self):
            opts = self.model._meta
            pk_value = obj._get_pk_val()
            preserved_filters = self.get_preserved_filters(request)

            redirect_url = reverse('admin:%s_%s_change' %
                               (opts.app_label, opts.model_name),
                               args=(pk_value,),
                               current_app=self.admin_site.name)
            redirect_url = add_preserved_filters({'preserved_filters': preserved_filters, 'opts': opts}, redirect_url)
            return HttpResponseRedirect(redirect_url)

        if "_load_component_properties" in request.POST:
            # Заполняет поле hstore согласно типу комплектующего.
            # Если поле hstore что-то содержало, то содержимое удаляется.
            obj.load_properties()
            return return_url(self)
        elif "_load_cpu_data" in request.POST:
            obj.load_cpu_data()
            return return_url(self)
        else:
            return super(ComponentAdmin, self).response_change(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        """
        Изменяет help_text у полей warranty и price_uah - показывает, когда закончится гарантия,
        и сумму по курсу на день покупки в долларах (используется API currencylayer.com)
        """
        form = super(ComponentAdmin, self).get_form(request, obj, **kwargs)

        if obj:
            """
            Вычисление конца гарантии, отображается в поле warranty.help_text
            """
            if obj.purchase_date and obj.warranty:
                buy_date = obj.purchase_date
                month_of_warranty = obj.warranty
                end_of_warranty = add_months(buy_date, month_of_warranty)
                form.base_fields['warranty'].help_text = 'End of warranty: {:%d %B %Y}'.format(end_of_warranty)

            """
            Отображение суммы в долларах в price_uah.help_text
            """
            if obj.price_usd:
                form.base_fields['price_uah'].help_text = 'Эквивалент ${} на {:%d.%b.%Y}'.format(obj.price_usd, obj.purchase_date)

            """
            Создание линка для поиска в Гугле `Brand + Model`
            """
            try:
                brand = obj.brand.name
            except AttributeError:
                brand = ''

            model = obj.model if obj.model else ''

            query = ' '.join([brand, model])
            args = {'q': query}
            param = urllib.parse.urlencode(args)
            form.base_fields['model'].help_text = "<a href='http://google.com.ua/#{}' target='_blank'>Search in Google</a>".format(param)

        return form

    def link_to_parent_computer(self, instance):
        if instance.container.kind == 'PC':
            model = 'computer'
        else:
            model = 'container'

        ancestor = instance.container.id
        url = reverse("admin:inventory_{model}_change".format(model=model), args=[ancestor])
        computer = instance.container.name
        return format_html("<a href='{}'>{}</a>", url, computer)


class CountryAdmin(admin.ModelAdmin):
    inlines = (ComponentAdminInline2, )

class StoreAdmin(admin.ModelAdmin):
    inlines = (ComponentAdminInline2, )

class ManufactureAdmin(admin.ModelAdmin):
    inlines = (ComponentAdminInline2, )

admin.site.site_header = 'SITH'

admin.site.register(Container, ContainerMPTTAdmin)
admin.site.register(Computer, ComputerMPTTAdmin)
admin.site.register(Component, ComponentAdmin)
admin.site.register(SpareType, SpareTypeAdmin)
admin.site.register(Store, StoreAdmin)
admin.site.register(Manufacture, ManufactureAdmin)
admin.site.register(Country, CountryAdmin)