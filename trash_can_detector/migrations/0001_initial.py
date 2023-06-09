# Generated by Django 4.2.1 on 2023-05-24 11:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Camera',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('description', models.CharField(max_length=100, null=True)),
                ('ip_camera', models.IntegerField(null=True)),
                ('date_created', models.DateField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Gallery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('picture', models.ImageField(null=True, upload_to='memory_tray_detector')),
                ('quantity', models.IntegerField(null=True)),
                ('timestamp', models.DateTimeField()),
                ('name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trash_can_detector.camera')),
            ],
        ),
        migrations.CreateModel(
            name='CamCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(null=True)),
                ('timestamp', models.CharField(max_length=100, null=True)),
                ('name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trash_can_detector.camera')),
            ],
        ),
    ]
