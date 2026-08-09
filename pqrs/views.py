from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, FileResponse, Http404
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from .models import Pqrs, RespuestaPqrs, HistorialPQRS
from empresas.models import Empresa
from usuarios.models import PerfilUsuario
import uuid
import csv
from .classification_service import classify_text_zero_shot

# ============================================================
# FUNCIÓN AUXILIAR PARA ENVIAR CORREOS
# ============================================================
def enviar_notificacion(destinatario, asunto, mensaje):
    """Envía un correo de notificación al destinatario."""
    if not destinatario:
        return
    try:
        send_mail(
            subject=asunto,
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario],
            fail_silently=False,
        )
        print(f"[CORREO] Enviado a {destinatario}")
    except Exception as e:
        print(f"[ERROR] No se pudo enviar correo a {destinatario}: {e}")

# ============================================================
# CREAR PQRS (con clasificación IA en el backend)
# ============================================================
def crear_pqrs(request):
    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    perfil = request.user.perfil
    todas_empresas = Empresa.objects.all()

    if perfil.rol == 'empresa':
        empresas_disponibles = [perfil.empresa] if perfil.empresa else []
        es_cliente = False
    else:
        empresas_disponibles = todas_empresas
        es_cliente = True

    if request.method == 'POST':
        asunto = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        empresa_id = request.POST.get('empresa')
        archivo = request.FILES.get('archivo')

        if not asunto or not descripcion:
            messages.error(request, 'Asunto y descripción obligatorios')
            return render(request, 'pqrs/crear.html', {
                'empresas': empresas_disponibles,
                'es_cliente': es_cliente
            })

        empresa_obj = get_object_or_404(Empresa, id=empresa_id)

        if perfil.rol == 'empresa' and empresa_obj != perfil.empresa:
            messages.error(request, 'No puedes crear PQRS para otra empresa')
            return render(request, 'pqrs/crear.html', {
                'empresas': empresas_disponibles,
                'es_cliente': es_cliente
            })

        # ============================================================
        # CLASIFICACIÓN POR IA (Hugging Face Zero-Shot)
        # ============================================================
        tipo_ia = classify_text_zero_shot(descripcion)

        codigo = f"PQRS-{uuid.uuid4().hex[:8].upper()}"

        pqrs = Pqrs.objects.create(
            codigo_radicado=codigo,
            asunto=asunto,
            descripcion=descripcion,
            tipo_detectado=tipo_ia,
            estado='Pendiente',
            id_usuario_creador=request.user,
            id_empresa=empresa_obj,
        )

        if archivo:
            pqrs.archivo = archivo
            pqrs.save()

        # ============================================================
        # NOTIFICACIÓN POR CORREO A LA EMPRESA
        # ============================================================
        # Buscar usuarios con rol empresa en la empresa destino
        usuarios_empresa = PerfilUsuario.objects.filter(empresa=empresa_obj, rol='empresa')
        for perfil_emp in usuarios_empresa:
            if perfil_emp.usuario.email:
                enviar_notificacion(
                    destinatario=perfil_emp.usuario.email,
                    asunto=f"Nueva PQRS radicada - {codigo}",
                    mensaje=f"Se ha recibido una nueva PQRS con radicado {codigo}.\n\n"
                            f"Asunto: {asunto}\n"
                            f"Descripción: {descripcion}\n\n"
                            f"Puedes gestionarla desde el dashboard."
                )

        messages.success(request, f'Radicado {codigo} creado (clasificado como {tipo_ia})')

        return redirect(
            'pqrs:mis_solicitudes' if perfil.rol == 'cliente' else 'pqrs:dashboard'
        )

    return render(request, 'pqrs/crear.html', {
        'empresas': empresas_disponibles,
        'es_cliente': es_cliente
    })

# ============================================================
# DASHBOARD (con never_cache, filtros, gráfico y exportación)
# ============================================================
@never_cache
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    perfil = request.user.perfil

    if perfil.rol != 'empresa':
        messages.warning(request, 'Acceso solo para empresas')
        return redirect('core:inicio')

    queryset = Pqrs.objects.filter(id_empresa=perfil.empresa)

    # Filtros
    q = request.GET.get('q', '')
    estado = request.GET.get('estado', '')

    if q:
        queryset = queryset.filter(
            Q(codigo_radicado__icontains=q) |
            Q(asunto__icontains=q)
        )
    if estado:
        queryset = queryset.filter(estado=estado)

    # Exportar CSV
    if request.GET.get('exportar') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="pqrs_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Radicado', 'Asunto', 'Tipo IA', 'Estado', 'Cliente', 'Fecha'])
        for p in queryset:
            writer.writerow([
                p.codigo_radicado,
                p.asunto,
                p.tipo_detectado,
                p.estado,
                p.id_usuario_creador.username,
                p.fecha_creacion.strftime('%Y-%m-%d %H:%M')
            ])
        return response

    pqrs_lista = queryset.order_by('-fecha_creacion')
    total = queryset.count()
    pendientes = queryset.filter(estado='Pendiente').count()
    en_proceso = queryset.filter(estado='En Proceso').count()
    resueltas = queryset.filter(estado='Resuelta').count()

    return render(request, 'pqrs/dashboard.html', {
        'pqrs_lista': pqrs_lista,
        'total': total,
        'pendientes': pendientes,
        'en_proceso': en_proceso,
        'resueltas': resueltas,
    })

# ============================================================
# DETALLE DE PQRS (con botón volver y mejor manejo de archivos)
# ============================================================
def detalle_pqrs(request, pqrs_id):
    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    pqrs = get_object_or_404(Pqrs, id=pqrs_id)
    respuestas = pqrs.respuestas.all().order_by('fecha_respuesta')
    perfil = request.user.perfil

    if perfil.rol == 'cliente' and pqrs.id_usuario_creador != request.user:
        messages.error(request, 'No tienes permiso')
        return redirect('pqrs:mis_solicitudes')
    if perfil.rol == 'empresa' and pqrs.id_empresa != perfil.empresa:
        messages.error(request, 'No tienes permiso')
        return redirect('pqrs:dashboard')

    if request.method == 'POST':
        texto = request.POST.get('respuesta')
        nuevo_estado = request.POST.get('estado')
        if texto:
            RespuestaPqrs.objects.create(
                id_pqrs=pqrs,
                id_usuario_responde=request.user,
                texto_respuesta=texto,
            )
            # ============================================================
            # NOTIFICACIÓN POR CORREO AL CLIENTE
            # ============================================================
            if pqrs.id_usuario_creador.email:
                enviar_notificacion(
                    destinatario=pqrs.id_usuario_creador.email,
                    asunto=f"Respuesta a tu PQRS - {pqrs.codigo_radicado}",
                    mensaje=f"Tu PQRS con radicado {pqrs.codigo_radicado} ha recibido una respuesta.\n\n"
                            f"La empresa {pqrs.id_empresa.nombre_empresa} ha respondido:\n"
                            f"{texto}\n\n"
                            f"Puedes ver el detalle en tus solicitudes."
                )
        if nuevo_estado in ['Pendiente', 'En Proceso', 'Resuelta']:
            estado_anterior = pqrs.estado
            pqrs.estado = nuevo_estado
            pqrs.save()
            # Guardar en historial
            HistorialPQRS.objects.create(
                pqrs=pqrs,
                usuario=request.user,
                estado_anterior=estado_anterior,
                estado_nuevo=nuevo_estado,
                comentario="Cambio de estado realizado por el usuario"
            )
        messages.success(request, 'Respuesta enviada')
        return redirect('pqrs:detalle', pqrs_id=pqrs.id)

    return render(request, 'pqrs/detalle.html', {
        'pqrs': pqrs,
        'respuestas': respuestas
    })

# ============================================================
# MIS SOLICITUDES (CLIENTE)
# ============================================================
@never_cache
def mis_solicitudes(request):
    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    perfil = request.user.perfil

    if perfil.rol != 'cliente':
        messages.warning(request, 'Acceso solo para clientes')
        return redirect('pqrs:dashboard')

    pqrs_lista = Pqrs.objects.filter(id_usuario_creador=request.user).order_by('-fecha_creacion')

    return render(request, 'pqrs/mis_solicitudes.html', {
        'pqrs_lista': pqrs_lista,
        'total': pqrs_lista.count(),
        'pendientes': pqrs_lista.filter(estado='Pendiente').count(),
        'en_proceso': pqrs_lista.filter(estado='En Proceso').count(),
        'resueltas': pqrs_lista.filter(estado='Resuelta').count(),
    })

# ============================================================
# DESCARGA FORZADA DE ARCHIVO
# ============================================================
def descargar_archivo(request, pqrs_id):
    pqrs = get_object_or_404(Pqrs, id=pqrs_id)
    if not pqrs.archivo:
        raise Http404
    if not request.user.is_authenticated:
        raise Http404
    perfil = request.user.perfil
    if perfil.rol == 'cliente' and pqrs.id_usuario_creador != request.user:
        raise Http404
    if perfil.rol == 'empresa' and pqrs.id_empresa != perfil.empresa:
        raise Http404
    return FileResponse(pqrs.archivo.open(), as_attachment=True, filename=pqrs.archivo.name)

# ============================================================
# EDITAR RESPUESTA
# ============================================================
@login_required
def editar_respuesta(request, respuesta_id):
    respuesta = get_object_or_404(RespuestaPqrs, id=respuesta_id)
    
    if respuesta.id_usuario_responde != request.user:
        messages.error(request, 'No tienes permiso para editar esta respuesta.')
        return redirect('pqrs:detalle', pqrs_id=respuesta.id_pqrs.id)
    
    if request.method == 'POST':
        nuevo_texto = request.POST.get('texto_respuesta', '').strip()
        if nuevo_texto:
            respuesta.texto_respuesta = nuevo_texto
            respuesta.save()
            messages.success(request, 'Respuesta actualizada correctamente.')
        else:
            messages.error(request, 'El texto de la respuesta no puede estar vacío.')
        return redirect('pqrs:detalle', pqrs_id=respuesta.id_pqrs.id)
    
    return render(request, 'pqrs/editar_respuesta.html', {'respuesta': respuesta})

# ============================================================
# ELIMINAR RESPUESTA
# ============================================================
@login_required
def eliminar_respuesta(request, respuesta_id):
    respuesta = get_object_or_404(RespuestaPqrs, id=respuesta_id)
    if respuesta.id_usuario_responde != request.user:
        messages.error(request, 'No tienes permiso para eliminar esta respuesta.')
        return redirect('pqrs:detalle', pqrs_id=respuesta.id_pqrs.id)
    
    pqrs_id = respuesta.id_pqrs.id
    if request.method == 'POST':
        respuesta.delete()
        messages.success(request, 'Respuesta eliminada correctamente.')
        return redirect('pqrs:detalle', pqrs_id=pqrs_id)
    
    return redirect('pqrs:detalle', pqrs_id=pqrs_id)

