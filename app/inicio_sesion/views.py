from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import *
from .forms import *
from django.views.decorators.http import require_http_methods
from .decorador import *
from django.contrib.messages import get_messages
from django.core.mail import send_mail
import requests
from .graph import enviar_correo_via_graph


def login_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            usuario = Usuario.objects.get(username=username)

            if usuario.check_password(password):

                request.session['id_usuario'] = usuario.id_usuario
                request.session['nombre'] = usuario.nombre_completo
                request.session['rol'] = usuario.rol

                if usuario.rol == '1':
                    return redirect('panel_admin')

                elif usuario.rol == '2':
                    return redirect('panel_empleado')

            else:
                messages.error(request, 'Contraseña incorrecta')

        except Usuario.DoesNotExist:
            messages.error(request, 'El usuario no existe')

    return render(request, 'inicio_sesion/login.html')

@login_requerido
def logout_view(request):
    # Eliminar todos los mensajes antes de destruir la sesión
    storage = get_messages(request)
    for _ in storage:
        pass
    storage.used = True
    request.session.flush()
    return redirect('login')


#==========================================================
# VISTA DE PANEL DE CONTROL PARA ADMINISTRADORES    
#==========================================================
@login_requerido
@solo_admin
def gestionar_usuarios(request):
    accion = request.GET.get('accion', 'listar')  # Por defecto, lista
    usuario_id = request.GET.get('id')

    # Variables de contexto por defecto
    context = {
        'accion': accion,
        'usuarios': Usuario.objects.all().order_by('-fecha_ultima_modificacion'),
        'form': None,
        'usuario': None,
    }

    # ========== CREAR ==========
    if accion == 'crear':
        if request.method == 'POST':
            form = CrearUsuarioForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Usuario creado con éxito.')
                return redirect('gestionar_usuarios')  # Redirige a la lista
            else:
                context['form'] = form
        else:
            context['form'] = CrearUsuarioForm()

    # ========== EDITAR ==========
    elif accion == 'editar':
        usuario = get_object_or_404(Usuario, pk=usuario_id)
        context['usuario'] = usuario
        if request.method == 'POST':
            form = EditarUsuarioForm(request.POST, instance=usuario)
            if form.is_valid():
                form.save()
                messages.success(request, 'Usuario actualizado correctamente.')
                return redirect('gestionar_usuarios')
            else:
                context['form'] = form
        else:
            context['form'] = EditarUsuarioForm(instance=usuario)

    # ========== ELIMINAR ==========
    elif accion == 'eliminar':
        usuario = get_object_or_404(Usuario, pk=usuario_id)
        context['usuario'] = usuario
        if request.method == 'POST':
            usuario.delete()
            messages.success(request, 'Usuario eliminado correctamente.')
            return redirect('gestionar_usuarios')

    # ========== LISTAR (por defecto) ==========
    # No requiere lógica adicional, el contexto ya tiene 'usuarios'

    return render(request, 'inicio_sesion/usuarios/gestionar_usuarios.html', context)


#=========================================================
# FUNCION DE CAMBIO DE CONTRASEÑA
#==========================================================
@login_requerido   # ← importante
@require_http_methods(['POST'])
def cambiar_password_inicial(request):
    usuario = Usuario.objects.get(pk=request.session['id_usuario'])
    
    password_actual = request.POST.get('password_actual')
    nuevo_email = request.POST.get('correo')
    nueva_password = request.POST.get('nueva_password')
    confirm_password = request.POST.get('confirm_password')

    if not usuario.check_password(password_actual):
        messages.error(request, 'Contraseña actual incorrecta.')
        return redirect(request.META.get('HTTP_REFERER', 'panel_admin' if usuario.rol == '1' else 'panel_empleado'))

    if nueva_password != confirm_password:
        messages.error(request, 'Las contraseñas nuevas no coinciden.')
        return redirect(request.META.get('HTTP_REFERER'))

    if nuevo_email:
        usuario.correo = nuevo_email
    
    usuario.set_password(nueva_password)
    usuario.save()

    messages.success(request, 'Contraseña y correo actualizados correctamente.')
    if usuario.rol == '1':
        return redirect('panel_admin')
    else:
        return redirect('panel_empleado')
    



#=========================================================
# VIEW PARA SOLICITAR CAMBIO DE CONTRASEÑA SI SE OLVIDA
#=========================================================

def solicitar_recuperacion(request):

    if request.method == 'POST':

        correo = request.POST.get('correo')

        try:
            usuario = Usuario.objects.get(correo=correo)

            RecuperacionCodigo.objects.filter(
                usuario=usuario,
                usado=False
            ).delete()

            codigo_recuperacion = RecuperacionCodigo.objects.create(
                usuario=usuario
            )

            # ── Renderizar la plantilla HTML del correo ──
            cuerpo_html = render_to_string(
                'inicio_sesion/recuperar_contrasena/plantilla_envio_correo.html',
                {
                    'usuario': usuario,
                    'codigo': codigo_recuperacion.codigo,
                }
            )

            # ── Envío vía Microsoft Graph (reemplaza Power Automate) ──
            try:
                respuesta = enviar_correo_via_graph(
                    destinatario=usuario.correo,
                    asunto='Recuperación de contraseña',
                    cuerpo_html=cuerpo_html,
                )

                if respuesta.status_code not in (200, 202):
                    messages.error(
                        request,
                        f'Error al enviar el correo: {respuesta.status_code} - {respuesta.text}'
                    )
                    return render(request, 'inicio_sesion/recuperar_contrasena/solicitar_cambio.html')

                messages.success(
                    request,
                    'Se envió un código de recuperación a tu correo.'
                )

            except requests.exceptions.RequestException as e:

                messages.error(
                    request,
                    f'Error al enviar el correo: {str(e)}'
                )

                return render(request, 'inicio_sesion/recuperar_contrasena/solicitar_cambio.html')

            request.session['correo_recuperacion'] = usuario.correo

            return redirect('validar_codigo')

        except Usuario.DoesNotExist:

            messages.error(
                request,
                'No existe una cuenta asociada a ese correo.'
            )

    return render(request, 'inicio_sesion/recuperar_contrasena/solicitar_cambio.html')


#=========================================================
# VIEW PARA VERIFICAR EL CODIGO DE RECUPERACION
#=========================================================

def validar_codigo(request):

    correo = request.session.get('correo_recuperacion')

    if not correo:
        return redirect('solicitar_recuperacion')

    if request.method == 'POST':

        codigo = request.POST.get('codigo')

        try:

            usuario = Usuario.objects.get(correo=correo)

            recuperacion = RecuperacionCodigo.objects.get(
                usuario=usuario,
                codigo=codigo,
                usado=False
            )

            if not recuperacion.es_valido():
                messages.error(request, 'El código ha expirado.')
            else:

                recuperacion.usado = True
                recuperacion.save()

                request.session['usuario_recuperacion'] = usuario.id_usuario

                return redirect('cambiar_password')

        except RecuperacionCodigo.DoesNotExist:
            messages.error(request, 'Código incorrecto.')

    return render(request, 'inicio_sesion/recuperar_contrasena/modificar_contrasena.html', {
        'paso': 'codigo'
    })


#=========================================================
# VIEW PARA REENVIAR CÓDIGO DE RECUPERACIÓN
#=========================================================

def reenviar_codigo(request):

    correo = request.session.get('correo_recuperacion')

    if not correo:
        return redirect('solicitar_recuperacion')

    try:

        usuario = Usuario.objects.get(correo=correo)

        ultimo_codigo = RecuperacionCodigo.objects.filter(
            usuario=usuario
        ).order_by('-creado_en').first()

        if ultimo_codigo:

            tiempo_transcurrido = (
                timezone.now() - ultimo_codigo.creado_en
            ).total_seconds()

            if tiempo_transcurrido < 60:

                segundos_restantes = int(
                    60 - tiempo_transcurrido
                )

                messages.error(
                    request,
                    f'Debes esperar {segundos_restantes} segundos para solicitar otro código.'
                )

                return redirect('validar_codigo')

        RecuperacionCodigo.objects.filter(
            usuario=usuario,
            usado=False
        ).delete()

        codigo_recuperacion = RecuperacionCodigo.objects.create(
            usuario=usuario
        )

        # ── Renderizar la plantilla HTML del correo ──
        cuerpo_html = render_to_string(
            'inicio_sesion/recuperar_contrasena/plantilla_envio_correo.html',
            {
                'usuario': usuario,
                'codigo': codigo_recuperacion.codigo,
            }
        )

        # ── Envío vía Microsoft Graph (reemplaza Power Automate) ──
        try:
            respuesta = enviar_correo_via_graph(
                destinatario=usuario.correo,
                asunto='Nuevo código de recuperación',
                cuerpo_html=cuerpo_html,
            )

            if respuesta.status_code not in (200, 202):
                messages.error(
                    request,
                    f'Error al enviar el correo: {respuesta.status_code} - {respuesta.text}'
                )
            else:
                messages.success(
                    request,
                    'Se envió un nuevo código a tu correo.'
                )

        except requests.exceptions.RequestException as e:
            messages.error(
                request,
                f'Error al enviar el correo: {str(e)}'
            )

    except Usuario.DoesNotExist:

        messages.error(
            request,
            'No fue posible reenviar el código.'
        )

    except Exception as e:

        messages.error(
            request,
            f'Error al enviar el correo: {str(e)}'
        )

    return redirect('validar_codigo')


#=========================================================
# VIEW PARA CAMBIAR LA CONTRASEÑA DESPUES DE VERIFICAR EL CODIGO
#=========================================================
def cambiar_password(request):

    usuario_id = request.session.get('usuario_recuperacion')

    if not usuario_id:
        return redirect('solicitar_recuperacion')

    usuario = Usuario.objects.get(id_usuario=usuario_id)

    if request.method == 'POST':

        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden.')

        else:

            usuario.set_password(password1)
            usuario.save()

            request.session.pop('usuario_recuperacion', None)
            request.session.pop('correo_recuperacion', None)

            messages.success(
                request,
                'Contraseña actualizada correctamente.'
            )

            return redirect('login')

    return render(request, 'inicio_sesion/recuperar_contrasena/modificar_contrasena.html', {
        'paso': 'password'
    })