# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2018-10-24 07:28
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20181024_1114'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patient',
            name='filename',
        ),
    ]