# Generated by Django 5.1 on 2024-08-27 05:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_authentication', '0004_industry_location_investorpreferences'),
    ]

    operations = [
        migrations.AlterField(
            model_name='industry',
            name='name',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='name',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
