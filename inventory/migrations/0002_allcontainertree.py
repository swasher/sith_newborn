# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-16 12:19
from __future__ import unicode_literals

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AllContainerTree',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('inventory.container',),
            managers=[
                ('_default_manager', django.db.models.manager.Manager()),
            ],
        ),
    ]