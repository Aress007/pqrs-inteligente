from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, FileResponse, Http404
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt
from .models import Pqrs, RespuestaPqrs, HistorialPQRS, ChatMensaje
from empresas.models import Empresa
from usuarios.models import PerfilUsuario
from .classification_service import classify_text_zero_shot
from .ia_service import chat_bot
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from io import BytesIO
from datetime import datetime
import uuid
import csv
import os
import math


# ============================================================
# FUNCIÓN AUXILIAR PARA ENVIAR CORREOS
# ============================================================

def enviar_notificacion(
    destinatario,
    asunto,
    mensaje,
    context=None
):
    """
    Envía un correo HTML utilizando SendGrid
    y una plantilla de Django.
    """

    if not destinatario:
        print("[CORREO] No se indicó destinatario.")
        return False

    if not settings.SENDGRID_API_KEY:
        print("[CORREO] SENDGRID_API_KEY no está configurada.")
        return False

    try:

        from django.template.loader import render_to_string
        from django.utils.html import strip_tags

        # ----------------------------------------------------
        # CONTEXTO PARA LA PLANTILLA
        # ----------------------------------------------------

        context = context or {}

        context.setdefault(
            "mensaje",
            mensaje
        )

        context.setdefault(
            "asunto",
            asunto
        )

        context.setdefault(
            "site_name",
            "PQRS Inteligente"
        )

        # ----------------------------------------------------
        # GENERAR HTML
        # ----------------------------------------------------

        html_content = render_to_string(
            "usuarios/email_notificacion.html",
            context
        )

        text_content = strip_tags(
            html_content
        )

        # ----------------------------------------------------
        # CREAR CORREO
        # ----------------------------------------------------

        email = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=destinatario,
            subject=asunto,
            plain_text_content=text_content,
            html_content=html_content,
        )

        # ----------------------------------------------------
        # ENVIAR CON SENDGRID
        # ----------------------------------------------------

        sg = SendGridAPIClient(
            settings.SENDGRID_API_KEY
        )

        response = sg.send(email)

        if 200 <= response.status_code < 300:

            print(
                f"[CORREO] HTML enviado correctamente a "
                f"{destinatario} "
                f"(SendGrid {response.status_code})"
            )

            return True

        print(
            f"[ERROR] SendGrid respondió con "
            f"status {response.status_code}"
        )

        return False

    except Exception as e:

        print(
            f"[ERROR] No se pudo enviar correo a "
            f"{destinatario}: {e}"
        )

        return False

# ============================================================
# CREAR PQRS
# ============================================================

def crear_pqrs(request):

    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    perfil = request.user.perfil
    todas_empresas = Empresa.objects.all()

    if perfil.rol == 'empresa':

        empresas_disponibles = [
            perfil.empresa
        ] if perfil.empresa else []

        es_cliente = False

    else:

        empresas_disponibles = todas_empresas
        es_cliente = True

    if request.method == 'POST':

        asunto = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        empresa_id = request.POST.get('empresa')
        archivo = request.FILES.get('archivo')
        
        if archivo:
            ext = os.path.splitext(archivo.name)[1].lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx']
            if ext not in valid_extensions:
                messages.error(request, 'Formato de archivo no permitido. Solo: JPG, PNG, PDF, DOC, DOCX.')
                return render(request, 'pqrs/crear.html', {'empresas': empresas_disponibles, 'es_cliente': es_cliente})

        if not asunto or not descripcion:

            messages.error(
                request,
                'Asunto y descripción obligatorios'
            )

            return render(
                request,
                'pqrs/crear.html',
                {
                    'empresas': empresas_disponibles,
                    'es_cliente': es_cliente
                }
            )

        empresa_obj = get_object_or_404(
            Empresa,
            id=empresa_id
        )

        if (
            perfil.rol == 'empresa'
            and empresa_obj != perfil.empresa
        ):

            messages.error(
                request,
                'No puedes crear PQRS para otra empresa'
            )

            return render(
                request,
                'pqrs/crear.html',
                {
                    'empresas': empresas_disponibles,
                    'es_cliente': es_cliente
                }
            )

        # ====================================================
        # CLASIFICACIÓN POR IA
        # ====================================================

        tipo_ia = classify_text_zero_shot(
            descripcion
        )

        codigo = (
            f"PQRS-{uuid.uuid4().hex[:8].upper()}"
        )

        pqrs = Pqrs.objects.create(
            codigo_radicado=codigo,
            asunto=asunto,
            descripcion=descripcion,
            tipo_detectado=tipo_ia,
            estado='Pendiente',
            id_usuario_creador=request.user,
            id_empresa=empresa_obj,
        )

        # ====================================================
        # GUARDAR ARCHIVO
        # ====================================================

        if archivo:

            pqrs.archivo = archivo
            pqrs.save()

        # ====================================================
        # HISTORIAL
        # ====================================================

        HistorialPQRS.objects.create(
            pqrs=pqrs,
            usuario=request.user,
            estado_anterior=None,
            estado_nuevo='Pendiente',
            comentario="PQRS creada"
        )

        # ====================================================
        # NOTIFICACIÓN A LA EMPRESA
        # ====================================================

        usuarios_empresa = PerfilUsuario.objects.filter(
            empresa=empresa_obj,
            rol='empresa'
        )

        for perfil_emp in usuarios_empresa:

            if perfil_emp.usuario.email:

                enviar_notificacion(
                    destinatario=perfil_emp.usuario.email,
                    asunto=(
                        f"Nueva PQRS radicada - {codigo}"
                    ),
                    mensaje=(
                        f"Se ha recibido una nueva PQRS "
                        f"con radicado {codigo}."
                    ),
                    context={
                        "titulo": "Nueva PQRS radicada",
                        "nombre_usuario": (
                            perfil_emp.usuario.get_full_name()
                            or perfil_emp.usuario.username
                        ),
                        "mensaje_intro": (
                            f"Se ha recibido una nueva PQRS "
                            f"con radicado {codigo}."
                        ),
                        "radicado": pqrs.codigo_radicado,
                        "asunto": pqrs.asunto,
                        "tipo": pqrs.tipo_detectado,
                        "estado": pqrs.estado,
                        "descripcion": pqrs.descripcion,
                        "respuesta_texto": "",
                        "link_url": request.build_absolute_uri(
                            reverse(
                                'pqrs:detalle',
                                kwargs={'pqrs_id': pqrs.id}
                            )
                        ),
                    }
                )

        messages.success(
            request,
            f'Radicado {codigo} creado '
            f'(clasificado como {tipo_ia})'
        )

        return redirect(
            'pqrs:mis_solicitudes'
            if perfil.rol == 'cliente'
            else 'pqrs:dashboard'
        )

    return render(
        request,
        'pqrs/crear.html',
        {
            'empresas': empresas_disponibles,
            'es_cliente': es_cliente
        }
    )


# ============================================================
# DASHBOARD
# ============================================================

@never_cache
def dashboard(request):

    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    perfil = request.user.perfil

    if perfil.rol != 'empresa':

        messages.warning(
            request,
            'Acceso solo para empresas'
        )

        return redirect(
            'pqrs:mis_solicitudes'
        )

    queryset = Pqrs.objects.filter(
        id_empresa=perfil.empresa
    )

    q = request.GET.get('q', '')
    estado = request.GET.get('estado', '')

    if q:

        queryset = queryset.filter(
            Q(codigo_radicado__icontains=q) |
            Q(asunto__icontains=q)
        )

    if estado:

        queryset = queryset.filter(
            estado=estado
        )

    if request.GET.get('exportar') == 'csv':

        response = HttpResponse(
            content_type='text/csv'
        )

        response['Content-Disposition'] = (
            'attachment; filename="pqrs_report.csv"'
        )

        writer = csv.writer(response)

        writer.writerow([
            'Radicado',
            'Asunto',
            'Tipo IA',
            'Estado',
            'Cliente',
            'Fecha'
        ])

        for p in queryset:

            writer.writerow([
                p.codigo_radicado,
                p.asunto,
                p.tipo_detectado,
                p.estado,
                p.id_usuario_creador.username,
                p.fecha_creacion.strftime(
                    '%Y-%m-%d %H:%M'
                )
            ])

        return response

    pqrs_lista = queryset.order_by(
        '-fecha_creacion'
    )

    total = queryset.count()

    pendientes = queryset.filter(
        estado='Pendiente'
    ).count()

    en_proceso = queryset.filter(
        estado='En Proceso'
    ).count()

    resueltas = queryset.filter(
        estado='Resuelta'
    ).count()

    return render(
        request,
        'pqrs/dashboard.html',
        {
            'pqrs_lista': pqrs_lista,
            'total': total,
            'pendientes': pendientes,
            'en_proceso': en_proceso,
            'resueltas': resueltas,
        }
    )


# ============================================================
# DETALLE DE PQRS
# ============================================================

def detalle_pqrs(request, pqrs_id):

    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    pqrs = get_object_or_404(
        Pqrs,
        id=pqrs_id
    )

    respuestas = pqrs.respuestas.all().order_by(
        'fecha_respuesta'
    )

    perfil = request.user.perfil

    # ========================================================
    # PERMISOS
    # ========================================================

    if (
        perfil.rol == 'cliente'
        and pqrs.id_usuario_creador != request.user
    ):

        messages.error(
            request,
            'No tienes permiso'
        )

        return redirect(
            'pqrs:mis_solicitudes'
        )

    if (
        perfil.rol == 'empresa'
        and pqrs.id_empresa != perfil.empresa
    ):

        messages.error(
            request,
            'No tienes permiso'
        )

        return redirect(
            'pqrs:dashboard'
        )

    # ========================================================
    # POST
    # ========================================================

    if request.method == 'POST':

        if pqrs.estado == 'Resuelta':

            messages.warning(
                request,
                'Esta PQRS ya está resuelta y cerrada. '
                'No se permiten más respuestas.'
            )

            return redirect(
                'pqrs:detalle',
                pqrs_id=pqrs.id
            )

        texto = request.POST.get(
            'respuesta'
        )

        nuevo_estado = request.POST.get(
            'estado'
        )

        archivo = request.FILES.get(
            'archivo'
        )
        
        if archivo:
            ext = os.path.splitext(archivo.name)[1].lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx']

            if ext not in valid_extensions:
                messages.error(
                    request,
                    'Formato de archivo no permitido. Solo: JPG, PNG, PDF, DOC, DOCX.'
                )

                return redirect(
                    'pqrs:detalle',
                    pqrs_id=pqrs.id
                )

        estado_anterior = pqrs.estado

        # ====================================================
        # GUARDAR RESPUESTA
        # ====================================================

        if texto:

            respuesta = RespuestaPqrs.objects.create(
                id_pqrs=pqrs,
                id_usuario_responde=request.user,
                texto_respuesta=texto,
            )

            if archivo:

                respuesta.archivo = archivo
                respuesta.save()

            HistorialPQRS.objects.create(
                pqrs=pqrs,
                usuario=request.user,
                estado_anterior=estado_anterior,
                estado_nuevo=pqrs.estado,
                comentario="Respuesta enviada"
            )

            # =================================================
            # CLIENTE RESPONDE → EMPRESA
            # =================================================

            if perfil.rol == 'cliente':

                usuarios_empresa = (
                    PerfilUsuario.objects.filter(
                        empresa=pqrs.id_empresa,
                        rol='empresa'
                    )
                )

                for perfil_emp in usuarios_empresa:

                    if perfil_emp.usuario.email:

                        enviar_notificacion(
                            destinatario=perfil_emp.usuario.email,
                            asunto=f"Nuevo mensaje del cliente - {pqrs.codigo_radicado}",
                            mensaje=(
                                f"El cliente ha respondido la PQRS "
                                f"{pqrs.codigo_radicado}."
                            ),
                            context={
                                "titulo": "Nueva respuesta del cliente",
                                "nombre_usuario": (
                                    perfil_emp.usuario.get_full_name()
                                    or perfil_emp.usuario.username
                                ),
                                "mensaje_intro": (
                                    f"El cliente ha respondido la PQRS "
                                    f"{pqrs.codigo_radicado}."
                                ),
                                "radicado": pqrs.codigo_radicado,
                                "asunto": pqrs.asunto,
                                "tipo": pqrs.tipo_detectado,
                                "estado": pqrs.estado,
                                "descripcion": pqrs.descripcion,
                                "respuesta_texto": texto,
                                "link_url": request.build_absolute_uri(
                                    reverse(
                                        'pqrs:detalle',
                                        kwargs={'pqrs_id': pqrs.id}
                                    )
                                ),
                            }
                        )
            # =================================================
            # EMPRESA RESPONDE → CLIENTE
            # =================================================

            elif perfil.rol == 'empresa':

                if pqrs.id_usuario_creador.email:

                    enviar_notificacion(
                        destinatario=pqrs.id_usuario_creador.email,
                        asunto=f"Respuesta a tu PQRS - {pqrs.codigo_radicado}",
                        mensaje=(
                            f"Tu PQRS con radicado {pqrs.codigo_radicado} "
                            f"ha recibido una nueva respuesta."
                        ),
                        context={
                            "titulo": "Respuesta a tu PQRS",
                            "nombre_usuario": (
                                pqrs.id_usuario_creador.get_full_name()
                                or pqrs.id_usuario_creador.username
                            ),
                            "mensaje_intro": (
                                f"Tu PQRS con radicado "
                                f"{pqrs.codigo_radicado} "
                                f"ha recibido una nueva respuesta."
                            ),
                            "radicado": pqrs.codigo_radicado,
                            "asunto": pqrs.asunto,
                            "tipo": pqrs.tipo_detectado,
                            "estado": pqrs.estado,
                            "descripcion": pqrs.descripcion,
                            "respuesta_texto": texto,
                            "link_url": request.build_absolute_uri(
                                reverse(
                                    'pqrs:detalle',
                                    kwargs={'pqrs_id': pqrs.id}
                                )
                            ),
                        }
                    )

        # ====================================================
        # CAMBIO DE ESTADO
        # ====================================================

        if nuevo_estado in [
            'Pendiente',
            'En Proceso',
            'Resuelta'
        ]:

            if nuevo_estado != estado_anterior:

                pqrs.estado = nuevo_estado

                if nuevo_estado == 'Resuelta':

                    pqrs.fecha_cierre = timezone.now()

                else:

                    pqrs.fecha_cierre = None

                pqrs.save()

                HistorialPQRS.objects.create(
                    pqrs=pqrs,
                    usuario=request.user,
                    estado_anterior=estado_anterior,
                    estado_nuevo=nuevo_estado,
                    comentario=(
                        f"Estado cambiado: "
                        f"{estado_anterior} → "
                        f"{nuevo_estado}"
                    )
                )

                if nuevo_estado == 'Resuelta':

                    HistorialPQRS.objects.create(
                        pqrs=pqrs,
                        usuario=request.user,
                        estado_anterior=estado_anterior,
                        estado_nuevo='Resuelta',
                        comentario="PQRS cerrada"
                    )

        messages.success(
            request,
            'Respuesta enviada'
        )

        return redirect(
            'pqrs:detalle',
            pqrs_id=pqrs.id
        )

    # ========================================================
    # SLA
    # ========================================================

    tiempo_transcurrido = None
    porcentaje = None
    tiempo_restante = None
    alerta = None

    SLA_HORAS = 72

    if pqrs.estado != 'Resuelta':

        ahora = timezone.now()

        delta = ahora - pqrs.fecha_creacion

        horas = (
            delta.total_seconds() / 3600
        )

        dias = int(
            horas // 24
        )

        horas_extra = int(
            horas % 24
        )

        horas_restantes = max(
            0,
            SLA_HORAS - horas
        )

        dias_restantes = int(
            horas_restantes // 24
        )

        horas_restantes_extra = int(
            horas_restantes % 24
        )

        porcentaje = min(
            100,
            int(
                (horas / SLA_HORAS) * 100
            )
        )

        if horas >= SLA_HORAS:

            alerta = 'vencida'

        elif horas >= SLA_HORAS * 0.8:

            alerta = 'proxima_a_vencer'

        else:

            alerta = 'dentro_plazo'

        tiempo_transcurrido = (
            f"{dias} días, "
            f"{horas_extra} horas"
        )

        tiempo_restante = (
            f"{dias_restantes} días, "
            f"{horas_restantes_extra} horas"
        )

    context = {
        'pqrs': pqrs,
        'respuestas': respuestas,
        'tiempo_transcurrido': tiempo_transcurrido,
        'porcentaje': porcentaje,
        'tiempo_restante': tiempo_restante,
        'alerta': alerta,
    }

    return render(
        request,
        'pqrs/detalle.html',
        context
    )


# ============================================================
# MIS SOLICITUDES
# ============================================================

@never_cache
def mis_solicitudes(request):

    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    perfil = request.user.perfil

    if perfil.rol != 'cliente':

        messages.warning(
            request,
            'Acceso solo para clientes'
        )

        return redirect(
            'pqrs:dashboard'
        )

    pqrs_lista = Pqrs.objects.filter(
        id_usuario_creador=request.user
    ).order_by(
        '-fecha_creacion'
    )

    return render(
        request,
        'pqrs/mis_solicitudes.html',
        {
            'pqrs_lista': pqrs_lista,
            'total': pqrs_lista.count(),
            'pendientes': pqrs_lista.filter(
                estado='Pendiente'
            ).count(),
            'en_proceso': pqrs_lista.filter(
                estado='En Proceso'
            ).count(),
            'resueltas': pqrs_lista.filter(
                estado='Resuelta'
            ).count(),
        }
    )


# ============================================================
# DESCARGA FORZADA DE ARCHIVO
# ============================================================

def descargar_archivo(request, pqrs_id):

    pqrs = get_object_or_404(
        Pqrs,
        id=pqrs_id
    )

    if not pqrs.archivo:
        raise Http404

    if not request.user.is_authenticated:
        raise Http404

    perfil = request.user.perfil

    if (
        perfil.rol == 'cliente'
        and pqrs.id_usuario_creador != request.user
    ):

        raise Http404

    if (
        perfil.rol == 'empresa'
        and pqrs.id_empresa != perfil.empresa
    ):

        raise Http404

    return FileResponse(
        pqrs.archivo.open(),
        as_attachment=True,
        filename=pqrs.archivo.name
    )


# ============================================================
# EDITAR RESPUESTA
# ============================================================

@login_required
def editar_respuesta(request, respuesta_id):

    respuesta = get_object_or_404(
        RespuestaPqrs,
        id=respuesta_id
    )

    if respuesta.id_usuario_responde != request.user:

        messages.error(
            request,
            'No tienes permiso para editar esta respuesta.'
        )

        return redirect(
            'pqrs:detalle',
            pqrs_id=respuesta.id_pqrs.id
        )

    if request.method == 'POST':

        nuevo_texto = request.POST.get(
            'texto_respuesta',
            ''
        ).strip()

        if nuevo_texto:

            respuesta.texto_respuesta = nuevo_texto
            respuesta.save()

            messages.success(
                request,
                'Respuesta actualizada correctamente.'
            )

        else:

            messages.error(
                request,
                'El texto de la respuesta no puede estar vacío.'
            )

        return redirect(
            'pqrs:detalle',
            pqrs_id=respuesta.id_pqrs.id
        )

    return render(
        request,
        'pqrs/editar_respuesta.html',
        {
            'respuesta': respuesta
        }
    )


# ============================================================
# ELIMINAR RESPUESTA
# ============================================================

@login_required
def eliminar_respuesta(request, respuesta_id):

    respuesta = get_object_or_404(
        RespuestaPqrs,
        id=respuesta_id
    )

    if respuesta.id_usuario_responde != request.user:

        messages.error(
            request,
            'No tienes permiso para eliminar esta respuesta.'
        )

        return redirect(
            'pqrs:detalle',
            pqrs_id=respuesta.id_pqrs.id
        )

    pqrs_id = respuesta.id_pqrs.id

    if request.method == 'POST':

        respuesta.delete()

        messages.success(
            request,
            'Respuesta eliminada correctamente.'
        )

        return redirect(
            'pqrs:detalle',
            pqrs_id=pqrs_id
        )

    return redirect(
        'pqrs:detalle',
        pqrs_id=pqrs_id
    )


# ============================================================
# CHATBOT
# ============================================================

@xframe_options_exempt
def chatbot_view(request):

    es_embed = request.GET.get(
        "embed"
    ) == "1"

    if not request.user.is_authenticated:

        return render(
            request,
            "pqrs/chatbot.html",
            {
                "mensajes": [],
                "es_embed": es_embed,
                "no_autenticado": True,
            }
        )

    if request.method == "POST":

        mensaje = request.POST.get(
            "mensaje",
            ""
        ).strip()

        if mensaje:

            ChatMensaje.objects.create(
                usuario=request.user,
                rol="usuario",
                mensaje=mensaje
            )

            pqrs_encontrada = None

            perfil = request.user.perfil

            if perfil.rol == 'cliente':

                pqrs_query = Pqrs.objects.filter(
                    id_usuario_creador=request.user
                )

            else:  # empresa

                pqrs_query = Pqrs.objects.filter(
                    id_empresa=perfil.empresa
                )

            for pqrs in pqrs_query:

                if (
                    pqrs.codigo_radicado.lower()
                    in mensaje.lower()
                ):

                    pqrs_encontrada = pqrs
                    break

            if pqrs_encontrada:

                contexto = f"""
El usuario está consultando una PQRS que existe en el sistema.

Radicado: {pqrs_encontrada.codigo_radicado}
Asunto: {pqrs_encontrada.asunto}
Descripción: {pqrs_encontrada.descripcion}
Tipo detectado: {pqrs_encontrada.tipo_detectado}
Estado actual: {pqrs_encontrada.estado}
Fecha de radicación: {pqrs_encontrada.fecha_creacion.strftime('%Y-%m-%d %H:%M')}

Respuestas registradas:
"""

                respuestas_pqrs = (
                    pqrs_encontrada.respuestas.all()
                    .order_by("fecha_respuesta")
                )

                if respuestas_pqrs.exists():

                    for respuesta_pqrs in respuestas_pqrs:

                        contexto += (
                            f"\n- "
                            f"{respuesta_pqrs.fecha_respuesta.strftime('%Y-%m-%d %H:%M')}: "
                            f"{respuesta_pqrs.texto_respuesta}"
                        )

                else:

                    contexto += (
                        "\nNo hay respuestas registradas todavía."
                    )

            else:

                contexto = """
No se encontró ningún radicado perteneciente al usuario
que coincida con la consulta.

No inventes información sobre radicados.

Si el usuario pregunta por un radicado que no aparece,
indícale que no fue encontrado o que debe verificar
el número de radicado.
"""

            historial_mensajes = (
                ChatMensaje.objects
                .filter(
                    usuario=request.user
                )
                .order_by("-fecha")[:20]
            )

            historial_mensajes = list(
                reversed(historial_mensajes)
            )

            historial = []

            for chat in historial_mensajes:

                historial.append({
                    "rol": chat.rol,
                    "mensaje": chat.mensaje
                })

            try:

                respuesta = chat_bot(
                    mensaje,
                    historial=historial,
                    contexto=contexto
                )

            except Exception as e:

                print(
                    f"[ERROR CHATBOT IA] {e}"
                )

                respuesta = (
                    "Lo siento, ocurrió un problema al "
                    "procesar tu mensaje. "
                    "Por favor, inténtalo nuevamente."
                )

            ChatMensaje.objects.create(
                usuario=request.user,
                rol="ia",
                mensaje=respuesta
            )

    mensajes = (
        ChatMensaje.objects
        .filter(
            usuario=request.user
        )
        .order_by("fecha")
    )

    if es_embed:

        return render(
            request,
            "pqrs/chatbot.html",
            {
                "mensajes": mensajes,
                "es_embed": True,
                "no_autenticado": False,
            }
        )

    return render(
        request,
        "pqrs/chatbot_completo.html",
        {
            "mensajes": mensajes,
            "es_embed": False,
            "no_autenticado": False,
        }
    )


# ========================================================
# GENERAR REPORTE PDF (VERSIÓN SIMPLIFICADA Y ESTABLE)
# ============================================================

def generar_reporte_pdf(request, pqrs_id=None):
    """Genera un reporte PDF de PQRS con logo, KPIs, gráficos y tabla."""

    # ========================================================
    # VALIDACIONES
    # ========================================================

    if not request.user.is_authenticated:
        return redirect('usuarios:login')

    perfil = request.user.perfil

    if perfil.rol != 'empresa':
        messages.warning(request, 'Solo las empresas pueden generar reportes')
        return redirect('core:inicio')

    if not perfil.empresa:
        messages.error(request, 'Tu usuario no tiene una empresa asociada.')
        return redirect('core:inicio')

    empresa = perfil.empresa

    # ========================================================
    # CONSULTA DE PQRS
    # ========================================================

    if pqrs_id:
        pqrs_list = Pqrs.objects.filter(id=pqrs_id, id_empresa=empresa)
    else:
        pqrs_list = Pqrs.objects.filter(id_empresa=empresa).order_by('-fecha_creacion')

    if not pqrs_list.exists():
        messages.warning(request, 'No hay PQRS para generar el reporte.')
        return redirect('pqrs:dashboard')

    pqrs_list = list(pqrs_list)

    fecha_generacion = timezone.localtime(timezone.now())

    # ========================================================
    # ESTADÍSTICAS
    # ========================================================

    total = len(pqrs_list)
    pendientes = sum(1 for p in pqrs_list if p.estado == 'Pendiente')
    en_proceso = sum(1 for p in pqrs_list if p.estado == 'En Proceso')
    resueltas = sum(1 for p in pqrs_list if p.estado == 'Resuelta')

    tasa_resolucion = round((resueltas / total) * 100) if total > 0 else 0

    peticiones = sum(1 for p in pqrs_list if (p.tipo_detectado or '').lower() == 'peticion')
    sugerencias = sum(1 for p in pqrs_list if (p.tipo_detectado or '').lower() == 'sugerencia')
    reclamos = sum(1 for p in pqrs_list if (p.tipo_detectado or '').lower() == 'reclamo')
    otros = total - (peticiones + sugerencias + reclamos)

    print(f"[PDF] Generando reporte: {total} PQRS")

    # ========================================================
    # COLORES
    # ========================================================

    AZUL = HexColor("#1E3A8A")
    AZUL_MEDIO = HexColor("#2563EB")
    AZUL_CLARO = HexColor("#EFF6FF")
    GRIS_OSCURO = HexColor("#334155")
    GRIS = HexColor("#64748B")
    GRIS_CLARO = HexColor("#F1F5F9")
    GRIS_LINEA = HexColor("#CBD5E1")
    VERDE = HexColor("#059669")
    VERDE_CLARO = HexColor("#ECFDF5")
    AMARILLO = HexColor("#D97706")
    AMARILLO_CLARO = HexColor("#FFFBEB")
    ROJO = HexColor("#DC2626")
    ROJO_CLARO = HexColor("#FEF2F2")

    # ========================================================
    # LOGO (LOCAL - media/)
    # ========================================================

    def obtener_logo():
        """Intenta cargar el logo desde la carpeta media local."""
        if not perfil.logo:
            return None
        try:
            ruta_logo = perfil.logo.path
            if os.path.exists(ruta_logo):
                print(f"[PDF] Logo encontrado: {ruta_logo}")
                return ImageReader(ruta_logo)
            else:
                print(f"[PDF] Logo NO existe en: {ruta_logo}")
        except Exception as e:
            print(f"[PDF] Error cargando logo: {e}")
        return None

    logo = obtener_logo()

    # ========================================================
    # UTILIDADES
    # ========================================================

    def texto_recortado(texto, max_width, fuente="Helvetica", tamaño=8):
        texto = str(texto or '')
        if stringWidth(texto, fuente, tamaño) <= max_width:
            return texto
        while len(texto) > 3 and stringWidth(texto + "...", fuente, tamaño) > max_width:
            texto = texto[:-1]
        return texto + "..."

    # ========================================================
    # BUFFER Y CANVAS
    # ========================================================

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # ========================================================
    # ENCABEZADO
    # ========================================================

    def dibujar_encabezado():
        p.setFillColor(AZUL)
        p.roundRect(15 * mm, height - 43 * mm, width - 30 * mm, 28 * mm, 4 * mm, fill=1, stroke=0)

        if logo:
            try:
                p.drawImage(
                    logo,
                    20 * mm,
                    height - 39 * mm,
                    width=20 * mm,
                    height=20 * mm,
                    preserveAspectRatio=True,
                    anchor='c',
                    mask='auto'
                )
                print("[PDF] Logo dibujado correctamente")
            except Exception as e:
                print(f"[PDF] Error dibujando logo: {e}")

        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 17)
        p.drawString(45 * mm, height - 27 * mm, "REPORTE DE PQRS")

        p.setFont("Helvetica", 9)
        p.drawString(45 * mm, height - 33 * mm, "Gestion y seguimiento de solicitudes")

        p.setFillColor(GRIS_OSCURO)
        p.setFont("Helvetica-Bold", 9)
        p.drawString(20 * mm, height - 51 * mm, empresa.nombre_empresa)

        p.setFont("Helvetica", 8)
        p.drawString(20 * mm, height - 56 * mm, f"NIT: {empresa.nit}")
        p.drawString(20 * mm, height - 61 * mm, f"Telefono: {empresa.telefono or 'No registrado'}")
        p.drawString(20 * mm, height - 66 * mm, "Generado: " + fecha_generacion.strftime('%d/%m/%Y %H:%M'))

        fechas = [item.fecha_creacion for item in pqrs_list if item.fecha_creacion]
        if fechas:
            periodo = f"{min(fechas).strftime('%d/%m/%Y')} - {max(fechas).strftime('%d/%m/%Y')}"
        else:
            periodo = "Sin fecha"

        p.setFont("Helvetica-Bold", 8)
        p.drawRightString(width - 20 * mm, height - 51 * mm, "PERIODO")
        p.setFont("Helvetica", 8)
        p.drawRightString(width - 20 * mm, height - 56 * mm, periodo)

    # ========================================================
    # PIE
    # ========================================================

    def dibujar_pie(numero_pagina):
        p.setStrokeColor(GRIS_LINEA)
        p.line(20 * mm, 17 * mm, width - 20 * mm, 17 * mm)
        p.setFillColor(GRIS)
        p.setFont("Helvetica", 7)
        p.drawString(20 * mm, 11 * mm, "PQRS Inteligente - Proyecto SENA Cucuta 2026")
        p.drawRightString(width - 20 * mm, 11 * mm, f"Pagina {numero_pagina}")

    # ========================================================
    # KPIs
    # ========================================================

    def dibujar_kpis(y):
        valores = [
            ("TOTAL PQRS", total, AZUL, AZUL_CLARO),
            ("PENDIENTES", pendientes, AMARILLO, AMARILLO_CLARO),
            ("EN PROCESO", en_proceso, AZUL_MEDIO, AZUL_CLARO),
            ("RESUELTAS", resueltas, VERDE, VERDE_CLARO),
            ("RESOLUCION", f"{tasa_resolucion}%",
             ROJO if tasa_resolucion < 50 else VERDE,
             ROJO_CLARO if tasa_resolucion < 50 else VERDE_CLARO),
        ]

        margen = 20 * mm
        espacio = 3 * mm
        ancho = ((width - 2 * margen) - 4 * espacio) / 5
        alto = 24 * mm
        x = margen

        for titulo, valor, color, fondo in valores:
            p.setFillColor(fondo)
            p.roundRect(x, y - alto, ancho, alto, 3 * mm, fill=1, stroke=0)

            p.setFillColor(color)
            p.setFont("Helvetica-Bold", 7)
            p.drawString(x + 4 * mm, y - 7 * mm, titulo)

            p.setFont("Helvetica-Bold", 18)
            p.drawString(x + 4 * mm, y - 18 * mm, str(valor))

            x += ancho + espacio

        return y - alto - 8 * mm

    # ========================================================
    # DESGLOSE
    # ========================================================

    def dibujar_desglose(y):
        alto = 35 * mm

        # Panel izquierdo
        p.setFillColor(colors.white)
        p.setStrokeColor(GRIS_LINEA)
        p.roundRect(20 * mm, y - alto, 80 * mm, alto, 3 * mm, fill=1, stroke=1)

        p.setFillColor(GRIS_OSCURO)
        p.setFont("Helvetica-Bold", 9)
        p.drawString(25 * mm, y - 7 * mm, "PQRS POR TIPO")

        tipos = [
            ("Peticiones", peticiones, AZUL_MEDIO),
            ("Sugerencias", sugerencias, VERDE),
            ("Reclamos", reclamos, ROJO),
        ]
        if otros > 0:
            tipos.append(("Otros", otros, GRIS))

        yy = y - 14 * mm
        for nombre, cantidad, color in tipos:
            p.setFillColor(color)
            p.circle(27 * mm, yy + 1 * mm, 1.5 * mm, fill=1, stroke=0)

            p.setFillColor(GRIS_OSCURO)
            p.setFont("Helvetica", 8)
            p.drawString(32 * mm, yy, nombre)

            p.setFont("Helvetica-Bold", 8)
            p.drawRightString(94 * mm, yy, str(cantidad))
            yy -= 6 * mm

        # Panel derecho
        x_estado = 105 * mm
        ancho_estado = width - x_estado - 20 * mm

        p.setFillColor(colors.white)
        p.setStrokeColor(GRIS_LINEA)
        p.roundRect(x_estado, y - alto, ancho_estado, alto, 3 * mm, fill=1, stroke=1)

        p.setFillColor(GRIS_OSCURO)
        p.setFont("Helvetica-Bold", 9)
        p.drawString(x_estado + 5 * mm, y - 7 * mm, "ESTADO DE LAS SOLICITUDES")

        estados = [
            ("Pendientes", pendientes, AMARILLO, total),
            ("En proceso", en_proceso, AZUL_MEDIO, total),
            ("Resueltas", resueltas, VERDE, total),
        ]

        yy = y - 15 * mm
        for nombre, cantidad, color, total_estado in estados:
            p.setFillColor(GRIS_CLARO)
            p.roundRect(x_estado + 5 * mm, yy - 1.5 * mm, ancho_estado - 10 * mm, 3 * mm, 1.5 * mm, fill=1, stroke=0)

            porcentaje_estado = cantidad / total_estado if total_estado else 0

            p.setFillColor(color)
            p.roundRect(x_estado + 5 * mm, yy - 1.5 * mm,
                        (ancho_estado - 10 * mm) * porcentaje_estado, 3 * mm, 1.5 * mm, fill=1, stroke=0)

            p.setFillColor(GRIS_OSCURO)
            p.setFont("Helvetica", 7)
            p.drawString(x_estado + 5 * mm, yy + 4 * mm, nombre)

            p.setFont("Helvetica-Bold", 7)
            p.drawRightString(width - 25 * mm, yy + 4 * mm,
                              f"{cantidad} ({round(porcentaje_estado * 100)}%)")
            yy -= 8 * mm

        return y - alto - 8 * mm

    # ========================================================
    # HALLAZGOS
    # ========================================================

    def dibujar_hallazgos(y):
        hallazgos = []

        if total:
            porcentaje_pendientes = round(pendientes / total * 100)
            if porcentaje_pendientes >= 70:
                hallazgos.append(f"El {porcentaje_pendientes}% de las PQRS se encuentran pendientes.")
            elif pendientes > 0:
                hallazgos.append(f"Actualmente hay {pendientes} PQRS pendientes de atencion.")

        if reclamos > 0:
            hallazgos.append(f"Se registraron {reclamos} reclamo{'s' if reclamos != 1 else ''}, los cuales requieren especial seguimiento.")

        if resueltas > 0:
            hallazgos.append(f"Se han resuelto {resueltas} PQRS, con una tasa de resolucion del {tasa_resolucion}%.")

        if not hallazgos:
            hallazgos.append("No se encontraron datos suficientes para generar hallazgos.")

        hallazgos = hallazgos[:3]

        alto = 10 * mm + len(hallazgos) * 5 * mm

        p.setFillColor(HexColor("#F8FAFC"))
        p.roundRect(20 * mm, y - alto, width - 40 * mm, alto, 3 * mm, fill=1, stroke=0)

        p.setFillColor(AZUL)
        p.setFont("Helvetica-Bold", 9)
        p.drawString(25 * mm, y - 7 * mm, "HALLAZGOS")

        yy = y - 13 * mm
        p.setFont("Helvetica", 7.5)

        for hallazgo in hallazgos:
            p.setFillColor(AZUL_MEDIO)
            p.circle(27 * mm, yy + 1 * mm, 1 * mm, fill=1, stroke=0)
            p.setFillColor(GRIS_OSCURO)
            p.drawString(32 * mm, yy, hallazgo[:105])
            yy -= 5 * mm

        return y - alto - 8 * mm

    # ========================================================
    # ENCABEZADO TABLA
    # ========================================================

    def dibujar_tabla_encabezado(y):
        altura = 9 * mm

        p.setFillColor(GRIS_CLARO)
        p.roundRect(20 * mm, y - altura, width - 40 * mm, altura, 2 * mm, fill=1, stroke=0)

        p.setFillColor(GRIS_OSCURO)
        p.setFont("Helvetica-Bold", 7)
        p.drawString(23 * mm, y - 6 * mm, "RADICADO")
        p.drawString(53 * mm, y - 6 * mm, "ASUNTO")
        p.drawString(112 * mm, y - 6 * mm, "TIPO")
        p.drawString(142 * mm, y - 6 * mm, "ESTADO")
        p.drawString(175 * mm, y - 6 * mm, "FECHA")

        return y - altura - 2 * mm

    # ========================================================
    # RENDERIZADO - PRIMERA PÁGINA
    # ========================================================

    numero_pagina = 1

    dibujar_encabezado()
    dibujar_pie(numero_pagina)

    y = height - 73 * mm
    y = dibujar_kpis(y)
    y = dibujar_desglose(y)
    y = dibujar_hallazgos(y)
    y -= 2 * mm
    y = dibujar_tabla_encabezado(y)

    p.setFont("Helvetica", 7)

    # ========================================================
    # FILAS DE LA TABLA
    # ========================================================

    for item in pqrs_list:
        altura_fila = 9 * mm

        if y < 27 * mm:
            # Nueva página
            p.showPage()
            numero_pagina += 1
            dibujar_encabezado()
            dibujar_pie(numero_pagina)
            y = height - 73 * mm
            y = dibujar_tabla_encabezado(y)
            p.setFont("Helvetica", 7)

        tipo = (item.tipo_detectado or '').lower()

        if tipo == 'reclamo':
            p.setFillColor(HexColor("#FFF7F7"))
            p.rect(20 * mm, y - 7 * mm, width - 40 * mm, 8 * mm, fill=1, stroke=0)

        p.setFillColor(GRIS_OSCURO)
        p.setFont("Helvetica-Bold", 6.5)
        p.drawString(23 * mm, y - 4 * mm,
                     texto_recortado(item.codigo_radicado, 27 * mm, "Helvetica-Bold", 6.5))

        p.setFont("Helvetica", 7)
        p.drawString(53 * mm, y - 4 * mm,
                     texto_recortado(item.asunto, 55 * mm, "Helvetica", 7))

        p.drawString(112 * mm, y - 4 * mm,
                     texto_recortado(item.tipo_detectado or 'N/A', 27 * mm, "Helvetica", 7))

        estado = item.estado or ''
        if estado == 'Resuelta':
            color_estado = VERDE
        elif estado == 'En Proceso':
            color_estado = AZUL_MEDIO
        else:
            color_estado = AMARILLO

        p.setFillColor(color_estado)
        p.roundRect(142 * mm, y - 6 * mm, 27 * mm, 5 * mm, 2 * mm, fill=1, stroke=0)

        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 6.5)
        p.drawCentredString(155.5 * mm, y - 4.3 * mm,
                            texto_recortado(estado, 24 * mm, "Helvetica-Bold", 6.5))

        p.setFillColor(GRIS_OSCURO)
        p.setFont("Helvetica", 7)
        p.drawString(175 * mm, y - 4 * mm, item.fecha_creacion.strftime('%d/%m/%Y'))

        p.setStrokeColor(HexColor("#E2E8F0"))
        p.line(20 * mm, y - 8 * mm, width - 20 * mm, y - 8 * mm)

        y -= altura_fila

    # ========================================================
    # FINALIZAR PDF
    # ========================================================

    print(f"[PDF] Guardando PDF con {numero_pagina} página(s)...")
    p.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    print(f"[PDF] PDF generado: {len(pdf_bytes)} bytes")

    response = HttpResponse(pdf_bytes, content_type='application/pdf')

    if pqrs_id:
        response['Content-Disposition'] = f'attachment; filename="reporte_pqrs_{pqrs_id}.pdf"'
    else:
        response['Content-Disposition'] = (
            'attachment; '
            f'filename="reporte_todas_pqrs_{fecha_generacion.strftime("%Y%m%d")}.pdf"'
        )

    return response