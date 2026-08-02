from django.contrib import admin
from .models import Plan, Empresa

# Registramos en el panel de administración
admin.site.register(Plan)
admin.site.register(Empresa)
