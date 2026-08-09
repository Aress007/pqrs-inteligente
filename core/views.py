from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.http import HttpResponse
from django.core.management import call_command
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
import io
import json

@never_cache
def inicio(request):
    return render(request, 'core/inicio.html')

def ayuda(request):
    return render(request, 'core/ayuda.html')

# ============================================================
# COPIAS DE SEGURIDAD (solo para empresas)
# ============================================================
@login_required
def respaldar_bd(request):
    """Descarga un archivo JSON con todos los datos de la base de datos."""
    # Verificar que el usuario sea empresa
    try:
        perfil = request.user.perfil
        if perfil.rol != 'empresa':
            messages.warning(request, 'No tienes permiso para acceder a esta función.')
            return redirect('core:inicio')
    except:
        messages.error(request, 'Perfil no encontrado.')
        return redirect('core:inicio')

    # Crear un buffer en memoria
    buffer = io.StringIO()
    call_command('dumpdata', format='json', stdout=buffer, exclude=['contenttypes', 'auth.permission'])
    buffer.seek(0)
    data = buffer.read()
    
    response = HttpResponse(data, content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="respaldo_pqrs.json"'
    return response

@login_required
def restaurar_bd(request):
    """Restaura la base de datos desde un archivo JSON subido."""
    # Verificar que el usuario sea empresa
    try:
        perfil = request.user.perfil
        if perfil.rol != 'empresa':
            messages.warning(request, 'No tienes permiso para acceder a esta función.')
            return redirect('core:inicio')
    except:
        messages.error(request, 'Perfil no encontrado.')
        return redirect('core:inicio')

    if request.method == 'POST' and request.FILES.get('archivo'):
        try:
            archivo = request.FILES['archivo']
            # Leer el archivo subido
            data = archivo.read().decode('utf-8')
            # Crear un buffer y cargar los datos
            buffer = io.StringIO(data)
            # Usar loaddata desde el buffer
            call_command('loaddata', buffer, format='json')
            messages.success(request, "Base de datos restaurada correctamente.")
        except Exception as e:
            messages.error(request, f"Error al restaurar: {str(e)}")
        return redirect('core:inicio')
    
    return render(request, 'core/restaurar_bd.html')