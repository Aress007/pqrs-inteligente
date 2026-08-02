from django.db import models
from django.contrib.auth.models import User
from empresas.models import Empresa

class PerfilUsuario(models.Model):
    ROLES = (
        ('empresa', 'Administrador de Empresa'),
        ('cliente', 'Cliente'),
    )
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Empresa (solo para roles empresa)")
    telefono = models.CharField(max_length=15, blank=True, null=True)
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')

    def __str__(self):
        return f"{self.usuario.username} - {self.get_rol_display()}"