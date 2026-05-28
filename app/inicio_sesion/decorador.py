from django.shortcuts import redirect


def login_requerido(view_func):

    def wrapper(request, *args, **kwargs):

        if not request.session.get('id_usuario'):
            return redirect('login')

        return view_func(request, *args, **kwargs)

    return wrapper


def solo_admin(view_func):

    def wrapper(request, *args, **kwargs):

        if request.session.get('rol') != '1':
            return redirect('login')

        return view_func(request, *args, **kwargs)

    return wrapper


def solo_empleado(view_func):

    def wrapper(request, *args, **kwargs):

        if request.session.get('rol') != '2':
            return redirect('login')

        return view_func(request, *args, **kwargs)

    return wrapper


