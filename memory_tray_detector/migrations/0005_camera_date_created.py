# Generated by Django 4.2.1 on 2023-05-22 09:47

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('memory_tray_detector', '0004_alter_gallery_picture'),
    ]

    operations = [
        migrations.AddField(
            model_name='camera',
            name='date_created',
            field=models.DateField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
