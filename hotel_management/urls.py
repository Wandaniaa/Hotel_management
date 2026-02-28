
from django.contrib import admin
from django.urls import path, include
from hotel import views
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.login_view, name='home'),
    path('admin/', admin.site.urls),
    path('hotel/', include('hotel.urls')),
     
     
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)