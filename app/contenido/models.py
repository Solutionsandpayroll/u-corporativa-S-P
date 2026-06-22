from django.db import models
from inicio_sesion.models import Usuario
from django.utils import timezone
import re

# =========================================================
# NOTICIAS
# =========================================================

class Noticia(models.Model):

    id_noticia = models.CharField(
        max_length=20,
        primary_key=True
    )

    fecha_public = models.DateField(
        auto_now_add=True
    )

    titulo = models.CharField(
        max_length=100
    )

    descripcion = models.TextField(blank=True)

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='noticias'
    )

    def __str__(self):
        return self.titulo

    class Meta:
        db_table = 'noticia'


# =========================================================
# CURSOS
# =========================================================

class Curso(models.Model):
    """Modelo principal para cursos."""
    id_curso = models.CharField(max_length=20, primary_key=True)
    fecha_public = models.DateField(auto_now_add=True)
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    estado = models.CharField(max_length=50, default='activo')

    class Meta:
        db_table = 'curso'
        ordering = ['-fecha_public']

    def __str__(self):
        return self.titulo


# =========================================================
# CREAR MODELO UNIFICADO PARA BLOQUES DE CONTENIDO DINÁMICO
# =========================================================

class BloqueContenido(models.Model):
    """
    Modelo unificado para gestionar contenido dinámico de cursos.
    Soporta tanto la Card Principal como la Columna Lateral.
    """
    SECCION_CHOICES = [
        ('principal', 'Card Principal - Izquierda'),
        ('lateral', 'Columna Lateral - Derecha'),
    ]

    TIPO_CHOICES = [
        ('banner', 'Banner Grande(Contenido Principal)'),
        ('informativa', 'Card Informativa'),
        ('archivos', 'Archivos'),
        ('archivo_categorizado', 'Archivos Categorizados (IMG/VIDEO vs Documentos)'),
        ('enlace', 'Enlace Web'),
    ]

    RENDER_CHOICES = [
        ('imagen_debajo', 'Imagen Debajo de Descripción'),
        ('imagen_fondo', 'Imagen como Fondo de Card'),
    ]

    curso = models.ForeignKey(
        'Curso',
        on_delete=models.CASCADE,
        related_name='bloques_contenido'
    )
    
    seccion = models.CharField(
        max_length=20,
        choices=SECCION_CHOICES,
        default='principal'
    )
    
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_CHOICES,
        default='informativa'
    )
    
    render_type = models.CharField(
        max_length=20,
        choices=RENDER_CHOICES,
        default='imagen_debajo',
        blank=True,
        null=True,
        help_text="Solo aplica para la sección principal"
    )
    
    titulo = models.CharField(max_length=200, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    url_recurso = models.TextField(blank=True, null=True)
    url_thumbnail = models.TextField(blank=True, null=True)
    
    orden = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'bloque_contenido'
        ordering = ['seccion', 'fecha_creacion']  # ← CAMBIADO: ordenar por fecha de creación
        verbose_name = 'Bloque de Contenido'
        verbose_name_plural = 'Bloques de Contenido'

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.curso.titulo} [{self.get_seccion_display()}]"

    @property
    def url_recurso_limpia(self):
        """Devuelve la URL limpia del recurso, extrayendo el src si es un iframe."""
        url = self.url_recurso or ''
        if not url:
            return ''
        if url.startswith('http://') or url.startswith('https://'):
            return url.strip()
        match = re.search(r'src="([^"]+)"', url)
        if match:
            return match.group(1).strip()
        return url.strip()

    @property
    def unique_id(self):
        """Extrae el UniqueId de la URL del recurso."""
        url = self.url_recurso_limpia
        if not url:
            return None
        m = re.search(r'UniqueId=([0-9a-fA-F\-]{36})', url)
        if m:
            return m.group(1)
        m = re.search(r'sourcedoc=\{([0-9a-fA-F\-]{36})\}', url)
        if m:
            return m.group(1)
        return None

    @property
    def sharepoint_base(self):
        """Extrae la base del sitio de SharePoint."""
        url = self.url_recurso_limpia
        if not url:
            return ''
        m = re.search(r'(https?://[^/]+/[^/]+/[^/]+)', url)
        return m.group(1) if m else ''

    @property
    def es_sharepoint(self):
        """Determina si la URL es de SharePoint/OneDrive."""
        url = (self.url_recurso_limpia).lower()
        return any(x in url for x in ['sharepoint.com', 'onedrive.com', 'embed.aspx', 'doc.aspx'])

    @property
    def url_visualizacion(self):
        """URL para abrir el archivo en Office Online."""
        if not self.es_sharepoint:
            return self.url_recurso_limpia
        uid = self.unique_id
        base = self.sharepoint_base
        if not uid or not base:
            return self.url_recurso_limpia
        return f"{base}/_layouts/15/Doc.aspx?sourcedoc=%7B{uid}%7D&action=default"

    @property
    def url_embed(self):
        """URL para incrustar en iframe (embed.aspx)."""
        if not self.es_sharepoint:
            return self.url_recurso_limpia
        uid = self.unique_id
        base = self.sharepoint_base
        if not uid or not base:
            return self.url_recurso_limpia
        return f"{base}/_layouts/15/embed.aspx?UniqueId={uid}"

# =========================================================
# QUIZ MODELS
# =========================================================

class ArchivoPregunta(models.Model):
    """Modelo para archivos adjuntos a preguntas."""
    nombre = models.CharField(max_length=255)
    url_original = models.TextField()
    url_visualizacion = models.TextField(blank=True)
    url_descarga = models.TextField(blank=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'archivo_pregunta'


class Quiz(models.Model):
    """Modelo para los quiz de los cursos."""
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    curso = models.OneToOneField(
        'Curso',
        on_delete=models.CASCADE,
        related_name='quiz'
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.titulo} - {self.curso.titulo}"
    
    class Meta:
        db_table = 'quiz'
    
    def get_progreso_usuario(self, usuario):
        """Obtiene el progreso del usuario en este quiz."""
        total_preguntas = self.preguntas.count()
        respondidas = ProgresoUsuario.objects.filter(
            quiz=self,
            usuario=usuario,
            respondida=True
        ).count()
        completado = ProgresoUsuario.objects.filter(
            quiz=self,
            usuario=usuario,
            es_correcta=True
        ).count() == total_preguntas
        
        return {
            'total': total_preguntas,
            'respondidas': respondidas,
            'porcentaje': (respondidas * 100) // total_preguntas if total_preguntas > 0 else 0,
            'completado': completado
        }


class Pregunta(models.Model):
    """Modelo para preguntas del quiz."""
    TIPO_CHOICES = [
        ('unica', 'Opción Única'),
        ('multiple', 'Opción Múltiple'),
        ('vf', 'Verdadero / Falso'),
        ('abierta', 'Respuesta Abierta'),
        ('archivo', 'Subir Archivo'),
    ]
    
    quiz = models.ForeignKey(
        'Quiz',
        on_delete=models.CASCADE,
        related_name='preguntas'
    )
    texto = models.TextField()
    descripcion = models.TextField(blank=True, null=True)
    imagen_url = models.TextField(blank=True, null=True, help_text='URL de imagen de apoyo')
    tipo_respuesta = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='unica'
    )
    pista = models.TextField(blank=True, null=True)
    explicacion = models.TextField(blank=True, null=True, help_text='Se muestra al fallar')
    orden = models.PositiveIntegerField(default=0)
    archivo_apoyo = models.ForeignKey(
        'ArchivoPregunta',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    contenido_relacionado = models.ForeignKey(
        'BloqueContenido',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    
    def __str__(self):
        return f"{self.quiz.titulo} - {self.texto[:50]}"
    
    class Meta:
        db_table = 'pregunta'
        ordering = ['orden']


class OpcionRespuesta(models.Model):
    """Modelo para opciones de respuesta."""
    pregunta = models.ForeignKey(
        'Pregunta',
        on_delete=models.CASCADE,
        related_name='opciones'
    )
    texto = models.CharField(max_length=500)
    es_correcta = models.BooleanField(default=False)
    
    def __str__(self):
        return self.texto
    
    class Meta:
        db_table = 'opcion_respuesta'


class ProgresoUsuario(models.Model):
    """Modelo para rastrear el progreso del usuario en el quiz."""
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE
    )
    quiz = models.ForeignKey(
        'Quiz',
        on_delete=models.CASCADE
    )
    pregunta = models.ForeignKey(
        'Pregunta',
        on_delete=models.CASCADE
    )
    respondida = models.BooleanField(default=False)
    es_correcta = models.BooleanField(default=False)
    respuesta_texto = models.TextField(blank=True, null=True)
    archivo_subido_url = models.TextField(blank=True, null=True)
    intentos_fallidos = models.PositiveIntegerField(default=0)
    fecha_respuesta = models.DateTimeField(blank=True, null=True)
    quiz_completado = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.usuario.nombre} - {self.pregunta.texto[:30]}"
    
    class Meta:
        db_table = 'progreso_usuario'
        unique_together = ('usuario', 'quiz', 'pregunta')


# =========================================================
# CONTENIDOS
# =========================================================

class Contenido(models.Model):
    """
    Modelo para archivos/recursos adjuntos.
    Se vincula a BloqueContenido (para dashboard), Curso o Noticia.
    """
    id_contenido = models.AutoField(primary_key=True)
    fecha_public = models.DateTimeField(auto_now_add=True)

    TIPO_CHOICES = [
        ('video', 'Video'),
        ('imagen', 'Imagen'),
    ]

    tipo_con = models.CharField(max_length=50, choices=TIPO_CHOICES, default='otro')
    url_recurso = models.TextField()
    
    # ← NUEVO CAMPO: nombre del archivo
    nombre_archivo = models.CharField(max_length=300, blank=True, null=True)
    
    bloque = models.ForeignKey(
        'BloqueContenido',
        on_delete=models.CASCADE,
        related_name='contenidos',
        blank=True,
        null=True
    )

    curso = models.ForeignKey(
        'Curso',
        on_delete=models.CASCADE,
        related_name='contenidos',
        blank=True,
        null=True
    )

    noticia = models.ForeignKey(
        'Noticia',
        on_delete=models.CASCADE,
        related_name='contenidos',
        blank=True,
        null=True
    )

    @property
    def unique_id(self):
        url = self.url_recurso or ''
        m = re.search(r'UniqueId=([0-9a-fA-F\-]{36})', url)
        if m:
            return m.group(1)
        m = re.search(r'sourcedoc=\{([0-9a-fA-F\-]{36})\}', url)
        if m:
            return m.group(1)
        return None

    @property
    def sharepoint_base(self):
        url = self.url_recurso or ''
        m = re.search(r'(https?://[^/]+/[^/]+/[^/]+)', url)
        return m.group(1) if m else ''

    @property
    def es_sharepoint(self):
        url = (self.url_recurso or '').lower()
        return any(x in url for x in ['sharepoint.com', 'onedrive.com', 'embed.aspx', 'doc.aspx'])

    @property
    def url_visualizacion(self):
        if not self.es_sharepoint:
            return self.url_recurso
        uid = self.unique_id
        base = self.sharepoint_base
        if not uid or not base:
            return self.url_recurso
        return f"{base}/_layouts/15/Doc.aspx?sourcedoc=%7B{uid}%7D&action=default"

    @property
    def url_descarga(self):
        if not self.es_sharepoint:
            return self.url_recurso
        uid = self.unique_id
        base = self.sharepoint_base
        if not uid or not base:
            return self.url_recurso
        return f"{base}/_layouts/15/download.aspx?UniqueId={uid}"

    # ← NUEVO MÉTODO: obtener nombre para mostrar
    def get_nombre_display(self):
        """Devuelve el nombre del archivo para mostrar."""
        if self.nombre_archivo and self.nombre_archivo.strip():
            return self.nombre_archivo
        # Si no hay nombre, extraer de la URL
        url = self.url_recurso or ''
        # Intentar extraer título del iframe
        match = re.search(r'title="([^"]+)"', url)
        if match:
            return match.group(1)
        # Usar última parte de la URL
        return url.split('/')[-1] if url else 'Archivo'

    def __str__(self):
        if self.bloque:
            return f"{self.get_tipo_con_display()} - Bloque #{self.bloque.id}"
        if self.curso:
            return f"{self.tipo_con} - {self.curso.titulo}"
        if self.noticia:
            return f"{self.tipo_con} - {self.noticia.titulo}"
        return self.tipo_con

    class Meta:
        db_table = 'contenido'
        ordering = ['-fecha_public']
        verbose_name = 'Contenido'
        verbose_name_plural = 'Contenidos'

    @property
    def icono(self):
        """Devuelve la clase Font Awesome según el tipo de archivo."""
        iconos = {
            'video': 'fa-file-video',
            'imagen': 'fa-file-image',
            'pdf': 'fa-file-pdf',
            'word': 'fa-file-word',
            'excel': 'fa-file-excel',
            'powerpoint': 'fa-file-powerpoint',
            'sharepoint': 'fa-cloud-arrow-up',  # Ícono de subida a la nube
            'url': 'fa-link',
            'otro': 'fa-file',
        }
        return iconos.get(self.tipo_con, 'fa-file')
    
    def get_tipo_categoria(self):
        """
        Categoriza el archivo en:
        - 'media': para imágenes y videos (se abren en nueva pestaña directamente)
        - 'documento': para PDF, Word, Excel, PowerPoint, etc (se abren con Office Online)
        - 'otro': para tipos desconocidos
        """
        if self.tipo_con in ['imagen', 'video']:
            return 'media'
        elif self.tipo_con in ['pdf', 'word', 'excel', 'powerpoint', 'sharepoint']:
            return 'documento'
        else:
            return 'otro'
    
    def detectar_tipo(self):
        url = (self.url_recurso or '').lower()
        if 'sharepoint.com' in url or 'onedrive.com' in url or 'embed.aspx' in url:
            return 'sharepoint'
        if url.endswith('.pdf'):
            return 'pdf'
        if url.endswith(('.doc', '.docx')):
            return 'word'
        if url.endswith(('.xls', '.xlsx')):
            return 'excel'
        if url.endswith(('.ppt', '.pptx')):
            return 'powerpoint'
        if url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')):
            return 'imagen'
        if url.endswith(('.mp4', '.webm', '.mov', '.avi')):
            return 'video'
        return 'url'

    def save(self, *args, **kwargs):
        if not self.tipo_con or self.tipo_con == 'otro':
            self.tipo_con = self.detectar_tipo()
        super().save(*args, **kwargs)