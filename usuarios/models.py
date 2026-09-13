from django.db import models
from django.contrib.auth.models import User
from empresas.models import Empresa
from core.validators import validate_file_extension

class PerfilUsuario(models.Model):
    ROLES = (
        ('empresa', 'Administrador de Empresa'),
        ('cliente', 'Cliente'),
    )
    nombres = models.CharField(max_length=50, blank=True, null=True)
    apellidos = models.CharField(max_length=50, blank=True, null=True)
    TIPO_DOCUMENTO_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('TI', 'Tarjeta de Identidad'),
        ('CE', 'Cédula de Extranjería'),
        ('NIT', 'NIT'),
        ('PAS', 'Pasaporte'),
    ]
    tipo_documento = models.CharField(
        max_length=10,
        choices=TIPO_DOCUMENTO_CHOICES,
        default='CC',
        verbose_name="Tipo de documento"
    )
    numero_documento = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Número de documento"
    )
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Empresa (solo para roles empresa)")
    telefono = models.CharField(max_length=15, blank=True, null=True)
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')
    foto = models.ImageField(upload_to='fotos_perfil/', blank=True, null=True, verbose_name="Foto de perfil", validators=[validate_file_extension])
    logo = models.ImageField(upload_to='logos_empresa/', blank=True, null=True, verbose_name="Logo de la empresa", validators=[validate_file_extension])

    def __str__(self):
        return f"{self.usuario.username} - {self.get_rol_display()}"