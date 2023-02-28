# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2023-02-28 12:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0026_auto_20170111_2046'),
    ]

    operations = [
        migrations.AlterField(
            model_name='component',
            name='manufacturing_date',
            field=models.CharField(blank=True, help_text="Format: APR 2010 or Q2'2012 or 42 / 14 (week / year). Please keep date format for future search ability!", max_length=20, null=True, verbose_name='Дата выпуска'),
        ),
        migrations.AlterField(
            model_name='computer',
            name='breadcrumbs',
            field=models.CharField(help_text='Это предвычисляемое поля для отображения в Grid', max_length=64, verbose_name='Расположение'),
        ),
        migrations.AlterField(
            model_name='container',
            name='name',
            field=models.CharField(max_length=50, verbose_name='Название'),
        ),
        migrations.AlterField(
            model_name='sparetype',
            name='name',
            field=models.CharField(help_text='Это ключ, пишется английскими буквами, должен соответсвовать значению, которое возвращает парсер.', max_length=32, unique=True),
        ),
    ]
