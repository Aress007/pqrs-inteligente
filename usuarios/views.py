from django.conf import settings
import time
import hashlib
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.http import HttpResponse
from empresas.models import Empresa, Plan
from .models import PerfilUsuario
from .forms import (
    RegistroUnificadoForm,
    EditarPerfilForm,
    EditarTelefonoForm,
    CambiarPasswordForm,
)


# ===== LOGIN =====

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


# ===== LOGOUT =====

@require_http_methods(["POST"])
@ensure_csrf_cookie
@never_cache
def logout_view(request):
    logout(request)
    messages.info(request, "Sesión cerrada correctamente")
    response = redirect("core:inicio")
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


# ===== REGISTRO UNIFICADO =====

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
                    usuario=user, empresa=empresa, telefono=telefono, rol="empresa"
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
                    usuario=user, telefono=telefono, rol="cliente", empresa=None
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

# ===== EDITAR PERFIL =====

@login_required
def editar_perfil(request):
    perfil = request.user.perfil
    if request.method == "POST":
        user_form = EditarPerfilForm(request.POST, instance=request.user)
        telefono_form = EditarTelefonoForm(request.POST)
        if user_form.is_valid() and telefono_form.is_valid():
            user_form.save()
            perfil.telefono = telefono_form.cleaned_data["telefono"]
            perfil.save()
            messages.success(request, "Tu perfil ha sido actualizado correctamente.")
            if perfil.rol == "empresa":
                return redirect("pqrs:dashboard")
            else:
                return redirect("pqrs:mis_solicitudes")
        else:
            messages.error(request, "Por favor corrige los errores.")
    else:
        user_form = EditarPerfilForm(instance=request.user)
        telefono_form = EditarTelefonoForm(initial={"telefono": perfil.telefono})

    return render(
        request,
        "usuarios/editar_perfil.html",
        {
            "user_form": user_form,
            "telefono_form": telefono_form,
        },
    )


# ===== CAMBIAR CONTRASEÑA =====

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


# ===== PAGO CON EPAYCO (WEB CHECKOUT - MODO SANDBOX) =====

def iniciar_pago_epayco(request, plan_id):
    """Inicia el pago con ePayco usando Web Checkout"""
    plan = get_object_or_404(Plan, id=plan_id)

    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para pagar")
        return redirect('usuarios:login')
    try:
        perfil = request.user.perfil
        if perfil.rol != 'empresa' or not perfil.empresa:
            messages.error(request, "No tienes una empresa asociada")
            return redirect('core:inicio')
        empresa = perfil.empresa
    except:
        messages.error(request, "Perfil de usuario no válido")
        return redirect('core:inicio')

    referencia = f"plan_{plan.id}_{empresa.id}_{int(time.time())}"
    empresa.ref_payco = referencia
    empresa.save()

    url_response = request.build_absolute_uri('/pago/exitoso/')
    url_confirmation = request.build_absolute_uri('/pago/confirmacion/')

    context = {
        'plan': plan,
        'public_key': settings.EPAYCO_PUBLIC_KEY,
        'reference': referencia,
        'email': request.user.email,
        'url_response': url_response,
        'url_confirmation': url_confirmation,
    }

    return render(request, 'usuarios/checkout_epayco.html', context)


# ===== VISTA DE RESPUESTA (REDIRECCIÓN POST-PAGO) =====

@never_cache
def pago_exitoso(request):
    """Redirección después de pagar (recibe parámetros GET de ePayco)"""
    resultado = request.GET.get('x_resultado', '')
    ref_payco = request.GET.get('x_ref_payco', '')
    mensaje = request.GET.get('x_mensaje', '')
    cod_transaccion = request.GET.get('x_cod_transaccion', '')

    context = {
        'resultado': resultado,
        'ref_payco': ref_payco,
        'mensaje': mensaje,
        'cod_transaccion': cod_transaccion,
    }

    if resultado == 'Aceptado':
        # Buscar la empresa por la referencia (ref_payco)
        try:
            empresa = Empresa.objects.get(ref_payco=ref_payco)
            messages.success(request, "¡Pago exitoso! Tu plan ha sido activado.")
            return redirect('pqrs:dashboard')
        except Empresa.DoesNotExist:
            messages.warning(request, "No se encontró la empresa asociada al pago, pero el pago fue aceptado. Contacta a soporte.")
            return redirect('core:inicio')
    else:
        messages.error(request, f"El pago no fue aceptado: {mensaje}")
        return render(request, 'usuarios/pago_resultado.html', context)


# ===== WEBHOOK DE CONFIRMACIÓN (NOTIFICACIÓN DE EPAYCO) =====

@csrf_exempt
def confirmacion_pago_epayco(request):
    """Webhook que ePayco llama para confirmar el pago (POST)"""
    if request.method != 'POST':
        return HttpResponse("Método no permitido", status=405)

    data = request.POST.dict()
    print(f"[EPAyCO WEBHOOK] Datos recibidos: {data}")
    p_cust_id_cliente = getattr(settings, 'EPAYCO_P_CUST_ID_CLIENTE', '')
    x_ref_payco = data.get('x_ref_payco', '')
    x_transaction_id = data.get('x_transaction_id', '')
    x_amount = data.get('x_amount', '')
    x_currency_code = data.get('x_currency_code', '')
    x_test_request = data.get('x_test_request', '')
    x_signature = data.get('x_signature', '')

    if not p_cust_id_cliente or not x_signature:
        return HttpResponse("Faltan datos para validar firma", status=400)

    # Construir cadena para firma
    cadena = f"{p_cust_id_cliente}^{x_ref_payco}^{x_transaction_id}^{x_amount}^{x_currency_code}^{x_test_request}"
    firma_calculada = hashlib.sha256(cadena.encode('utf-8')).hexdigest()

    if firma_calculada != x_signature:
        print(f"[ERROR] Firma inválida. Esperada: {firma_calculada}, Recibida: {x_signature}")
        return HttpResponse("Firma inválida", status=400)

    # 2. Procesar el pago si es exitoso
    x_resultado = data.get('x_resultado', '')
    if x_resultado == 'Aceptado':
        try:
            empresa = Empresa.objects.get(ref_payco=x_ref_payco)

            try:
                partes = x_ref_payco.split('_')
                if len(partes) >= 3:
                    plan_id = int(partes[1])
                    plan = Plan.objects.get(id=plan_id)
                    empresa.id_plan = plan
                else:
                    pass
            except:
           
                pass

            # Actualizar fechas de suscripción (ejemplo: 30 días desde ahora)
            ahora = timezone.now()
            empresa.fecha_inicio_suscripcion = ahora
            empresa.fecha_fin_suscripcion = ahora + timedelta(days=30)
            empresa.pago_activo = True
            empresa.ref_payco = x_ref_payco  
            empresa.save()

            print(f"[EPAyCO] Pago exitoso para empresa {empresa.id} - Plan actualizado")
            return HttpResponse("OK", status=200)

        except Empresa.DoesNotExist:
            print(f"[ERROR] Empresa no encontrada para ref_payco: {x_ref_payco}")
            return HttpResponse("Empresa no encontrada", status=404)
    else:
        print(f"[EPAyCO] Pago rechazado: {x_resultado}")
        return HttpResponse("Pago rechazado", status=200)  

    return HttpResponse("Error procesando webhook", status=400)