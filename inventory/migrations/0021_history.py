# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-12-24 20:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0020_auto_20161223_0029'),
    ]

    operations = [
        migrations.CreateModel(
            name='History',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('component', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.Component')),
                ('container', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.Container')),
            ],
        ),
    ]
