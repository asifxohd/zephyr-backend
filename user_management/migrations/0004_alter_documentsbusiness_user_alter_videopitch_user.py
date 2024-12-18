# Generated by Django 5.1.2 on 2024-10-29 11:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0003_remove_businesspreferences_social_media_links_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentsbusiness',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='video_document', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='videopitch',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='video_pitches', to=settings.AUTH_USER_MODEL),
        ),
    ]
