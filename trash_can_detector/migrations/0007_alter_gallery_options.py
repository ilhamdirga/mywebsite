# Generated by Django 4.2.1 on 2023-06-07 07:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trash_can_detector', '0006_alter_gallery_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='gallery',
            options={'get_latest_by': 'id'},
        ),
    ]
