from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('ayuda/', views.ayuda, name='ayuda'),
    path('funciones/', views.funciones, name='funciones'),
    path('respaldar-bd/', views.respaldar_bd, name='respaldar_bd'),
    path('restaurar-bd/', views.restaurar_bd, name='restaurar_bd'),
]