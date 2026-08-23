"""
URLs principales del proyecto PQRS-INTELIGENTE
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('empresas/', include('empresas.urls')),
    path('pqrs/', include('pqrs.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('pago/exitoso/', TemplateView.as_view(template_name='pago/exitoso.html'), name='pago_exitoso'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)