from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Usuario


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


def logout_view(request):

    request.session.flush()

    return redirect('login')