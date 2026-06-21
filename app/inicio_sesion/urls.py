from django.urls import path
from .views import *

urlpatterns = [

    
    # Rutas de inicio de sesión
    path('', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # Rutas de panel de control para administradores
    path('usuarios/', gestionar_usuarios, name='gestionar_usuarios'),

    # Ruta de actualizar contraseña inicial
    path('cambiar-password-inicial/', cambiar_password_inicial, name='cambiar_password_inicial'),

    #Rutas para recuperación de contraseña
    path('recuperar-password/',solicitar_recuperacion,name='solicitar_recuperacion'),
    path('validar-codigo/', validar_codigo,name='validar_codigo'),
    path('reenviar-codigo/',reenviar_codigo,name='reenviar_codigo'),
    path('cambiar-password/', cambiar_password,name='cambiar_password'),


]