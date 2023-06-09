# Generated by Django 4.2.1 on 2023-05-22 14:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('memory_tray_detector', '0005_camera_date_created'),
    ]

    operations = [
        migrations.CreateModel(
            name='CamCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='memory_tray_detector.camera')),
            ],
        ),
        migrations.DeleteModel(
            name='Gallery',
        ),
    ]
