from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'trash_can_detector'
urlpatterns = [
    path('', views.home, name='home'),
    path('open-cam/<int:camera_id>/', views.open_cam, name='open-cam'),
    # path('open-cam-local/<int:camera_id>/', views.open_cam_local, name='open-cam-local'),
    path('camera/', views.camera, name='camera'),
    path('camera/add', views.add_camera, name='add-camera'),
    path('camera/delete/<int:delete_id>', views.delete, name='delete-camera'),
    path('camera/delete-checkbox/', views.camera_delete_checkbox, name='delete-camera-checkbox'),
    path('camera/delete-all/', views.camera_delete_all, name='delete-camera-all'),
    path('camera/delete/', views.camera_delete_checkbox, name='delete-camera-checkbox'),
    path('camera/update/<int:update_id>', views.update, name='update-camera'),
    path('gallery/', views.gallery, name='gallery'),
    path('gallery/delete/<int:delete_id>', views.delete_gallery, name='delete-gallery'),
    path('gallery/delete-checkbox/', views.gallery_delete_checkbox, name='delete-gallery-checkbox'),
    path('gallery/delete-all/', views.gallery_delete_all, name='delete-gallery-all'),
    
]