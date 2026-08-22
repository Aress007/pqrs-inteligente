from django.urls import path
from . import views

app_name = "pqrs"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("crear/", views.crear_pqrs, name="crear"),
    path("mis-solicitudes/", views.mis_solicitudes, name="mis_solicitudes"),
    path("descargar/<int:pqrs_id>/", views.descargar_archivo, name="descargar_archivo"),
    path("<int:pqrs_id>/", views.detalle_pqrs, name="detalle"),
    path("respuesta/editar/<int:respuesta_id>/", views.editar_respuesta, name="editar_respuesta",),
    path("respuesta/eliminar/<int:respuesta_id>/", views.eliminar_respuesta, name="eliminar_respuesta",),
    path('chatbot/', views.chatbot_view, name='chatbot'),
]