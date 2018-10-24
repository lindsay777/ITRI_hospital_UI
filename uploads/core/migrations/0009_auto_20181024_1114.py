# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2018-10-24 03:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_auto_20181004_1841'),
    ]

    operations = [
        migrations.RenameField(
            model_name='frax',
            old_name='fracture',
            new_name='hipFracture',
        ),
        migrations.AddField(
            model_name='frax',
            name='majorFracture',
            field=models.CharField(max_length=5, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='pub_date',
            field=models.CharField(max_length=22, null=True),
        ),
        migrations.AlterField(
            model_name='patient',
            name='age',
            field=models.CharField(max_length=3, null=True),
        ),
        migrations.AlterField(
            model_name='patient',
            name='mp',
            field=models.CharField(max_length=3, null=True),
        ),
        migrations.AlterField(
            model_name='patient',
            name='name',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
