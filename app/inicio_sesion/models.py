from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import random, string
from django.utils import timezone
from datetime import timedelta

class Usuario(models.Model):

    ROL_CHOICES = (
        ('1', 'Administrador'),
        ('2', 'Empleado'),
    )

    id_usuario = models.AutoField(
        primary_key=True
    )

    username = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    nombre_completo = models.CharField(
        max_length=255
    )

    correo = models.EmailField(
        unique=True,
        null=True,
        blank=True
    )

    password = models.CharField(
        max_length=255
    )

    rol = models.CharField(
        max_length=1,
        choices=ROL_CHOICES,
        default='2'
    )



    ESTADO_CHOICES = (
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    )
    
    estado = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default='Activo'
    )

    fecha_ultima_modificacion = models.DateTimeField(
        auto_now=True
    )

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    @property
    def es_admin(self):
        return self.rol == '1'

    @property
    def es_empleado(self):
        return self.rol == '2'

    def __str__(self):
        return self.nombre_completo

    class Meta:
        db_table = 'usuario'

class RecuperacionCodigo(models.Model):
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    codigo = models.CharField(max_length=6, unique=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField()
    usado = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = ''.join(random.choices(string.digits, k=6))
        if not self.expira_en:
            self.expira_en = timezone.now() + timedelta(minutes=3)
        super().save(*args, **kwargs)

    def es_valido(self):
        return not self.usado and self.expira_en > timezone.now()

    class Meta:
        db_table = 'recuperacion_codigo'