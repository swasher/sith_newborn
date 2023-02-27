# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-29 17:21
from __future__ import unicode_literals

import cloudinary.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0008_auto_20160927_1705'),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('picture', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True)),
                ('component', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.Component')),
            ],
        ),
    ]
