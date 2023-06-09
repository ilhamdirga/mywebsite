from django.contrib import admin
from .models import Camera, CamCard, Gallery, ListCamera
# Register your models here.
admin.site.register(Camera)
admin.site.register(CamCard)
admin.site.register(Gallery)
admin.site.register(ListCamera)