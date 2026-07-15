from django.urls import path
from .views import *

urlpatterns = [
    
    # Rutas de contenido PANEL ADMINISTRADOR Y EMPLEADO
    path('admin-panel/', panel_admin, name='panel_admin'),
    path('empleado-panel/', panel_empleado, name='panel_empleado'),
    
    # Rutas de contenido NOTICIAS ADMINISTRADOR
    path('admin/noticias/',administrar_noticias,name='administrar_noticias'),
    path('admin/noticias/<str:id_noticia>/',administrar_noticias,name='editar_noticia'),
    path('noticias/eliminar/<str:id_noticia>/', eliminar_noticia, name='eliminar_noticia'),
    
    # Rutas de contenido NOTICIAS EMPLEADO
    path('empleado/noticias/',ver_noticias,name='ver_noticias'),
    
    # Rutas de contenido CURSOS
    path('cursos/',gestionar_cursos,name='gestionar_cursos'),
    path('curso/eliminar/<str:id_curso>/',eliminar_curso,name='eliminar_curso'),
    path('curso/editar/<str:id_curso>/',editar_curso,name='editar_curso'),
    
    # Rutas de contenido BLOQUES DE CONTENIDO
    path('curso/<str:id_curso>/contenido/',agregar_contenido,name='agregar_contenido'),
    
    # API endpoints para manejar bloques de contenido vía AJAX
    path('api/curso/<str:id_curso>/bloque/guardar/',guardar_bloque_contenido,name='guardar_bloque_contenido'),
    path('api/bloque/<int:id_bloque>/editar/',editar_bloque_contenido,name='editar_bloque_contenido'),
    path('api/curso/<str:id_curso>/render-type/',actualizar_render_type,name='actualizar_render_type'),
    path('api/bloque/<int:id_bloque>/eliminar/',eliminar_bloque,name='eliminar_bloque'),
    path('api/contenido/<int:id>/eliminar/', eliminar_contenido_ajax, name='eliminar_contenido_ajax'),

    # RUTAS DE QUIZ
    path('admin/quiz/<str:id_curso>/', crear_quiz, name='crear_quiz'),
    path('admin/quiz/pregunta/agregar/<int:quiz_id>/', agregar_pregunta, name='agregar_pregunta'),
    path('admin/quiz/pregunta/guardar/<str:id_curso>/', guardar_pregunta_quiz, name='guardar_pregunta_quiz'),
    path('admin/quiz/pregunta/eliminar/<int:pregunta_id>/', eliminar_pregunta, name='eliminar_pregunta'),
    path('admin/quiz/gestion/<str:id_curso>/', gestion_quiz, name='gestion_quiz'),
    path('admin/quiz/respuestas/<str:id_curso>/<str:usuario_id>/', ver_respuestas_quiz, name='ver_respuestas_quiz'),
    
    path('empleado/quiz/<str:id_curso>/', resolver_quiz, name='resolver_quiz'),
    path('api/quiz/responder/', responder_pregunta, name='responder_pregunta'),
    
    # RUTAS DE CURSOS EMPLEADO
    path('empleado/cursos/', listar_cursos_empleado, name='listar_cursos_empleado'),
    path('empleado/curso/<str:id_curso>/', ver_curso_empleado, name='ver_curso_empleado'),

    # RUTAS DE SUBIR ARCHIVO

    
    # RUTAS DE SUBIR ARCHIVO
    path('estadisticas/', cursos_estadisticas, name='estadisticas_cursos'),
    path('estadisticas/descargar/', descargar_excel_estadisticas, name='descargar_excel'),

    # ELIMINAR QUIZ
    path('curso/<int:id_curso>/eliminar-quiz/', eliminar_quiz, name='eliminar_quiz'),

]
