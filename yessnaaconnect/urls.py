from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from yessnaaconnect.views import home

# ── Personnalisation de l'interface Django Admin ──
admin.site.site_header  = "Yess Naa Connect – Administration"
admin.site.site_title   = "Yess Naa Connect"
admin.site.index_title  = "Tableau de bord administrateur"

urlpatterns = [
    path('admin', home, name='home'),
    path('admin/', admin.site.urls),
    path('espace-admin/', include('administration.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)