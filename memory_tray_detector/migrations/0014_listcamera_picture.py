# Generated by Django 4.2.1 on 2023-05-27 10:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('memory_tray_detector', '0013_listcamera'),
    ]

    operations = [
        migrations.AddField(
            model_name='listcamera',
            name='picture',
            field=models.ImageField(null=True, upload_to='memory_tray_detector'),
        ),
    ]
