from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Usuario(models.Model):

    ROL_CHOICES = (
        ('1', 'Administrador'),
        ('2', 'Empleado'),
    )

    id_usuario = models.CharField(
        max_length=20,
        primary_key=True
    )

    nombre_completo = models.CharField(
        max_length=255
    )

    password = models.CharField(
        max_length=255
    )

    rol = models.CharField(
        max_length=1,
        choices=ROL_CHOICES,
        default='2'
    )

    estado = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        default='Activo'
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
    
    