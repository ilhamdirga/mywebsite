# Generated by Django 4.2.1 on 2023-05-31 01:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trash_can_detector', '0002_gallery_detected_day_alter_gallery_picture_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='camera',
            name='ip_camera',
            field=models.CharField(max_length=200, null=True),
        ),
    ]