from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from inicio_sesion.decorador import *
from .models import * 
from inicio_sesion.models import *
from django.contrib import messages
from .forms import *
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import json
import re
from django.views.decorators.csrf import ensure_csrf_cookie
from .utils import *
import uuid
from django.utils import timezone
from datetime import date
import calendar


def detectar_tipo_archivo_contenido(url_archivo, tipo_forzado=''):
    """Detecta el tipo de archivo usando una etiqueta forzada o la URL."""
    tipo_forzado = (tipo_forzado or '').strip().lower()
    if tipo_forzado in ['imagen', 'img', 'image']:
        return 'imagen'
    if tipo_forzado in ['video', 'vid']:
        return 'video'

    url_limpia = limpiar_iframe(url_archivo)
    url_lower = url_limpia.lower()

    if any(x in url_lower for x in ['.mp4', '.avi', '.mov', '.mkv', 'youtube.com', 'youtu.be', 'vimeo.com']):
        return 'video'
    if any(x in url_lower for x in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
        return 'imagen'
    if '.pdf' in url_lower:
        return 'pdf'
    if any(x in url_lower for x in ['.doc', '.docx']):
        return 'word'
    if any(x in url_lower for x in ['.xls', '.xlsx']):
        return 'excel'
    if any(x in url_lower for x in ['.ppt', '.pptx']):
        return 'powerpoint'
    if 'sharepoint.com' in url_lower or 'onedrive.com' in url_lower or 'embed.aspx' in url_lower or 'doc.aspx' in url_lower:
        return 'sharepoint'

    return 'otro'


def _guardar_pregunta_en_quiz(quiz, data, pregunta=None):
    """Crea o actualiza una pregunta y sus opciones reutilizando la misma lógica."""
    texto = (data.get('texto') or '').strip()
    if not texto:
        return None, JsonResponse({'success': False, 'error': 'El texto es requerido'}, status=400)

    tipo_respuesta = (data.get('tipo_respuesta') or 'unica').strip()

    imagen_raw = (data.get('imagen_url') or '').strip()
    imagen_url = None
    if imagen_raw:
        imagen_url = limpiar_iframe(imagen_raw) if '<iframe' in imagen_raw.lower() else imagen_raw

    archivo_raw = (data.get('archivo_apoyo') or '').strip()
    archivo_pregunta = pregunta.archivo_apoyo if pregunta and pregunta.archivo_apoyo else None
    if archivo_raw:
        archivo_datos = preparar_archivo_sharepoint(archivo_raw)
        archivo_url = archivo_datos['url_limpia'] if archivo_datos['url_limpia'] else archivo_raw
        if archivo_url:
            nombre_archivo = archivo_datos['nombre']
            if archivo_pregunta:
                archivo_pregunta.nombre = nombre_archivo
                archivo_pregunta.url_original = archivo_raw
                archivo_pregunta.url_visualizacion = archivo_datos['url_visualizacion']
                archivo_pregunta.url_descarga = archivo_datos['url_descarga']
                archivo_pregunta.save()
            else:
                archivo_pregunta = ArchivoPregunta.objects.create(
                    nombre=nombre_archivo,
                    url_original=archivo_raw,
                    url_visualizacion=archivo_datos['url_visualizacion'],
                    url_descarga=archivo_datos['url_descarga']
                )

    opciones_data = data.get('opciones', []) or []
    if tipo_respuesta in ['unica', 'multiple', 'vf'] and not opciones_data:
        return None, JsonResponse({'success': False, 'error': 'Agrega al menos una opción de respuesta'}, status=400)

    if tipo_respuesta == 'unica':
        correctas = [opcion for opcion in opciones_data if opcion.get('es_correcta')]
        if len(correctas) != 1:
            return None, JsonResponse({'success': False, 'error': 'La respuesta única debe tener exactamente una opción correcta'}, status=400)

    if tipo_respuesta == 'vf':
        correctas = [opcion for opcion in opciones_data if opcion.get('es_correcta')]
        if len(correctas) != 1:
            return None, JsonResponse({'success': False, 'error': 'Verdadero/Falso debe tener exactamente una respuesta correcta'}, status=400)

    if pregunta is None:
        pregunta = Pregunta.objects.create(
            quiz=quiz,
            texto=texto,
            descripcion=data.get('descripcion', ''),
            tipo_respuesta=tipo_respuesta,
            pista=data.get('pista', ''),
            explicacion=data.get('explicacion', ''),
            orden=quiz.preguntas.count() + 1,
            imagen_url=imagen_url if imagen_url else None,
            archivo_apoyo=archivo_pregunta
        )
    else:
        pregunta.texto = texto
        pregunta.descripcion = data.get('descripcion', '')
        pregunta.tipo_respuesta = tipo_respuesta
        pregunta.pista = data.get('pista', '')
        pregunta.explicacion = data.get('explicacion', '')
        pregunta.imagen_url = imagen_url if imagen_url else None
        pregunta.archivo_apoyo = archivo_pregunta
        pregunta.save()
        pregunta.opciones.all().delete()

    for opcion_data in opciones_data:
        OpcionRespuesta.objects.create(
            pregunta=pregunta,
            texto=opcion_data.get('texto', ''),
            es_correcta=opcion_data.get('es_correcta', False)
        )

    return pregunta, None



# =========================================================
# PANELES
# =========================================================

@login_requerido
@solo_admin
def panel_admin(request):
    usuario = Usuario.objects.get(pk=request.session['id_usuario'])
    usar_password_default = usuario.check_password('Empleado2026*')
    
    contexto = {
        'nombre': request.session.get('nombre'),
        'mostrar_modal_cambio': usar_password_default,
        'correo': usuario.correo or '',   # ← lo usaremos en el template
    }
    return render(request, 'contenido/panel_admin.html', contexto)

@login_requerido
@solo_empleado
def panel_empleado(request):
    usuario = Usuario.objects.get(pk=request.session['id_usuario'])
    usar_password_default = usuario.check_password('Empleado2026*')
    
    contexto = {
        'nombre': request.session.get('nombre'),
        'mostrar_modal_cambio': usar_password_default,
        'correo': usuario.correo or '',
    }
    return render(request, 'contenido/panel_empleado.html', contexto)
    
    


# =========================================================
# NOTICIAS
# =========================================================

# =========================================================
# NOTICIAS ADMINISTRAR (ADMINISTRADOR)
# =========================================================

@login_requerido
@solo_admin
def administrar_noticias(request, id_noticia=None):
    """
    Vista unificada para listar, crear y editar noticias.
    """
    noticias = Noticia.objects.all().order_by('-fecha_public')
    noticia = None
    contenido = None
    form_tiene_errores = False

    # Modo edición: cargar la noticia existente y su primer contenido
    if id_noticia:
        noticia = get_object_or_404(Noticia, id_noticia=id_noticia)
        contenido = noticia.contenidos.first()

    # Procesar el formulario (POST)
    if request.method == 'POST':
        noticia_form = NoticiaForm(request.POST, instance=noticia)
        contenido_form = ContenidoForm(request.POST, instance=contenido)

        if noticia_form.is_valid() and contenido_form.is_valid():
            # Guardar noticia
            noticia_guardada = noticia_form.save(commit=False)

            # Si es creación, generar ID automático y asignar usuario
            if not noticia:
                noticia_guardada.id_noticia = uuid.uuid4().hex[:10]
                noticia_guardada.usuario_id = request.session.get('id_usuario')

            noticia_guardada.save()

            # Guardar contenido asociado
            contenido_guardado = contenido_form.save(commit=False)
            contenido_guardado.noticia = noticia_guardada

            # Limpiar URL del iframe solo si se proporcionó un valor
            if contenido_guardado.url_recurso:
                contenido_guardado.url_recurso = limpiar_iframe(contenido_guardado.url_recurso)

            contenido_guardado.save()

            # Mensajes de éxito diferenciados
            if not noticia:
                messages.success(request, 'Noticia creada exitosamente.')
            else:
                messages.success(request, 'Noticia editada exitosamente.')

            return redirect('administrar_noticias')
        else:
            form_tiene_errores = True

    # Método GET: preparar formularios vacíos o con datos de edición
    else:
        noticia_form = NoticiaForm(instance=noticia)
        contenido_form = ContenidoForm(instance=contenido)

        # En creación, forzar tipo de contenido por defecto a "imagen"
        if not noticia:
            contenido_form.initial['tipo_con'] = 'imagen'

    contexto = {
        'noticias': noticias,
        'noticia_form': noticia_form,
        'contenido_form': contenido_form,
        'editando': noticia is not None,
        'noticia': noticia,          # necesario para el action del modal en edición
        'form_tiene_errores': form_tiene_errores,
    }

    return render(request, 'contenido/noticias/admin_noticias.html', contexto)

@login_requerido
@solo_admin
def eliminar_noticia(request, id_noticia):
    noticia = get_object_or_404(Noticia, id_noticia=id_noticia)
    noticia.delete()
    messages.success(request, 'Noticia eliminada correctamente.')
    return redirect('administrar_noticias')


# =========================================================
# VER NOTICIAS (GENERAL)
# =========================================================

@login_requerido
def ver_noticias(request, from_admin=False):

    noticias = Noticia.objects.prefetch_related(
        'contenidos'
    ).all().order_by('-fecha_public')
    
    # Determinar si viene desde admin o desde empleado
    desde_admin = from_admin or request.GET.get('from') == 'admin' or request.session.get('rol') == 'admin'

    contexto = {
        'noticias': noticias,
        'desde_admin': desde_admin,  # Pasar información de dónde viene
        'rol': request.session.get('rol')
    }

    return render(
        request,
        'contenido/noticias/ver_noticias.html',
        contexto
    )
    
# =========================================================
# CURSOS
# =========================================================

# =========================================================
# CREAR CURSO
# =========================================================
@login_requerido
@solo_admin
def gestionar_cursos(request):
    cursos = Curso.objects.prefetch_related('contenidos').all().order_by('-fecha_public')
    form = CursoForm()

    if request.method == 'POST':
        form = CursoForm(request.POST)
        if form.is_valid():
            curso = form.save(commit=False)
            if not curso.id_curso:
                from .utils import generar_id_unico
                curso.id_curso = generar_id_unico('CURSO_')
            curso.save()

            # Guardar imagen
            imagen_url = request.POST.get('imagen_url', '').strip()
            if imagen_url:
                if '<iframe' in imagen_url.lower():
                    url_limpia = limpiar_iframe(imagen_url)
                else:
                    url_limpia = imagen_url
                Contenido.objects.update_or_create(
                    curso=curso,
                    tipo_con='imagen',
                    defaults={'url_recurso': url_limpia, 'nombre_archivo': 'Imagen del Curso'}
                )
            messages.success(request, 'Curso creado exitosamente.')
            return redirect('gestionar_cursos')

    context = {'cursos': cursos, 'form': form}
    return render(request, 'contenido/cursos/gestionar_cursos.html', context)


# =========================================================
# EDITAR CURSO
# =========================================================
@login_requerido
@solo_admin
def editar_curso(request, id_curso):
    curso = get_object_or_404(Curso, id_curso=id_curso)
    initial_data = {}
    contenido_imagen = curso.contenidos.filter(tipo_con='imagen').first()
    if contenido_imagen:
        initial_data['imagen_url'] = contenido_imagen.url_recurso

    if request.method == 'POST':
        form = CursoForm(request.POST, instance=curso)
        if form.is_valid():
            curso_guardado = form.save()
            imagen_url = request.POST.get('imagen_url', '').strip()
            if imagen_url:
                if '<iframe' in imagen_url.lower():
                    url_limpia = limpiar_iframe(imagen_url)
                else:
                    url_limpia = imagen_url
                Contenido.objects.update_or_create(
                    curso=curso_guardado,
                    tipo_con='imagen',
                    defaults={'url_recurso': url_limpia, 'nombre_archivo': 'Imagen del Curso'}
                )
            messages.success(request, 'Curso actualizado exitosamente.')
            return redirect('gestionar_cursos')
    else:
        form = CursoForm(instance=curso, initial=initial_data)

    cursos = Curso.objects.prefetch_related('contenidos').all()
    context = {'form': form, 'cursos': cursos, 'editando': True}
    return render(request, 'contenido/cursos/gestionar_cursos.html', context)


# =========================================================
# ELIMINAR CURSO
# =========================================================

@login_requerido
@solo_admin
def eliminar_curso(request, id_curso):
    curso = get_object_or_404(Curso, id_curso=id_curso)
    curso.delete()
    messages.success(request, 'Curso eliminado correctamente.')
    return redirect('gestionar_cursos')

# =========================================================
# AGREGAR CONTENIDO A CURSO
# =========================================================
@login_requerido
@solo_admin
@ensure_csrf_cookie
def agregar_contenido(request, id_curso):
    curso = get_object_or_404(Curso, id_curso=id_curso)
    
    # ← CAMBIADO: ordenar por fecha_creacion ascendente (más antiguo primero)
    bloques_principal = curso.bloques_contenido.filter(
        seccion='principal',
        activo=True
    ).order_by('fecha_creacion')
    
    bloques_lateral = curso.bloques_contenido.filter(
        seccion='lateral',
        activo=True
    ).order_by('fecha_creacion')
    
    form_bloque = BloqueContenidoForm()
    
    context = {
        'curso': curso,
        'bloques_principal': bloques_principal,
        'bloques_lateral': bloques_lateral,
        'form_bloque': form_bloque,
    }
    
    return render(request, 'contenido/cursos/agregar_contenido.html', context)

@login_requerido
@solo_admin
@require_POST
def guardar_bloque_contenido(request, id_curso):
    try:
        curso = get_object_or_404(Curso, id_curso=id_curso)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST

        seccion = data.get('seccion')
        tipo = data.get('tipo')

        if not seccion or not tipo:
            return JsonResponse({'success': False, 'error': 'Sección y tipo son requeridos'}, status=400)

        if seccion == 'principal':
            if tipo != 'banner':
                return JsonResponse({'success': False, 'error': 'Solo se permite Banner Grande en la sección principal'}, status=400)
        elif seccion == 'lateral':
            tipos_permitidos = ['informativa', 'archivos', 'archivo_categorizado', 'enlace']
            if tipo not in tipos_permitidos:
                return JsonResponse({'success': False, 'error': f'Tipo no válido. Use: {tipos_permitidos}'}, status=400)

        url_recurso_original = data.get('url_recurso', '')
        url_recurso_limpia = limpiar_iframe(url_recurso_original)

        if tipo in ['banner', 'enlace']:
            url_final = url_recurso_limpia
        else:
            url_final = ''

        bloque = BloqueContenido.objects.create(
            curso=curso,
            seccion=seccion,
            tipo=tipo,
            titulo=data.get('titulo', ''),
            descripcion=data.get('descripcion', ''),
            url_recurso=url_final,
            orden=data.get('orden', 0),
            render_type=data.get('render_type', 'imagen_debajo') if seccion == 'principal' else None
        )

        archivos_adjuntos = []
        urls_archivos = data.get('urls_archivos', '')
        nombres_archivos = data.get('nombres_archivos', '')
        tipos_archivos = data.get('tipos_archivos', '')

        if tipo in ['archivos', 'archivo_categorizado'] and urls_archivos:
            urls = [url.strip() for url in urls_archivos.split('\n') if url.strip()]
            nombres = [nombre.strip() for nombre in nombres_archivos.split('\n') if nombre.strip()] if nombres_archivos else []
            tipos = [tipo_archivo.strip() for tipo_archivo in tipos_archivos.split('\n') if tipo_archivo.strip()] if tipos_archivos else []
            
            for i, url in enumerate(urls):
                url_limpia = limpiar_iframe(url)
                tipo_seleccionado = tipos[i] if i < len(tipos) else ''
                tipo_contenido = detectar_tipo_archivo_contenido(url_limpia, tipo_seleccionado)
                
                # Obtener nombre del archivo
                nombre_archivo = ''
                if i < len(nombres) and nombres[i]:
                    nombre_archivo = nombres[i]
                else:
                    title_match = re.search(r'title="([^"]+)"', url)
                    if title_match:
                        nombre_archivo = title_match.group(1)
                    else:
                        nombre_archivo = url_limpia.split('/')[-1] if url_limpia else 'Archivo'
                
                # Guardar contenido con tipo detectado
                contenido = Contenido.objects.create(
                    bloque=bloque,
                    tipo_con=tipo_contenido,
                    url_recurso=url_limpia,
                    nombre_archivo=nombre_archivo
                )
                
                archivos_adjuntos.append({
                    'id': contenido.id_contenido,
                    'url_archivo': contenido.url_recurso,
                    'tipo_archivo': contenido.tipo_con,
                    'icono': contenido.icono,
                    'tipo_display': contenido.get_tipo_con_display(),
                    'es_sharepoint': contenido.es_sharepoint,
                    'url_visualizacion': contenido.url_visualizacion,
                    'url_descarga': contenido.url_descarga,
                    'nombre': contenido.get_nombre_display(),
                })

        return JsonResponse({
            'success': True,
            'bloque': {
                'id': bloque.id,
                'tipo': bloque.tipo,
                'titulo': bloque.titulo,
                'descripcion': bloque.descripcion,
                'url_recurso': bloque.url_recurso,
                'seccion': bloque.seccion,
                'render_type': bloque.render_type,
                'fecha_creacion': bloque.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                'archivos': archivos_adjuntos,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error del servidor: {str(e)}'}, status=500)

@login_requerido
@solo_admin
@require_POST
def actualizar_render_type(request, id_curso):
    try:
        curso = get_object_or_404(Curso, id_curso=id_curso)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST

        nuevo_render_type = data.get('render_type')
        if nuevo_render_type not in ['imagen_debajo', 'imagen_fondo']:
            return JsonResponse({'success': False, 'error': 'Tipo de renderizado no válido'}, status=400)

        BloqueContenido.objects.filter(curso=curso, seccion='principal').update(render_type=nuevo_render_type)
        return JsonResponse({'success': True, 'render_type': nuevo_render_type})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error del servidor: {str(e)}'}, status=500)

@login_requerido
@solo_admin
@require_POST
def eliminar_bloque(request, id_bloque):
    """Elimina un bloque y sus contenidos asociados en cascada."""
    try:
        bloque = get_object_or_404(BloqueContenido, id=id_bloque)
        bloque.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error del servidor: {str(e)}'}, status=500)

@login_requerido
@solo_admin
@require_POST
def editar_bloque_contenido(request, id_bloque):
    """Actualiza un bloque de contenido existente."""
    try:
        bloque = get_object_or_404(BloqueContenido, id=id_bloque)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST
        
        # Actualizar campos básicos del bloque
        bloque.titulo = data.get('titulo', bloque.titulo)
        bloque.descripcion = data.get('descripcion', bloque.descripcion)
        
        # Actualizar URL del recurso si es necesario
        if 'url_recurso' in data:
            url_recurso_original = data.get('url_recurso', '')
            url_recurso_limpia = limpiar_iframe(url_recurso_original)
            
            if bloque.tipo in ['banner', 'enlace']:
                bloque.url_recurso = url_recurso_limpia
            else:
                bloque.url_recurso = ''
        
        # Actualizar render_type si es sección principal
        if 'render_type' in data and bloque.seccion == 'principal':
            bloque.render_type = data.get('render_type')
        
        bloque.save()
        
        # Actualizar contenidos/archivos si se proporcionan
        urls_archivos = data.get('urls_archivos', '')
        nombres_archivos = data.get('nombres_archivos', '')
        tipos_archivos = data.get('tipos_archivos', '')
        
        if bloque.tipo in ['archivos', 'archivo_categorizado'] and urls_archivos:
            # Borrar contenidos antiguos
            bloque.contenidos.all().delete()
            
            # Crear nuevos contenidos
            urls = [url.strip() for url in urls_archivos.split('\n') if url.strip()]
            nombres = [nombre.strip() for nombre in nombres_archivos.split('\n') if nombre.strip()] if nombres_archivos else []
            tipos = [tipo_archivo.strip() for tipo_archivo in tipos_archivos.split('\n') if tipo_archivo.strip()] if tipos_archivos else []
            
            archivos_adjuntos = []
            for i, url in enumerate(urls):
                url_limpia = limpiar_iframe(url)
                tipo_seleccionado = tipos[i] if i < len(tipos) else ''
                tipo_contenido = detectar_tipo_archivo_contenido(url_limpia, tipo_seleccionado)
                
                # Obtener nombre del archivo
                nombre_archivo = ''
                if i < len(nombres) and nombres[i]:
                    nombre_archivo = nombres[i]
                else:
                    title_match = re.search(r'title="([^"]+)"', url)
                    if title_match:
                        nombre_archivo = title_match.group(1)
                    else:
                        nombre_archivo = url_limpia.split('/')[-1] if url_limpia else 'Archivo'
                
                # Guardar contenido con tipo detectado
                contenido = Contenido.objects.create(
                    bloque=bloque,
                    tipo_con=tipo_contenido,
                    url_recurso=url_limpia,
                    nombre_archivo=nombre_archivo
                )
                
                archivos_adjuntos.append({
                    'id': contenido.id_contenido,
                    'url_archivo': contenido.url_recurso,
                    'tipo_archivo': contenido.tipo_con,
                    'icono': contenido.icono,
                    'tipo_display': contenido.get_tipo_con_display(),
                    'es_sharepoint': contenido.es_sharepoint,
                    'url_visualizacion': contenido.url_visualizacion,
                    'url_descarga': contenido.url_descarga,
                    'nombre': contenido.get_nombre_display(),
                })
        
        return JsonResponse({
            'success': True,
            'bloque': {
                'id': bloque.id,
                'tipo': bloque.tipo,
                'titulo': bloque.titulo,
                'descripcion': bloque.descripcion,
                'url_recurso': bloque.url_recurso,
                'seccion': bloque.seccion,
                'render_type': bloque.render_type,
                'fecha_creacion': bloque.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            }
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error del servidor: {str(e)}'}, status=500)
    
@login_requerido
@solo_admin
@require_POST
def eliminar_contenido_ajax(request, id):
    try:
        contenido = Contenido.objects.get(id_contenido=id)
        # Si el contenido es un archivo físico, elimínalo aquí si es necesario
        contenido.delete()
        return JsonResponse({'success': True})
    except Contenido.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Contenido no encontrado'})
# =========================================================
# CREAR QUIZ
# =========================================================

@login_requerido
@solo_admin
def crear_quiz(request, id_curso):
    """Vista para crear/editar un quiz, incluyendo asignación de usuarios al curso."""
    curso = get_object_or_404(Curso, id_curso=id_curso)
    quiz = curso.quiz if hasattr(curso, 'quiz') else None

    if request.method == 'POST':
        data = json.loads(request.body)

        if not data.get('titulo'):
            return JsonResponse({'success': False, 'error': 'El título es requerido'}, status=400)

        if quiz:
            quiz.titulo = data.get('titulo')
            quiz.descripcion = data.get('descripcion', '')
            quiz.save()
        else:
            quiz = Quiz.objects.create(
                titulo=data.get('titulo'),
                descripcion=data.get('descripcion', ''),
                curso=curso
            )

        # --- Asignación de usuarios al curso ---
        usuarios_ids = data.get('usuarios_asignados', [])
        if isinstance(usuarios_ids, list):
            usuarios_ids_validos = [int(uid) for uid in usuarios_ids if str(uid).isdigit()]

            AsignacionCurso.objects.filter(curso=curso).exclude(
                usuario_id__in=usuarios_ids_validos
            ).delete()

            existentes = set(
                AsignacionCurso.objects.filter(curso=curso).values_list('usuario_id', flat=True)
            )
            nuevas = [
                AsignacionCurso(usuario_id=uid, curso=curso)
                for uid in usuarios_ids_validos if uid not in existentes
            ]
            if nuevas:
                AsignacionCurso.objects.bulk_create(nuevas)

        return JsonResponse({
            'success': True,
            'quiz_id': quiz.id,
            'mensaje': 'Quiz creado/actualizado exitosamente'
        })

    usuarios_asignados_ids = list(
        AsignacionCurso.objects.filter(curso=curso).values_list('usuario_id', flat=True)
    )

    context = {
        'curso': curso,
        'quiz': quiz,
        'preguntas': quiz.preguntas.all().order_by('orden') if quiz else [],
        'usuarios': Usuario.objects.all().order_by('nombre_completo'),
        'usuarios_asignados_ids': usuarios_asignados_ids,
    }

    return render(request, 'contenido/quiz/crear_quiz.html', context)


@login_requerido
@solo_admin
def agregar_pregunta(request, quiz_id):
    """Vista AJAX para agregar una pregunta al quiz."""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    if request.method == 'POST':
        data = json.loads(request.body)

        pregunta, error_response = _guardar_pregunta_en_quiz(quiz, data)
        if error_response:
            return error_response
        
        return JsonResponse({
            'success': True,
            'quiz_id': quiz.id,
            'pregunta_id': pregunta.id,
            'mensaje': 'Pregunta agregada exitosamente'
        })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


@login_requerido
@solo_admin
def guardar_pregunta_quiz(request, id_curso):
    """Crea o actualiza una pregunta; si el quiz no existe, lo crea automáticamente."""
    curso = get_object_or_404(Curso, id_curso=id_curso)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    data = json.loads(request.body)
    quiz = Quiz.objects.filter(curso=curso).first()

    if not quiz:
        quiz = Quiz.objects.create(
            titulo=(data.get('quiz_titulo') or f'Quiz - {curso.titulo}').strip(),
            descripcion=(data.get('quiz_descripcion') or '').strip(),
            activo=bool(data.get('quiz_activo', True)),
            curso=curso
        )

    pregunta_id = data.get('pregunta_id')
    pregunta = get_object_or_404(Pregunta, id=pregunta_id, quiz=quiz) if pregunta_id else None

    pregunta, error_response = _guardar_pregunta_en_quiz(quiz, data, pregunta=pregunta)
    if error_response:
        return error_response

    return JsonResponse({
        'success': True,
        'quiz_id': quiz.id,
        'pregunta_id': pregunta.id,
        'mensaje': 'Pregunta guardada exitosamente'
    })


@login_requerido
@solo_admin
def eliminar_pregunta(request, pregunta_id):
    """Elimina una pregunta del quiz."""
    pregunta = get_object_or_404(Pregunta, id=pregunta_id)
    quiz = pregunta.quiz
    pregunta.delete()  # cascada borra ProgresoUsuario huérfanos

    # Recalcular completado para todos los usuarios que tenían este quiz
    total_actual = quiz.preguntas.count()
    usuarios_con_progreso = ProgresoUsuario.objects.filter(quiz=quiz).values_list('usuario_id', flat=True).distinct()

    for usuario_id in usuarios_con_progreso:
        correctas = ProgresoUsuario.objects.filter(
            usuario_id=usuario_id, quiz=quiz, es_correcta=True
        ).count()
        completado_real = total_actual > 0 and correctas == total_actual
        ProgresoUsuario.objects.filter(
            usuario_id=usuario_id, quiz=quiz
        ).update(quiz_completado=completado_real)

    return JsonResponse({'success': True, 'mensaje': 'Pregunta eliminada'})


@login_requerido
@solo_empleado
def resolver_quiz(request, id_curso):
    """Vista para que el empleado resuelva el quiz."""
    curso = get_object_or_404(Curso, id_curso=id_curso)
    usuario_id = request.session.get('id_usuario')

    tiene_acceso = AsignacionCurso.objects.filter(
        curso=curso,
        usuario_id=usuario_id
    ).exists()

    if not tiene_acceso:
        messages.error(request, 'No tienes asignado este curso, por lo que no puedes realizar el cuestionario.')
        return redirect('ver_curso_empleado', id_curso=id_curso)

    quiz = get_object_or_404(Quiz, curso=curso)

    preguntas = quiz.preguntas.all().order_by('orden')
    total = preguntas.count()

    ProgresoUsuario.objects.filter(
        usuario_id=usuario_id,
        quiz=quiz
    ).exclude(
        pregunta_id__in=preguntas.values_list('id', flat=True)
    ).delete()

    existentes_ids = set(
        ProgresoUsuario.objects.filter(
            usuario_id=usuario_id, quiz=quiz
        ).values_list('pregunta_id', flat=True)
    )
    nuevos = [
        ProgresoUsuario(usuario_id=usuario_id, quiz=quiz, pregunta=p)
        for p in preguntas if p.id not in existentes_ids
    ]
    if nuevos:
        ProgresoUsuario.objects.bulk_create(nuevos)

    correctas = ProgresoUsuario.objects.filter(
        usuario_id=usuario_id, quiz=quiz, es_correcta=True
    ).count()
    completado_real = total > 0 and correctas == total

    ProgresoUsuario.objects.filter(
        usuario_id=usuario_id, quiz=quiz
    ).update(quiz_completado=completado_real)

    if completado_real:
        context = {
            'curso': curso,
            'quiz': quiz,
            'completado': True,
            'mensaje': 'Ya has completado este quiz. No puedes intentarlo de nuevo.'
        }
        return render(request, 'contenido/quiz/resolver_quiz.html', context)

    for pregunta in preguntas:
        archivo = pregunta.archivo_apoyo
        if archivo:
            archivo_origen = archivo.url_original or archivo.url_visualizacion or archivo.url_descarga
            archivo_datos = preparar_archivo_sharepoint(archivo_origen)
            archivo.nombre = archivo.nombre or archivo_datos['nombre']
            archivo.url_visualizacion = archivo_datos['url_visualizacion']
            archivo.url_descarga = archivo_datos['url_descarga']

    progreso_usuario = {}
    for prog in ProgresoUsuario.objects.filter(usuario_id=usuario_id, quiz=quiz):
        progreso_usuario[prog.pregunta_id] = {
            'respondida': prog.respondida,
            'es_correcta': prog.es_correcta,
            'intentos_fallidos': prog.intentos_fallidos,
            'respuesta': prog.respuesta_texto or prog.archivo_subido_url or ''
        }

    respondidas = sum(1 for p in progreso_usuario.values() if p['respondida'])

    context = {
        'curso': curso,
        'quiz': quiz,
        'preguntas': preguntas,
        'progreso': progreso_usuario,
        'total': total,
        'respondidas': respondidas,
        'correctas': correctas,
        'porcentaje': (respondidas * 100) // total if total > 0 else 0,
        'completado': completado_real
    }

    return render(request, 'contenido/quiz/resolver_quiz.html', context)

@login_requerido
@solo_empleado
@require_POST
def responder_pregunta(request):
    """API para responder una pregunta del quiz."""
    try:
        data = json.loads(request.body)
        usuario_id = request.session.get('id_usuario')
        pregunta_id = data.get('pregunta_id')
        quiz_id = data.get('quiz_id')
        respuesta = (data.get('respuesta') or '').strip()
        archivo_url_raw = (data.get('archivo_url') or '').strip()
        archivo_url = limpiar_iframe(archivo_url_raw).strip()
        tipo_archivo_seleccionado = (data.get('tipo_archivo') or '').strip().lower()
        
        if not all([usuario_id, pregunta_id, quiz_id]):
            return JsonResponse({'success': False, 'error': 'Datos incompletos'}, status=400)
        
        pregunta = get_object_or_404(Pregunta, id=pregunta_id)
        quiz = get_object_or_404(Quiz, id=quiz_id)

        progreso, _ = ProgresoUsuario.objects.get_or_create(
            usuario_id=usuario_id,
            quiz=quiz,
            pregunta=pregunta
        )

        if progreso.es_correcta:
            return JsonResponse({
                'success': False,
                'error': 'Esta pregunta ya fue validada correctamente',
                'ya_validada': True
            }, status=400)

        if pregunta.tipo_respuesta == 'archivo':
            if not archivo_url:
                return JsonResponse({'success': False, 'error': 'Debes pegar el iframe o enlace del archivo'}, status=400)
        elif not respuesta:
            return JsonResponse({'success': False, 'error': 'La respuesta es requerida'}, status=400)

        def detectar_tipo_archivo_respuesta(url_archivo):
            url = (url_archivo or '').lower()
            if not url:
                return ''
            if any(x in url for x in ['sharepoint.com', 'onedrive.com', 'embed.aspx', 'doc.aspx']):
                return 'sharepoint'
            if any(x in url for x in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
                return 'imagen'
            if any(x in url for x in ['.mp4', '.avi', '.mov', '.mkv', '.webm']):
                return 'video'
            if '.pdf' in url:
                return 'pdf'
            if any(x in url for x in ['.doc', '.docx']):
                return 'word'
            if any(x in url for x in ['.xls', '.xlsx']):
                return 'excel'
            if any(x in url for x in ['.ppt', '.pptx']):
                return 'powerpoint'
            return 'url'
        
        # Validar respuesta
        es_correcta = False
        nota_validacion = ''
        
        if pregunta.tipo_respuesta in ['unica', 'multiple']:
            # Validar contra opciones correctas
            opciones_correctas = set(
                pregunta.opciones.filter(es_correcta=True).values_list('id', flat=True)
            )
            respuestas_usuario = set(map(int, respuesta.split(','))) if respuesta else set()
            es_correcta = respuestas_usuario == opciones_correctas
        
        elif pregunta.tipo_respuesta == 'vf':
            es_correcta = respuesta.lower() in ['verdadero', 'falso']
        
        elif pregunta.tipo_respuesta == 'abierta':
            # La respuesta queda validada y el administrador revisa el contenido.
            es_correcta = True
            nota_validacion = 'La información va a ser validada por el administrador.'
        
        elif pregunta.tipo_respuesta == 'archivo':
            es_correcta = bool(archivo_url)
            if es_correcta:
                tipo_final = tipo_archivo_seleccionado or detectar_tipo_archivo_respuesta(archivo_url)
                nota_validacion = f'Tipo de archivo: {tipo_final}' if tipo_final else 'Archivo validado.'
        
        # Actualizar progreso
        if not es_correcta:
            progreso.intentos_fallidos += 1
            if progreso.intentos_fallidos >= 3:
                es_correcta = True  # Después de 3 intentos, se marca como correcta
        
        progreso.respondida = True
        progreso.es_correcta = es_correcta
        progreso.respuesta_texto = respuesta if pregunta.tipo_respuesta != 'archivo' else ''
        
        # MODIFICACIÓN: guardar prefijo tipo_archivo_seleccionado si existe
        if pregunta.tipo_respuesta == 'archivo':
            if tipo_archivo_seleccionado:
                progreso.archivo_subido_url = f"{tipo_archivo_seleccionado}|||{archivo_url_raw}"
            else:
                progreso.archivo_subido_url = archivo_url_raw
        else:
            progreso.archivo_subido_url = ''
        
        progreso.fecha_respuesta = timezone.now()
        progreso.save()
        
        # Verificar si el quiz está completado
        total_preguntas = quiz.preguntas.count()
        correctas = ProgresoUsuario.objects.filter(
            usuario=progreso.usuario,
            quiz=quiz,
            es_correcta=True
        ).count()
        
        completado = correctas == total_preguntas
        if completado:
            ProgresoUsuario.objects.filter(
                usuario=progreso.usuario,
                quiz=quiz
            ).update(quiz_completado=True)
        
        return JsonResponse({
            'success': True,
            'es_correcta': es_correcta,
            'pista': pregunta.pista if not es_correcta and pregunta.pista else '',
            'explicacion': pregunta.explicacion if not es_correcta else '',
            'nota_validacion': nota_validacion,
            'intentos': progreso.intentos_fallidos,
            'completado': completado,
            'mensaje': 'Respuesta guardada exitosamente'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_requerido
@solo_admin
def gestion_quiz(request, id_curso):
    """Vista para gestionar el quiz de un curso (admin)."""
    curso = get_object_or_404(Curso, id_curso=id_curso)
    quiz = curso.quiz if hasattr(curso, 'quiz') else None

    if quiz:
        total_preguntas = quiz.preguntas.count()
        usuarios = Usuario.objects.filter(
            asignaciones__curso=curso
        ).distinct()

        estadisticas = []
        for usuario in usuarios:
            respondidas = ProgresoUsuario.objects.filter(
                usuario=usuario,
                quiz=quiz,
                respondida=True
            ).count()
            completado = ProgresoUsuario.objects.filter(
                usuario=usuario,
                quiz=quiz,
                es_correcta=True
            ).count() == total_preguntas

            estadisticas.append({
                'usuario': usuario.nombre_completo,
                'usuario_id': usuario.id_usuario,
                'respondidas': respondidas,
                'total': total_preguntas,
                'porcentaje': (respondidas * 100) // total_preguntas if total_preguntas > 0 else 0,
                'completado': completado
            })
    else:
        estadisticas = []

    context = {
        'curso': curso,
        'quiz': quiz,
        'estadisticas': estadisticas
    }

    return render(request, 'contenido/quiz/gestion_quiz.html', context)


@login_requerido
@solo_admin
def ver_respuestas_quiz(request, id_curso, usuario_id):
    """Vista para ver todas las respuestas de un empleado en el quiz."""
    curso = get_object_or_404(Curso, id_curso=id_curso)
    quiz = get_object_or_404(Quiz, curso=curso)
    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
    
    # Obtener todas las respuestas del usuario
    respuestas = ProgresoUsuario.objects.filter(
        usuario=usuario,
        quiz=quiz
    ).select_related('pregunta').order_by('pregunta__orden')
    
    # Calcular estadísticas
    total_preguntas = quiz.preguntas.count()
    respondidas = respuestas.filter(respondida=True).count()
    correctas = respuestas.filter(es_correcta=True).count()
    completado = respuestas.filter(quiz_completado=True).exists()
    
    # Preparar datos de respuestas con análisis de archivos
    respuestas_detalladas = []
    for respuesta in respuestas:
        pregunta = respuesta.pregunta
        datos_respuesta = {
            'pregunta': pregunta,
            'respondida': respuesta.respondida,
            'es_correcta': respuesta.es_correcta,
            'respuesta_texto': respuesta.respuesta_texto,
            'archivo_subido_url': respuesta.archivo_subido_url,
            'intentos_fallidos': respuesta.intentos_fallidos,
            'fecha_respuesta': respuesta.fecha_respuesta,
        }
        
        # Si la pregunta tiene archivo, procesarlo
        if pregunta.tipo_respuesta == 'archivo' and respuesta.archivo_subido_url:
            raw = respuesta.archivo_subido_url
            
            # Separar prefijo de tipo si existe (formato: "imagen_video|||<iframe>")
            if '|||' in raw:
                tipo_seleccionado, iframe_raw = raw.split('|||', 1)
            else:
                tipo_seleccionado, iframe_raw = '', raw

            archivo_datos = preparar_archivo_sharepoint(iframe_raw)
            url_archivo = archivo_datos['url_limpia']
            nombre_archivo = archivo_datos['nombre']

            # El tipo seleccionado por el empleado es la fuente más confiable
            if tipo_seleccionado == 'imagen_video':
                tipo_archivo = 'imagen_video'   # ← iframe de imagen O video de SharePoint
            elif tipo_seleccionado == 'documento':
                tipo_archivo = 'sharepoint'
            else:
                # Registros antiguos sin prefijo: detectar automáticamente
                tipo_archivo = detectar_tipo_archivo_contenido(url_archivo)

            datos_respuesta['archivo_subido_url'] = url_archivo
            datos_respuesta['nombre_archivo'] = nombre_archivo
            datos_respuesta['tipo_archivo'] = tipo_archivo
            datos_respuesta['es_media'] = tipo_archivo == 'imagen_video'
            datos_respuesta['es_sharepoint'] = archivo_datos['es_sharepoint']
            datos_respuesta['url_visualizacion'] = archivo_datos['url_visualizacion']
            datos_respuesta['url_descarga'] = archivo_datos['url_descarga']
        
        # Si la pregunta tiene opciones (multiple choice), obtener los textos
        if pregunta.tipo_respuesta in ['unica', 'multiple'] and respuesta.respuesta_texto:
            ids_opciones = [int(x) for x in respuesta.respuesta_texto.split(',') if x.isdigit()]
            opciones_seleccionadas = pregunta.opciones.filter(id__in=ids_opciones)
            datos_respuesta['opciones_seleccionadas'] = [o.texto for o in opciones_seleccionadas]
        
        respuestas_detalladas.append(datos_respuesta)
    
    context = {
        'curso': curso,
        'quiz': quiz,
        'usuario': usuario,
        'respuestas': respuestas_detalladas,
        'total': total_preguntas,
        'respondidas': respondidas,
        'correctas': correctas,
        'porcentaje': (correctas * 100) // total_preguntas if total_preguntas > 0 else 0,
        'completado': completado
    }
    
    return render(request, 'contenido/quiz/ver_respuestas_quiz.html', context)

@login_requerido
@solo_empleado
def listar_cursos_empleado(request):
    """Vista para que el empleado vea los cursos disponibles."""
    cursos = Curso.objects.prefetch_related('contenidos').all().order_by('titulo')
    usuario_id = request.session.get('id_usuario')
    
    # Obtener estado del quiz para cada curso
    cursos_data = []
    for curso in cursos:
        quiz = Quiz.objects.filter(curso=curso).first()
        progreso = None
        estado_quiz = 'sin_iniciar'
        porcentaje = 0
        
        if quiz:
            respondidas = ProgresoUsuario.objects.filter(
                usuario_id=usuario_id,
                quiz=quiz,
                respondida=True
            ).count()

            # Contar preguntas respondidas correctamente
            correctas = ProgresoUsuario.objects.filter(
                usuario_id=usuario_id,
                quiz=quiz,
                es_correcta=True
            ).count()
            
            # Verificar si está completado
            completado = ProgresoUsuario.objects.filter(
                usuario_id=usuario_id,
                quiz=quiz,
                quiz_completado=True
            ).exists()
            
            total = quiz.preguntas.count()
            porcentaje = (respondidas * 100) // total if total > 0 else 0
            
            if completado:
                estado_quiz = 'completado'
            elif respondidas > 0:
                estado_quiz = 'en_progreso'
            else:
                estado_quiz = 'sin_iniciar'
        
        cursos_data.append({
            'curso': curso,
            'quiz': quiz,
            'estado_quiz': estado_quiz,
            'porcentaje': porcentaje,
            'quiz_completado': completado if quiz else False
        })
    
    context = {
        'cursos_data': cursos_data,
        'nombre': request.session.get('nombre')
    }
    
    return render(request, 'contenido/cursos/ver_cursos_empleado.html', context)


@login_requerido
@solo_empleado
def ver_curso_empleado(request, id_curso):
    """Vista para que el empleado vea el contenido de un curso específico."""
    curso = get_object_or_404(Curso, id_curso=id_curso)
    usuario_id = request.session.get('id_usuario')
    
    # Obtener bloques de contenido (principal y lateral)
    bloques_principal = BloqueContenido.objects.filter(
        curso=curso, 
        seccion='principal'
    ).order_by('orden')
    
    bloques_lateral = BloqueContenido.objects.filter(
        curso=curso, 
        seccion='lateral'
    ).order_by('orden')
    
    # Obtener estado del quiz
    quiz = Quiz.objects.filter(curso=curso).first()
    quiz_data = None
    
    if quiz:
        total_preguntas = quiz.preguntas.count()
        correctas = ProgresoUsuario.objects.filter(
            usuario_id=usuario_id,
            quiz=quiz,
            es_correcta=True
        ).count()
        respondidas = ProgresoUsuario.objects.filter(
            usuario_id=usuario_id,
            quiz=quiz,
            respondida=True
        ).count()
        completado = ProgresoUsuario.objects.filter(
            usuario_id=usuario_id,
            quiz=quiz,
            quiz_completado=True
        ).exists()
        
        quiz_data = {
            'quiz': quiz,
            'titulo': quiz.titulo,
            'descripcion': quiz.descripcion,
            'preguntas': quiz.preguntas.all().order_by('orden'),
            'total': total_preguntas,
            'respondidas': respondidas,
            'correctas': correctas,
            'porcentaje': (respondidas * 100) // total_preguntas if total_preguntas > 0 else 0,
            'completado': completado
        }
    
    # Verificar si el usuario es admin (acceso a edición)
    es_admin = request.session.get('rol') == 'admin' or request.session.get('es_admin', False)

    # Verificar si el empleado está asignado a este curso
    tiene_acceso_quiz = AsignacionCurso.objects.filter(
        curso=curso,
        usuario_id=usuario_id
    ).exists()
    
    context = {
        'curso': curso,
        'bloques_principal': bloques_principal,
        'bloques_lateral': bloques_lateral,
        'quiz_data': quiz_data,
        'nombre': request.session.get('nombre'),
        'is_admin': es_admin,
        'readonly': not es_admin,
        'tiene_acceso_quiz': tiene_acceso_quiz,
    }
    
    return render(request, 'contenido/cursos/ver_curso_contenido_empleado.html', context)


# =========================================================
# COMO SUBIR UN ARCHIVO
# =========================================================


@login_requerido
def subir_archivo(request, from_admin=False):
    id_curso = (request.GET.get('id_curso') or '').strip()
    volver_quiz_url = None

    if id_curso:
        volver_quiz_url = reverse('resolver_quiz', kwargs={'id_curso': id_curso})
    else:
        referer = request.META.get('HTTP_REFERER', '')
        if '/empleado/quiz/' in referer:
            volver_quiz_url = referer

    # Determinación correcta del rol usando la sesión
    es_admin = request.session.get('rol') == '1'   # '1' = Administrador

    return render(request, "contenido/subir_archivo.html", {
        'volver_quiz_url': volver_quiz_url,
        'es_admin': es_admin,          # nueva variable
    })
# =========================================================
# VIEW DE REPORTE DE CURSOS PARA LLEVAR CONTROL DE LOS CURSOS REALIZADOS POR MESES
# =========================================================

@login_requerido
@solo_admin
def cursos_estadisticas(request):
    hoy = date.today()
    datos, meta = get_cursos_stats()  # sin filtro de mes, muestra acumulado

    opciones_meses = _opciones_ultimos_meses(hoy)

    context = {
        'datos': datos,
        'meta': meta,
        'opciones_meses': opciones_meses,
    }
    return render(request, 'contenido/reporte/estadisticas.html', context)

@login_requerido
@solo_admin
def descargar_excel_estadisticas(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    cursos_ids = request.POST.getlist('cursos')
    if not cursos_ids:
        return HttpResponse("No se seleccionaron cursos.", status=400)

    hoy = date.today()

    # Valores por defecto seguros ANTES del try
    fecha_inicio = date(hoy.year, hoy.month, 1)
    fecha_fin    = hoy

    try:
        tipo_periodo = request.POST.get('tipo_periodo', '6m')

        if tipo_periodo == '6m':
            year  = int(request.POST.get('year_6m',  hoy.year))
            month = int(request.POST.get('month_6m', hoy.month))
            if not (1 <= month <= 12):
                raise ValueError("Mes fuera de rango")

            mes_esp = request.POST.get('mes_especifico', '').strip()

            if mes_esp:
                m = int(mes_esp)
                if not (1 <= m <= 12):
                    raise ValueError("Mes específico fuera de rango")
                # Si el mes puntual es posterior al mes final, pertenece al año anterior
                y = year if m <= month else year - 1
                fecha_inicio = date(y, m, 1)
                fecha_fin    = date(y, m, calendar.monthrange(y, m)[1])
            else:
                fecha_fin = date(year, month, calendar.monthrange(year, month)[1])
                m0 = month - 5
                y0 = year
                if m0 <= 0:
                    m0 += 12
                    y0 -= 1
                fecha_inicio = date(y0, m0, 1)

        elif tipo_periodo == 'year':
            year         = int(request.POST.get('year_full', hoy.year))
            fecha_inicio = date(year, 1,  1)
            fecha_fin    = date(year, 12, 31)

        elif tipo_periodo == 'custom':
            fecha_inicio = date.fromisoformat(request.POST.get('fecha_inicio', ''))
            fecha_fin    = date.fromisoformat(request.POST.get('fecha_fin',    ''))
            if fecha_inicio > fecha_fin:
                fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

        # tipo_periodo desconocido → se usan los valores por defecto definidos arriba

    except (ValueError, TypeError):
        # Fechas por defecto ya asignadas antes del try
        pass

    output = generar_excel(cursos_ids, fecha_inicio, fecha_fin)

    nombre   = f"cursos_{fecha_inicio.isoformat()}_{fecha_fin.isoformat()}.xlsx"
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return response


# Helper
def _opciones_ultimos_meses(hoy, n=12):
    y, m = hoy.year, hoy.month
    opts = []
    for _ in range(n):
        opts.append({
            'value': f"{y}-{m:02d}",
            'label': f"{MESES_ES[m-1]} {y}"   # ← español
        })
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    return opts