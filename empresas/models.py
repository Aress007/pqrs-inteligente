from django.db import models

class Plan(models.Model):
    nombre_plan = models.CharField(max_length=50, verbose_name="Nombre del Plan")
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Mensual")
    limite_usuarios = models.IntegerField(verbose_name="Límite de Usuarios")
    limite_pqrs = models.IntegerField(verbose_name="Límite de PQRS Mensuales")

    def __str__(self):
        return self.nombre_plan

class Empresa(models.Model):
    nombre_empresa = models.CharField(max_length=150, verbose_name="Nombre de la Empresa")
    nit = models.CharField(max_length=20, unique=True, verbose_name="NIT de la Empresa")
    telefono = models.CharField(max_length=15, blank=True, null=True, verbose_name="Teléfono")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    id_plan = models.ForeignKey(Plan, on_delete=models.PROTECT, verbose_name="Plan Contratado")
    fecha_inicio_suscripcion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha inicio suscripción")
    fecha_fin_suscripcion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha fin suscripción")
    ref_payco = models.CharField(max_length=100, null=True, blank=True, verbose_name="Referencia ePayco")
    pago_activo = models.BooleanField(default=False, verbose_name="Pago activo")

    def __str__(self):
        return self.nombre_empresa