# Generated by Django 5.0.4 on 2024-04-29 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userAuthentications', '0003_alter_customuser_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='phone_number',
            field=models.CharField(max_length=10, unique=True),
        ),
    ]
