# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-12-14 00:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django_hstore.fields
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0018_auto_20161115_1119'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='country',
            options={'ordering': ['country'], 'verbose_name': 'Страна', 'verbose_name_plural': 'Страны'},
        ),
        migrations.AlterField(
            model_name='component',
            name='assembled',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='inventory.Country', verbose_name='Собрано в'),
        ),
        migrations.AlterField(
            model_name='component',
            name='brand',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='inventory.Manufacture', verbose_name='Бренд'),
        ),
        migrations.AlterField(
            model_name='component',
            name='container',
            field=mptt.fields.TreeForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.Container', verbose_name='Владелец'),
        ),
        migrations.AlterField(
            model_name='component',
            name='data',
            field=django_hstore.fields.DictionaryField(blank=True, verbose_name='Характеристики изделия'),
        ),
        migrations.AlterField(
            model_name='component',
            name='description',
            field=models.TextField(blank=True, verbose_name='Примечания'),
        ),
        migrations.AlterField(
            model_name='component',
            name='iscash',
            field=models.BooleanField(default=False, verbose_name='Оплачено наличными'),
        ),
        migrations.AlterField(
            model_name='component',
            name='manufacturing_date',
            field=models.CharField(blank=True, help_text="Format: APR 2010 or Q2'2012 or 42/2014 (week/year). Please keep date format for future search ability!", max_length=20, null=True, verbose_name='Дата производства'),
        ),
        migrations.AlterField(
            model_name='component',
            name='model',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Модель'),
        ),
        migrations.AlterField(
            model_name='component',
            name='name',
            field=models.CharField(max_length=64, verbose_name='Наименование'),
        ),
        migrations.AlterField(
            model_name='component',
            name='price_uah',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Стоимость в грн', max_digits=8, null=True, verbose_name='Стоимость, грн'),
        ),
        migrations.AlterField(
            model_name='component',
            name='purchase_date',
            field=models.DateField(blank=True, null=True, verbose_name='Дата покупки'),
        ),
        migrations.AlterField(
            model_name='component',
            name='serialnumber',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='Серийный номер'),
        ),
        migrations.AlterField(
            model_name='component',
            name='sparetype',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.SpareType', verbose_name='Тип изделия'),
        ),
        migrations.AlterField(
            model_name='component',
            name='store',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='inventory.Store', verbose_name='Куплено в'),
        ),
        migrations.AlterField(
            model_name='component',
            name='warranty',
            field=models.SmallIntegerField(blank=True, help_text='месяцев', null=True, verbose_name='Гарания'),
        ),
        migrations.AlterField(
            model_name='sparetype',
            name='name',
            field=models.CharField(help_text='Это ключ, пишется английскими буквами, должен соответсвовать значению, которое возвращает парсер.', max_length=32),
        ),
    ]
