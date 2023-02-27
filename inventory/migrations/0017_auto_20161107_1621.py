# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-11-07 16:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0016_auto_20161105_1910'),
    ]

    operations = [
        migrations.AlterField(
            model_name='component',
            name='manufacturing_date',
            field=models.CharField(blank=True, help_text='Format: APR 2010 or Q2 2012', max_length=20, null=True),
        ),
    ]