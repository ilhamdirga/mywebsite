# Generated by Django 4.2.1 on 2023-06-08 13:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('memory_tray_detector', '0018_gallery_type_tray'),
    ]

    operations = [
        migrations.AddField(
            model_name='listcamera',
            name='type_tray',
            field=models.CharField(max_length=5, null=True),
        ),
    ]
