# -*- coding: utf-8 -*-

from time import gmtime, strftime
from django.utils import timezone
from django.conf import settings
from django.core import urlresolvers
from django.db import models
from django.db import IntegrityError
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.html import format_html
from django.db.models import Sum
from django_hstore import hstore
from mptt.models import MPTTModel, TreeForeignKey
import cloudinary
from cloudinary.models import CloudinaryField
from cloudinary.uploader import destroy
from .get_cpu_data import cpu_data
from .speccy import parse_speccy
from .utils import uah_to_usd
from .utils import human_to_bytes, bytes_to_human

import logging
logger = logging.getLogger(__name__)


KIND_CHOICES = (
    ('ORG', 'Организация'),
    ('ROOM', 'Помещение'),
    ('BOX', 'Бокс'),
    ('TBL', 'Рабочее место'),
    ('PC', 'Компьютер'),
)


class Container(MPTTModel):
    """
    Эта модель содержит древовидную структуру, в которой узлами являются помещения (или контейнеры типа шкафа) или
    компьютеры, которые, в свою очередь, являются контейнерами для комплетующих.
    """
    name = models.CharField(max_length=50, verbose_name='Название')
    kind = models.CharField(max_length=4, choices=KIND_CHOICES, null=True)
    notice = models.TextField(max_length=300, default='', blank=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = 'Помещение'
        verbose_name_plural = 'Помещения'

    def update_memory(self):
        pass

    def __str__(self):
        return self.name


class Computer(Container):
    os = models.CharField(max_length=100, blank=True)
    ram = models.CharField(max_length=20, blank=True) # TODO может это надо сделать integer для поиска
    installation_date = models.CharField(max_length=40, blank=True, null=True) # TODO это надо сделать датой
    speccy = models.FileField(upload_to='', blank=True)
    breadcrumbs = models.CharField(max_length=64, help_text='Это предвычисляемое поля для отображения в Grid', verbose_name='Расположение')

    class Meta:
        verbose_name = 'Компьютер'
        verbose_name_plural = 'Компьютеры'
        ordering = ['name']

    def __str__(self):
        return self.name

    def update_memory(self):
        """
        Предвычисление объема памяти Компьютера из входящих в него планок памяти.
        == HARDCODED: ==
        - компонент памяти должен иметь атрибут name='memory'
        - компонент памяти должен иметь ключ hstore 'Объем' со значением вида "256 MBytes"
        Вызывы:
        - память удалена:  в signals.py
        - память была перемещена из одного Компа в другой: в signals.py
        - память была добавлена или изменена вручную: в computer.save
        """
        flatten_data = list(Component.objects.filter(container=self.pk, sparetype__name='memory')
                            .values_list('data', flat=True))
        ram = bytes_to_human(sum(
            [human_to_bytes(i['Объем'] if 'Объем' in i.keys() else '0 MBytes') for i in flatten_data]
        ), base=1024)
        if self.ram != ram:
            self.ram = ram
            self.save()

    def save(self, *args, **kwargs):

        logger.info('Heroku Logging Test: Computer pk:{} saved'.format(self.pk))

        if self.speccy._file:
            xml = self.speccy.read()
            summary, devices = parse_speccy(xml)
            self.os = summary['os']
            self.cpu = summary['cpu']

            # DEPRECATED; Now we calc total RAM as total sum of every ram module
            # self.ram = summary['ram']

            self.installation_date = summary['installation_date']
            self.kind = 'PC'
            # Если пользователь не ввел название, то даем компу название по NetBIOS
            if not self.name:
                self.name = summary['user']
            self.speccy = None

            try:
                with transaction.atomic():
                    super(Computer, self).save(*args, **kwargs)
            except IntegrityError:
                # Ранее тут мог возникнуть эксепшн IntegrityError, когда поле Container.name было unique
                # Сейчас Компьютеры могут иметь одинаковые названия.
                # Это связяно с тем, что Помещения ДОЛЖНЫ иметь возможность иметь одинаковые названия, например,
                # разные офисы могут иметь свои 'Коридоры'
                pass
            else:
                manufactures = Manufacture.objects.all()
                for device in devices:
                    c = Component()
                    c.name = device['verbose']
                    c.container = self
                    c.sparetype = SpareType.objects.get(name=device['type'])
                    c.data = device['feature']

                    if 'Серийный номер' in device:
                        c.serialnumber = device['Серийный номер']

                    for manufacture in manufactures:
                        if manufacture.name.lower() in c.name.lower():
                            c.brand = manufacture
                            break
                    c.save()
                self.update_memory()
        else:
            # TODO мне кажется, это лишнее. Верхний блок выполняется, если Комп был только что создан и содержал
            # speccy. А если нет, то логично else: pass помойму, он и так нормально сохранится вызовом super чуть ниже
            # self.kind = 'PC'
            # self.speccy = None
            # super(Computer, self).save(*args, **kwargs)
            pass

        # При каждом сохранении мы обновляем поле breadcrumbs, чтобы не вычислять его в темплейте (Офис->Серверная->Стораж)
        if self.parent:
            self.breadcrumbs = ' > '.join(
                self.parent.get_ancestors(include_self=True).values_list('name', flat=True))
        else:
            self.breadcrumbs = ''

        self.update_memory()

        super(Computer, self).save(*args, **kwargs) # Call the "real" save() method.

    def _get_cpu(self):
        # == HARCODED ==
        cpu = Component.objects.filter(container_id=self.id, sparetype__name__exact='cpu')
        if cpu:
            return cpu[0]
        else:
            return None
    _get_cpu.short_description = "Процессор"
    get_cpu = property(_get_cpu)

    def _computer_price(self):
        price = self.component_set.all().aggregate(Sum('price_usd'))['price_usd__sum']
        without_price = self.component_set.all().filter(price_usd__isnull=True).count()
        html = format_html('<strong>${}</strong> and {} item without price', price, without_price) if price else '-'
        return html
    price = property(_computer_price)


class SpareType(models.Model):
    name = models.CharField(max_length=32, help_text='Это ключ, пишется английскими буквами, должен соответсвовать значению, которое возвращает парсер.', unique=True)
    name_verbose = models.CharField(max_length=32, verbose_name='Human-like название')

    class Meta:
        verbose_name = 'Тип железа'
        verbose_name_plural = 'Тип железа'
        ordering = ['name_verbose']

    def __str__(self):
        return self.name_verbose


class Property(models.Model):
    """
    Список свойств для каждого конкретного вида железа. Применяется только для заполнения новосозданного Компонента,
    при нажатии кнопки LOAD_PROPERTIES
    """
    name = models.CharField(max_length=32)
    sparetype = models.ForeignKey(SpareType)

    class Meta:
        verbose_name = 'Свойство'
        verbose_name_plural = 'Свойства'

    def __str__(self):
        return self.name


class Store(models.Model):
    name = models.CharField(max_length=64)
    address = models.CharField(max_length=128, blank=True)
    phone = models.CharField(max_length=25, blank=True)

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'

    def __str__(self):
        return self.name


class Manufacture(models.Model):
    name = models.CharField(max_length=64)

    class Meta:
        ordering = ['name']
        verbose_name = 'Вендор'
        verbose_name_plural = 'Вендоры'

    def __str__(self):
        return self.name


class Country(models.Model):
    country = models.CharField(max_length=64)

    class Meta:
        ordering = ['country']
        verbose_name = 'Страна'
        verbose_name_plural = 'Страны'

    def __str__(self):
        return self.country


class Component(models.Model):

    name = models.CharField(max_length=64, verbose_name='Наименование')
    container = TreeForeignKey(Container, verbose_name='Владелец')
    breadcrumbs = models.CharField(max_length=64, help_text='Это вычисляемое поля для отображения в Grid, потому что его вычисление в'
                                                       'темплейте очень тяжелое - для нескольких сотен компонентов'
                                                       'время загрузки темплейта Grid возрастало с ~300ms до ~2100ms')
    sparetype = models.ForeignKey(SpareType, verbose_name='Тип изделия')

    brand = models.ForeignKey(Manufacture, blank=True, null=True, verbose_name='Бренд')
    model = models.CharField(max_length=100, blank=True, null=True, verbose_name='Модель')
    manufacturing_date = models.CharField(max_length=20, blank=True, null=True, help_text="Format: APR 2010 or Q2'2012 or 42 / 14 (week / year). Please keep date format for future search ability!", verbose_name='Дата выпуска')
    assembled = models.ForeignKey(Country, blank=True, null=True, verbose_name='Собрано в')

    purchase_date = models.DateField(blank=True, null=True, verbose_name='Дата покупки')
    store = models.ForeignKey(Store, blank=True, null=True, verbose_name='Куплено в')
    warranty = models.SmallIntegerField(blank=True, null=True, help_text='месяцев', verbose_name='Гарания')
    serialnumber = models.CharField(max_length=128, blank=True, null=True, verbose_name='Серийный номер')
    description = models.TextField(blank=True, verbose_name='Примечания')
    price_uah = models.DecimalField(max_digits=8, decimal_places=2, help_text='Стоимость в грн', blank=True, null=True, verbose_name='Стоимость, грн')
    price_usd = models.DecimalField(max_digits=8, decimal_places=2, help_text='Это поле используется как help_text для поля price_uah на странице редактирования Компонента', blank=True, null=True)
    iscash = models.BooleanField(default=False, verbose_name='Оплачено наличными')
    invoice = models.CharField(max_length=64, verbose_name='Номер счета', blank=True)
    product_page = models.URLField(blank=True, verbose_name='URL на страницу продукта')

    data = hstore.DictionaryField(blank=True, verbose_name='Характеристики изделия')  # can pass attributes like null, blank, etc.
    objects = hstore.HStoreManager()

    class Meta:
        verbose_name = 'Комплектующие и устройства'
        verbose_name_plural = 'Комплектующие и устройства'

    def __str__(self):
        return self.name

    def load_properties(self):
        """
        Загрузка полей hsore для выбранного компонента. Т.е. для монитора загрузятся
        'диагональ', 'тип экрана' и.д.
        """
        properties  = Property.objects.filter(sparetype__pk=self.sparetype_id)

        data = self.data
        for prop in properties:
            if prop.name not in data:
                data[prop.name] = ''
        self.data=data
        self.save()

    def load_cpu_data(self):
        """
        Загрузка данных о процессоре с внешнего источника. Для Интела это Intel Ark, для AMD -  www.cpu-world.com
        Линк на страницу продукта должен быть указан в поле product_page
        """
        # При загрузке данных о CPU сначала удалим поля с пустым значением
        if self.data:
            removed_empty_values = dict((k, v) for k, v in self.data.items() if v)
            self.data = removed_empty_values
            self.save()

        if self.product_page:
            info = cpu_data(self.product_page)
            if info:
                #self.data = info
                for key, value in info.items():
                    self.data[key] = value
                self.save()
        else:
            pass

    def save(self, *args, **kwargs):
        # При нажатии в админке save_as мы должны сначала сохранить объект, а потом обращаться к его полям (price_uah и т.д)
        if self.pk is None:
            super(Component, self).save(*args, **kwargs) # Call the "real" save() method.

        # Вычисление цены в долларах на дату покупки
        if self.price_uah and self.purchase_date:
            item = Component.objects.get(pk=self.pk)

            # Если изменилась цена в гривнах или дата покупки - то нужно вычислять цену в USD заново
            need_recalculate = item.price_uah != self.price_uah or item.purchase_date != self.purchase_date

            if need_recalculate or not self.price_usd:
                usd = uah_to_usd(self.price_uah, self.purchase_date)
                self.price_usd = usd

        # При каждом сохранении мы обновляем поле parent, чтобы не вычислять его в темплейте (Офис->Серверная->Стораж)
        if self.container:
            if self.container.kind == 'PC':
                breadcrumbs = ' > '.join(self.container.get_ancestors(include_self=False).values_list('name', flat=True))
                pc = self.container.name.split(' ', 1)[0]
                if breadcrumbs:
                    pc = ' > ' + pc
                self.breadcrumbs = breadcrumbs + pc
            else:
                self.breadcrumbs = ' > '.join(self.container.get_ancestors(include_self=True).values_list('name', flat=True))

        # Проверяем, если self.container отличается от последнего контейнера в History,
        # то заносим в History новые данные о владельце
        was_owned = History.objects.filter(component=self.id).order_by('-date')
        if was_owned:
            previous_owner =was_owned[0].container
        else:
            previous_owner = False
        new_owner = self.container
        if previous_owner != new_owner:
            h = History()
            h.container = self.container
            h.component = self
            h.save()

        super(Component, self).save(*args, **kwargs) # Call the "real" save() method.

    # DEPRECATED but live there for future use
    # This function show how implement Property field, which calculating from hstore
    #
    # def _important_props(self):
    #
    #     class SafeDict(dict):
    #         def __missing__(self, key):
    #             return '{' + key + '}'
    #
    #     mem_string = '{Объем} + {Тип}'
    #     cpu_string = '{Сокет}'
    #
    #     #props = self.data['Объем'] + self.data['Тип']
    #     if self.sparetype.name == 'memory':
    #         data = self.data
    #         props = mem_string.format_map(SafeDict(**data))
    #     elif self.sparetype.name == 'cpu':
    #         data = self.data
    #         props = cpu_string.format_map(SafeDict(**data))
    #     else:
    #         props = ''
    #     return props
    # important_props = property(_important_props)


class History(models.Model):
    component = models.ForeignKey(Component)
    container = models.ForeignKey(Container, verbose_name='Размещение')
    date = models.DateTimeField(default=timezone.now, verbose_name='Дата')

    class Meta:
        verbose_name = 'История перемещений'
        verbose_name_plural = 'История перемещений'


class MyCloudinaryField(CloudinaryField):
    def upload_options(self, model_instance):

        tags = {'folder': 'inventory',
                'tags': [model_instance.component.name],
                'context': {'caption': model_instance.component.name,
                            'alt': model_instance.component.name,
                            }
                }

        try:
            domain = settings.DOMAIN
            url = urlresolvers.reverse('admin:inventory_component_change', args=(model_instance.component.id,))
            link = '{}{}'.format(domain, url)
        except:
            link = None

        if link:
            tags['context'].update({'link': link})

        return tags


class Image(models.Model):

    component = models.ForeignKey(Component)
    picture = MyCloudinaryField('', blank=True, null=True)

    @property
    def metatag(self):
        try:
            resource = cloudinary.api.resource(self.picture.public_id)
        except cloudinary.api.NotFound:
            return {'tag':'', 'caption':'', 'alt':''}

        try:
            tag = resource['tags'][0]
        except:
            tag = ''

        try:
            alt = resource['context']['custom']['alt']
        except:
            alt = ''

        try:
            caption = resource['context']['custom']['caption']
        except:
            caption = ''

        return {'tag':tag, 'caption':caption, 'alt':alt}

    @property
    def preview_url(self):
        picture_preview = cloudinary.CloudinaryImage(self.picture.public_id).image(format='JPG', width=100, height=100, crop='fill')
        return picture_preview

    def metatag_caption(self):
        try:
            resource = cloudinary.api.resource(self.picture.public_id)
            caption = resource['context']['custom']['caption']
        except cloudinary.api.NotFound:
            caption = ''

        return caption

    def __str__(self):
        try:
            public_id = self.picture.public_id
        except AttributeError:
            public_id = ''
        return "{} with Public_id: {}".format(self.component.name, public_id)


@receiver(post_delete, sender=Image)
def purge_cloudinary(sender, instance, **kwargs):
    """Deletes file from cloudinary
    when corresponding `Image` object is deleted.
    """
    destroy(instance.picture.public_id)