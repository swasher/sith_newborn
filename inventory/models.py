import sys
import cloudinary
from django.conf import settings
from django.core import urlresolvers
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete
from django.dispatch import receiver
from mptt.models import MPTTModel, TreeForeignKey
from django_hstore import hstore
from cloudinary.models import CloudinaryField
from cloudinary.uploader import destroy
from .get_cpu_data import cpu_data
from .speccy import parse_speccy
from .utils import uah_to_usd


DATATYPE_CHOICES = (
('IntegerField', 'IntegerField'),
('FloatField', 'FloatField'),
('DecimalField', 'DecimalField'),
('BooleanField', 'BooleanField'),
('CharField', 'CharField'),
('TextField', 'TextField'),
('DateField', 'DateField'),
('DateTimeField', 'DateTimeField'),
('EmailField', 'EmailField'),
('GenericIPAddressField', 'GenericIPAddressField'),
('URLField', 'URLField'),
)

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
    name = models.CharField(max_length=50, unique=True)
    kind = models.CharField(max_length=4, choices=KIND_CHOICES, null=True)
    notice = models.TextField(max_length=300, default='', blank=True)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = 'Помещение'
        verbose_name_plural = 'Помещения'

    def __str__(self):
        return self.name


class Computer(Container):
    os = models.CharField(max_length=100, blank=True)
    ram = models.CharField(max_length=20, blank=True) # TODO может это надо сделать integer для поиска
    installation_date = models.CharField(max_length=40, blank=True, null=True) # TODO это надо сделать датой
    speccy = models.FileField(upload_to='', blank=True)

    class Meta:
        verbose_name = 'Компьютер'
        verbose_name_plural = 'Компьютеры'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.speccy._file:
            # if Component.objects.filter(container=self.pk):
            #     messages.add_message(request, messages.INFO, 'Car has been sold')
            xml = self.speccy.read()
            summary, devices = parse_speccy(xml)
            self.os = summary['os']
            self.cpu = summary['cpu']
            self.ram = summary['ram']
            self.installation_date = summary['installation_date']
            self.kind = 'PC'
            self.name = '{} on {} with {}'.format(summary['user'], self.cpu, self.ram)
            self.speccy = None
            super(Computer, self).save(*args, **kwargs)

            for device in devices:
                c = Component()
                c.name = device['verbose']
                c.container = self
                c.sparetype = SpareType.objects.get(name=device['type'])
                c.data = device['feature']

                if 'serial_number' in device:
                    c.serialnumber = device['serial_number']

                manufactures = Manufacture.objects.all()
                for manufacture in manufactures:
                    if manufacture.name.lower() in c.name.lower():
                        c.brand = manufacture

                c.save()
        else:
            self.kind = 'PC'
            self.speccy = None
            super(Computer, self).save(*args, **kwargs)

    def get_ancestors_list(self):
        ancestors = self.get_ancestors()
        return '->'.join([i.name for i in ancestors])


class SpareType(models.Model):
    name = models.CharField(max_length=32, help_text='Это ключ, пишется английскими буквами, должен соответсвовать значению, возвращаемому парсером.')
    name_verbose = models.CharField(max_length=32, verbose_name='Human-like название')

    class Meta:
        verbose_name = 'Тип железа'
        verbose_name_plural = 'Тип железа'
        ordering = ['name_verbose']

    def __str__(self):
        return self.name_verbose


class Property(models.Model):
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
    phone = models.CharField(max_length=10, blank=True)

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

    def __str__(self):
        return self.country


class Component(models.Model):

    name = models.CharField(max_length=64, verbose_name='Наименование')
    container = TreeForeignKey(Container, verbose_name='Владелец')
    sparetype = models.ForeignKey(SpareType, verbose_name='Тип изделия')

    brand = models.ForeignKey(Manufacture, blank=True, null=True, verbose_name='Бренд')
    model = models.CharField(max_length=100, blank=True, null=True, verbose_name='Модель')
    manufacturing_date = models.CharField(max_length=20, blank=True, null=True, help_text='Format: APR 2010 or Q2 2012', verbose_name='Дата производства')
    assembled = models.ForeignKey(Country, blank=True, null=True, verbose_name='Собрано в')

    purchase_date = models.DateField(blank=True, null=True, verbose_name='Дата покупки')
    store = models.ForeignKey(Store, blank=True, null=True, verbose_name='Куплено в')
    warranty = models.SmallIntegerField(blank=True, null=True, help_text='месяцев', verbose_name='Гарания')
    serialnumber = models.CharField(max_length=128, blank=True, null=True, verbose_name='Серийный номер')
    description = models.TextField(blank=True, verbose_name='Примечания')
    price_uah = models.DecimalField(max_digits=8, decimal_places=2, help_text='Стоимость в грн', blank=True, null=True, verbose_name='Стоимость, грн')
    price_usd = models.DecimalField(max_digits=8, decimal_places=2, help_text='Это поле используется как help_text для поля price_uah на странице редактирования Компонента', blank=True, null=True)
    # deprecated price_uah = models.IntegerField(help_text='Стоимость в грн', blank=True, null=True)
    # deprecated price_usd = models.IntegerField(help_text='Ориентировачная стоимость в USD на момент покупки', blank=True, null=True)
    iscash = models.BooleanField(default=False, verbose_name='Оплачено наличными')
    invoice = models.CharField(max_length=64, verbose_name='Номер счета', blank=True)
    product_page = models.URLField(blank=True, verbose_name='URL на страницу продукта')

    data = hstore.DictionaryField(blank=True, verbose_name='Характеристики изделия')  # can pass attributes like null, blank, etc.

    def load_properties(self):
        """
        Загрузка полей hsore для выбранного компонента. Т.е. для монитора загрузятся 'диагональ', 'тип экрана' и.д.
        """
        properties  = Property.objects.filter(sparetype__pk=self.sparetype_id)

        data = self.data
        for prop in properties:
            if prop.name not in data:
                data[prop.name] = ''
        self.data=data
        self.save()

    def load_cpu_data(self):
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

        if self.price_uah and self.purchase_date:
            orig = Component.objects.get(pk=self.pk)
            price_is_changed = orig.price_uah != self.price_uah or orig.purchase_date != self.purchase_date

            if price_is_changed or not self.price_usd:
                usd = uah_to_usd(self.price_uah, self.purchase_date)
                self.price_usd = usd

        super(Component, self).save(*args, **kwargs) # Call the "real" save() method.


    class Meta:
        verbose_name = 'Комплектующие и устройства'
        verbose_name_plural = 'Комплектующие и устройства'

    def __str__(self):
        return self.name


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