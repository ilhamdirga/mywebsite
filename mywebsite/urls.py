from django.contrib import admin
from django.urls import path, include

from . import views
from person_detector import views as viewsPersonDetector

from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login_page, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('', views.index, name='landing-page'),
    path('person-detector/', include('person_detector.urls')),
    path('memory-tray-detector/', include('memory_tray_detector.urls')),
    path('trash-can-detector/', include('trash_can_detector.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)