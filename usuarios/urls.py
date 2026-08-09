from django.urls import path
from . import views

app_name = "usuarios"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("registro/", views.registro_unificado, name="registro_unificado"),
    path("pagar-epayco/<int:plan_id>/", views.iniciar_pago_epayco, name="iniciar_pago_epayco"),
    path("pago/exitoso/", views.pago_exitoso, name="pago_exitoso"),
    path("pago/confirmacion/", views.confirmacion_pago_epayco, name="pago_confirmacion"),
    path("editar-perfil/", views.editar_perfil, name="editar_perfil"),
    path("cambiar-password/", views.cambiar_password, name="cambiar_password"),
    path('recuperar-contrasena/', views.recuperar_contraseña, name='recuperar_contraseña'),
    path('cambiar-contrasena/<str:token>/', views.cambiar_con_token, name='cambiar_con_token'),
]