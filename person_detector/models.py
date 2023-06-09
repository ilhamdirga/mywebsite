from django.db import models

import os

# untuk menambahkan data person
class Post(models.Model):
    name = models.CharField(max_length=20)
    fullName = models.CharField(max_length=50)
    date_created = models.DateField(auto_now_add=True)
    picture = models.ImageField(upload_to='person_detector', null=True)

    def __str__(self):
        return self.name
    
    def delete(self, *args, **kwargs):
        self.picture.delete()
        super().delete(*args, **kwargs)  

# untuk menyimpan person yang terdeteksi
class DetectedFace(models.Model):
    name = models.CharField(max_length=100)
    detected_time = models.DateTimeField()
    detected_day = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.detected_time})"
    
# Untuk menyimpan addres Ip Camera
class IpCamera(models.Model):
    name = models.CharField(max_length=20)
    ip_camera = models.CharField(max_length=50, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        get_latest_by = 'id'
