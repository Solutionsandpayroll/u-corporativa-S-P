# Como ejecutar el proyecto

## Introducción breve
Este proyecto es una aplicación web Django para gestionar inicio de sesión, usuarios, contenidos, cursos, noticias, archivos, estadísticas y quizzes. Está organizada en dos apps principales: inicio_sesion y contenido.

## Funcionamiento
1. El usuario entra por la pantalla de login y la solicitud llega a login_view en inicio_sesion/views.py.
2. Si las credenciales son correctas, se crea la sesión y el sistema redirige al panel correspondiente según el rol.
3. Las peticiones del panel de administración y del panel de empleado se atienden en la app contenido.
4. La lógica de negocio se concentra en las vistas y en funciones reutilizables de contenido/utils.py.
5. La recuperación de contraseña envía correos con Microsoft Graph desde app/inicio_sesion/graph.py.
6. La respuesta puede ser una página HTML renderizada con templates o una respuesta JSON en las rutas AJAX y API internas.

## Estructura tecnica
| Archivo o carpeta | Rol |
| --- | --- |
| app/manage.py | Punto de entrada para comandos de Django. |
| app/app/settings.py | Configuración del proyecto, base de datos, static, templates y apps instaladas. |
| app/app/urls.py | Enrutamiento principal del proyecto. |
| app/inicio_sesion/views.py | Login, logout, gestión de usuarios y recuperación de contraseña. |
| app/inicio_sesion/graph.py | Configuración de Microsoft Graph para envío de correos de recuperación. |
| app/inicio_sesion/urls.py | Rutas de autenticación y administración de usuarios. |
| app/contenido/views.py | Paneles, noticias, cursos, bloques de contenido, quizzes, archivos y estadísticas. |
| app/contenido/urls.py | Rutas principales de contenido y API internas. |
| app/contenido/utils.py | Lógica reutilizable separada por funciones. |
| app/templates/ | Plantillas HTML de la aplicación. |
| app/static/ | Archivos estáticos como CSS, JS e imágenes. |
| requirements.txt | Dependencias Python del proyecto. |
| build_files.sh | Script de instalación y preparación para despliegue. |
| vercel.json | Configuración de despliegue en Vercel. |

Si el proyecto es Django, la relación principal es la siguiente:
- urls.py: enrutamiento.
- views.py: endpoints y control de peticiones.
- utils.py: lógica reutilizable separada por funciones.
- manage.py: punto de entrada para comandos.

## Endpoints principales
| Ruta | Función | Propósito |
| --- | --- | --- |
| / | login_view | Inicio de sesión. |
| /logout/ | logout_view | Cerrar sesión. |
| /usuarios/ | gestionar_usuarios | Crear, editar, listar y eliminar usuarios. |
| /cambiar-password-inicial/ | cambiar_password_inicial | Actualizar contraseña y correo desde el panel. |
| /recuperar-password/ | solicitar_recuperacion | Iniciar recuperación de contraseña. |
| /validar-codigo/ | validar_codigo | Validar el código de recuperación. |
| /reenviar-codigo/ | reenviar_codigo | Solicitar un nuevo código de recuperación. |
| /cambiar-password/ | cambiar_password | Finalizar el cambio de contraseña. |
| /contenido/admin-panel/ | panel_admin | Panel principal del administrador. |
| /contenido/empleado-panel/ | panel_empleado | Panel principal del empleado. |
| /contenido/admin/noticias/ | administrar_noticias | Crear, editar y listar noticias. |
| /contenido/noticias/eliminar/<str:id_noticia>/ | eliminar_noticia | Eliminar una noticia. |
| /contenido/empleado/noticias/ | ver_noticias | Ver noticias desde el panel de empleado. |
| /contenido/cursos/ | gestionar_cursos | Crear y listar cursos. |
| /contenido/curso/editar/<str:id_curso>/ | editar_curso | Editar un curso. |
| /contenido/curso/eliminar/<str:id_curso>/ | eliminar_curso | Eliminar un curso. |
| /contenido/curso/<str:id_curso>/contenido/ | agregar_contenido | Administrar bloques de contenido del curso. |
| /contenido/api/curso/<str:id_curso>/bloque/guardar/ | guardar_bloque_contenido | Guardar bloques de contenido por AJAX. |
| /contenido/api/bloque/<int:id_bloque>/editar/ | editar_bloque_contenido | Editar un bloque de contenido por API. |
| /contenido/api/bloque/<int:id_bloque>/eliminar/ | eliminar_bloque | Eliminar un bloque de contenido por API. |
| /contenido/admin/quiz/<str:id_curso>/ | crear_quiz | Crear el quiz de un curso. |
| /contenido/admin/quiz/gestion/<str:id_curso>/ | gestion_quiz | Administrar el quiz del curso. |
| /contenido/empleado/quiz/<str:id_curso>/ | resolver_quiz | Resolver el quiz como empleado. |
| /contenido/api/quiz/responder/ | responder_pregunta | Registrar respuestas del quiz vía AJAX. |
| /contenido/empleado/cursos/ | listar_cursos_empleado | Listar cursos asignados al empleado. |
| /contenido/empleado/curso/<str:id_curso>/ | ver_curso_empleado | Ver el detalle de un curso. |
| /contenido/subir-archivo/ | subir_archivo | Subir o registrar archivos. |
| /contenido/estadisticas/ | cursos_estadisticas | Ver estadísticas de cursos. |
| /contenido/estadisticas/descargar/ | descargar_excel_estadisticas | Descargar estadísticas en Excel. |

## Requisitos
- Python recomendado: 3.12.x.
- Entorno virtual: recomendado.
- Dependencias: requirements.txt.
- Base de datos: la configuración usa DATABASE_URL mediante dj-database-url.
- Correo: la recuperación de contraseña usa Microsoft Graph configurado en app/inicio_sesion/graph.py.

Nota: el archivo app/db.sqlite3 existe en el proyecto, pero la configuración activa no apunta directamente a SQLite; espera la variable DATABASE_URL.

## Estructura recomendada de ejecucion
1. Abrir PowerShell y ubicarse en la raíz del proyecto.

```powershell
cd C:\u_corporativa_V4
```

2. Crear el entorno virtual si no existe.

```powershell
python -m venv env
```

3. Activar el entorno virtual.

```powershell
. .\env\Scripts\Activate.ps1
```

4. Instalar las dependencias.

```powershell
pip install -r requirements.txt
```

5. Definir las variables de entorno necesarias para Django.

```powershell
$env:SECRET_KEY = "tu_clave_secreta"
$env:DATABASE_URL = "sqlite:///db.sqlite3"
$env:GRAPH_TENANT_ID = "tu_tenant_id"
$env:GRAPH_CLIENT_ID = "tu_client_id"
$env:GRAPH_CLIENT_SECRET = "tu_client_secret"
```

Si usas otra base de datos, reemplaza DATABASE_URL por la cadena correspondiente.

6. Entrar al directorio donde está manage.py.

```powershell
cd .\app
```

7. Preparar la base de datos.

```powershell
python manage.py makemigrations
python manage.py migrate
```

8. Recopilar archivos estáticos si vas a correr el proyecto con la misma configuración de despliegue.

```powershell
python manage.py collectstatic --noinput
```

9. Ejecutar el servidor local.

```powershell
python manage.py runserver
```

10. Abrir la aplicación en el navegador.

```text
http://127.0.0.1:8000/
```

## Opcion con script
El archivo build_files.sh instala dependencias, ejecuta collectstatic y luego aplica makemigrations y migrate. Está pensado como paso de preparación para despliegue y usa comandos de Bash, por lo que no es el flujo normal en PowerShell de Windows.

## Notas
- La base de datos se configura con DATABASE_URL y dj-database-url.
- Las plantillas HTML están en la carpeta app/templates.
- Los archivos estáticos están en la carpeta app/static.
- WhiteNoise está configurado para servir estáticos.
- El proyecto usa sesiones para controlar el acceso por rol.
- El archivo app/inicio_sesion/graph.py centraliza la configuración de Microsoft Graph para enviar correos desde noreply@solutionsandpayroll.com.
- vercel.json apunta al WSGI del proyecto en app/app/wsgi.py.