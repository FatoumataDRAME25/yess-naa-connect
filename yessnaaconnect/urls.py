from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# ── Personnalisation de l'interface Django Admin ──
admin.site.site_header  = "Yess Naa Connect – Administration"
admin.site.site_title   = "Yess Naa Connect"
admin.site.index_title  = "Tableau de bord administrateur"

handler404 = 'client.views.page_404'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('client.urls')),
    path('espace-admin/', include('administration.urls')),
    path('producteur/', include('producteur.urls')),
    path('livreur/', include('livreur.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
