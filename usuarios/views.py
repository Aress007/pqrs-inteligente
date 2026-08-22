from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.utils.html import strip_tags
from django.conf import settings
from django.http import HttpResponse
import os
import time
from empresas.models import Empresa, Plan
from .models import PerfilUsuario
from .forms import (RegistroUnificadoForm, EditarPerfilForm, CambiarPasswordForm,)


# ============================================================
# FUNCIÓN AUXILIAR PARA ELIMINAR ARCHIVOS
# ============================================================
def eliminar_archivo_si_existe(ruta):
    """Elimina un archivo físico si existe."""
    if ruta and os.path.isfile(ruta):
        os.remove(ruta)
        return True
    return False

# ============================================================
# LOGIN
# ============================================================
@never_cache
def login_view(request):
    if request.user.is_authenticated:
        try:
            perfil = request.user.perfil
            if perfil.rol == "empresa":
                return redirect("pqrs:dashboard")
            else:
                return redirect("pqrs:mis_solicitudes")
        except:
            return redirect("core:inicio")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            try:
                perfil = user.perfil
            except:
                PerfilUsuario.objects.create(usuario=user, rol="cliente", empresa=None)
                messages.info(request, "Perfil creado automáticamente")
            messages.success(request, f"Bienvenido {user.username}")
            try:
                perfil = user.perfil
                if perfil.rol == "empresa":
                    return redirect("pqrs:dashboard")
                else:
                    return redirect("pqrs:mis_solicitudes")
            except:
                return redirect("core:inicio")
        else:
            messages.error(request, "Credenciales incorrectas")
    return render(request, "usuarios/login.html")

# ============================================================
# LOGOUT
# ============================================================
@require_http_methods(["POST"])
@ensure_csrf_cookie
@never_cache
def logout_view(request):
    try:
        from pqrs.models import ChatMensaje
        ChatMensaje.objects.filter(usuario=request.user).delete()
    except:
        pass 
    
    logout(request)
    messages.info(request, "Sesión cerrada correctamente")
    response = redirect("core:inicio")
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response

# ============================================================
# REGISTRO UNIFICADO
# ============================================================
def registro_unificado(request):
    if request.method == "POST":
        form = RegistroUnificadoForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            telefono = form.cleaned_data["telefono"]
            es_empresa = form.cleaned_data["es_empresa"]

            user = User.objects.create_user(
                username=username, email=email, password=password
            )

            if es_empresa:
                plan = form.cleaned_data["plan"]
                if not plan:
                    messages.error(request, "Debe seleccionar un plan")
                    return render(
                        request, "usuarios/registro_unificado.html", {"form": form}
                    )
                empresa = Empresa.objects.create(
                    nombre_empresa=form.cleaned_data["nombre_empresa"],
                    nit=form.cleaned_data["nit"],
                    telefono=telefono,
                    direccion=form.cleaned_data["direccion"],
                    id_plan=plan,
                )
                PerfilUsuario.objects.create(
                    usuario=user,
                    empresa=empresa,
                    telefono=telefono,
                    rol="empresa",
                )
                messages.success(request, "Empresa registrada exitosamente")
                user_auth = authenticate(request, username=username, password=password)
                if user_auth:
                    login(request, user_auth)
                    if plan.precio > 0:
                        request.session["empresa_id"] = empresa.id
                        return redirect("usuarios:iniciar_pago_epayco", plan_id=plan.id)
                    else:
                        return redirect("pqrs:dashboard")
                else:
                    messages.warning(request, "Cuenta creada, inicia sesión manualmente")
                    return redirect("usuarios:login")
            else:
                PerfilUsuario.objects.create(
                    usuario=user,
                    telefono=telefono,
                    rol="cliente",
                    empresa=None,
                )
                messages.success(request, "Cliente registrado exitosamente")
                user_auth = authenticate(request, username=username, password=password)
                if user_auth:
                    login(request, user_auth)
                    return redirect("pqrs:mis_solicitudes")
                else:
                    messages.warning(
                        request, "Cuenta creada, inicia sesión manualmente"
                    )
                    return redirect("usuarios:login")
        else:
            messages.error(request, "Corrige los errores del formulario")
    else:
        form = RegistroUnificadoForm()

    planes = Plan.objects.all()
    return render(
        request, "usuarios/registro_unificado.html", {"form": form, "planes": planes}
    )

# ============================================================
# VISTA DE PAGO SIMULADO
# ============================================================
@never_cache
def pago_simulado(request):
    return render(request, "usuarios/pago_simulado.html")

# ============================================================
# EDITAR PERFIL
# ============================================================
@login_required
def editar_perfil(request):
    perfil = request.user.perfil

    if request.method == "POST":

        # ============================================================
        # ELIMINAR FOTO DE PERFIL
        # ============================================================
        if request.POST.get("eliminar_foto") == "on":
            if perfil.foto:
                try:
                    eliminar_archivo_si_existe(perfil.foto.path)
                except Exception:
                    pass
                
                perfil.foto = None
                perfil.save(update_fields=["foto"])

                messages.success(
                    request,
                    "Foto de perfil eliminada correctamente."
                )
                return redirect("usuarios:editar_perfil")

        # ============================================================
        # ELIMINAR LOGO DE EMPRESA
        # ============================================================
        if request.POST.get("eliminar_logo") == "on":
            if perfil.logo:
                try:
                    eliminar_archivo_si_existe(perfil.logo.path)
                except Exception:
                    pass

                perfil.logo = None
                perfil.save(update_fields=["logo"])

                messages.success(
                    request,
                    "Logo de la empresa eliminado correctamente."
                )
                return redirect("usuarios:editar_perfil")

        # ============================================================
        # GUARDAR CAMBIOS DEL PERFIL
        # ============================================================
        form = EditarPerfilForm(
            request.POST,
            request.FILES,
            instance=request.user
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Tu perfil ha sido actualizado correctamente."
            )

            if perfil.rol == "empresa":
                return redirect("pqrs:dashboard")
            else:
                return redirect("pqrs:mis_solicitudes")

        else:
            print("ERRORES DEL FORMULARIO:", form.errors)
            messages.error(
                request,
                "Por favor corrige los errores."
            )

    else:
        form = EditarPerfilForm(instance=request.user)

    return render(
        request,
        "usuarios/editar_perfil.html",
        {
            "user_form": form,
        },
    )

# ============================================================
# CAMBIAR CONTRASEÑA
# ============================================================
@login_required
def cambiar_password(request):
    perfil = request.user.perfil
    if request.method == "POST":
        form = CambiarPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Tu contraseña ha sido cambiada exitosamente.")
            if perfil.rol == "empresa":
                return redirect("pqrs:dashboard")
            else:
                return redirect("pqrs:mis_solicitudes")
        else:
            messages.error(request, "Por favor corrige los errores.")
    else:
        form = CambiarPasswordForm(request.user)
    return render(request, "usuarios/cambiar_password.html", {"form": form})

# ============================================================
# PAGO CON EPAYCO (Web Checkout)
# ============================================================
def iniciar_pago_epayco(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para pagar")
        return redirect('usuarios:login')

    context = {
        'plan': plan,
        'public_key': settings.EPAYCO_PUBLIC_KEY,
        'reference': f"plan_{plan.id}_{request.user.id}_{int(time.time())}",
        'email': request.user.email,
        'url_response': request.build_absolute_uri('/pago/exitoso/'),
        'url_confirmation': request.build_absolute_uri('/pago/confirmacion/'),
    }
    return render(request, 'usuarios/checkout_epayco.html', context)

@csrf_exempt
def confirmacion_pago_epayco(request):
    if request.method == 'POST':
        data = request.POST.dict()
        print(f"[EPAyCO WEBHOOK] Datos recibidos: {data}")
        return HttpResponse("OK")
    return HttpResponse("Método no permitido", status=405)

# ============================================================
# RECUPERACIÓN DE CONTRASEÑA (con correo real)
# ============================================================
def recuperar_contraseña(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "El correo ingresado no está registrado.")
            return render(request, 'usuarios/recuperar_contraseña.html')
        
        signer = TimestampSigner()
        token = signer.sign(str(user.pk))
        reset_url = request.build_absolute_uri(reverse('usuarios:cambiar_con_token', args=[token]))
        
        html_message = render_to_string('usuarios/msg_correo.html', {
            'username': user.username,
            'reset_url': reset_url,
            'site_name': 'PQRS Inteligente',
        })
        subject = "Recuperación de contraseña - PQRS Inteligente"
        text_message = strip_tags(html_message)
        
        try:
            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            email_msg.encoding = 'utf-8'
            email_msg.send()
            messages.success(request, "Se ha enviado un enlace de recuperación a tu correo.")
            return redirect('usuarios:login')
        except Exception as e:
            messages.error(request, f"Error al enviar el correo: {str(e)}")
            return render(request, 'usuarios/recuperar_contraseña.html')
    
    return render(request, 'usuarios/recuperar_contraseña.html')

def cambiar_con_token(request, token):
    signer = TimestampSigner()
    try:
        user_id = signer.unsign(token, max_age=3600)
        usuario = get_object_or_404(User, pk=user_id)
    except (BadSignature, SignatureExpired):
        messages.error(request, "El enlace de recuperación es inválido o ha expirado.")
        return redirect('usuarios:recuperar_contraseña')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, 'usuarios/cambiar_con_token.html')
        usuario.password = make_password(new_password)
        usuario.save()
        messages.success(request, "Contraseña cambiada correctamente. Inicia sesión.")
        return redirect('usuarios:login')
    
    return render(request, 'usuarios/cambiar_con_token.html')