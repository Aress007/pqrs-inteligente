from django.db import models
from django.contrib.auth.models import User
from empresas.models import Empresa

class Pqrs(models.Model):
    ESTADOS_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('En Proceso', 'En Proceso'),
        ('Resuelta', 'Resuelta'),
    ]

    codigo_radicado = models.CharField(max_length=50, unique=True, verbose_name="Código de Radicado")
    asunto = models.CharField(max_length=200, verbose_name="Asunto")
    descripcion = models.TextField(verbose_name="Descripción de la Solicitud")
    tipo_detectado = models.CharField(max_length=50, verbose_name="Tipo Detectado por IA")
    estado = models.CharField(max_length=30, choices=ESTADOS_CHOICES, default='Pendiente', verbose_name="Estado Actual")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Radicación")
    archivo = models.FileField(upload_to='pqrs_adjuntos/', blank=True, null=True, verbose_name="Archivo adjunto")
    
    id_usuario_creador = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario que Crea")
    id_empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa Destino")

    def __str__(self):
        return f"{self.codigo_radicado} - {self.asunto}"

class RespuestaPqrs(models.Model):
    id_pqrs = models.ForeignKey(Pqrs, on_delete=models.CASCADE, related_name="respuestas", verbose_name="PQRS Asociado")
    id_usuario_responde = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario que Responde")
    texto_respuesta = models.TextField(verbose_name="Contenido de la Respuesta")
    fecha_respuesta = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Respuesta")

    def __str__(self):
        return f"Respuesta a {self.id_pqrs.codigo_radicado}"