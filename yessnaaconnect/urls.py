from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from yessnaaconnect.views import home

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('espace-admin/', include('admin.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)