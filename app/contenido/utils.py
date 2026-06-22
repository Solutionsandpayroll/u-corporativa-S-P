import re, calendar, io
from django.utils import timezone
from django.db.models import Count, Q
from datetime import date
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from .models import *



def limpiar_iframe(url_iframe):
    """
    Extrae la URL limpia de un iframe de SharePoint.
    Si es un iframe, extrae el src. Si es una URL, la retorna como está.
    """
    if not url_iframe:
        return ''

    # Buscar src en iframe — soporta comillas dobles y simples
    match = re.search(r'src=["\'](.*?)["\']', url_iframe, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Si no es iframe, retornar como URL
    return url_iframe.strip()

def extraer_titulo_iframe(url_iframe):
    """Extrae el valor del atributo title desde un iframe HTML."""
    if not url_iframe:
        return ''

    match = re.search(r'title\s*=\s*["\']([^"\']+)["\']', url_iframe, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return ''


def extraer_unique_id_sharepoint(url_iframe):
    """Extrae el UniqueId de un enlace o iframe de SharePoint/OneDrive."""
    if not url_iframe:
        return ''

    url_limpia = limpiar_iframe(url_iframe)
    patrones = [
        r'UniqueId=([0-9a-fA-F\-]{36})',
        r'sourcedoc=%7B([0-9a-fA-F\-]{36})%7D',
        r'sourcedoc=\{([0-9a-fA-F\-]{36})\}',
    ]

    for patron in patrones:
        match = re.search(patron, url_limpia, re.IGNORECASE)
        if match:
            return match.group(1)

    return ''


def extraer_base_sharepoint(url_iframe):
    """
    Extrae la base del sitio de SharePoint.
    Busca /personal/USUARIO o /sites/SITIO en cualquier posición de la URL,
    para cubrir formatos como /:w:/r/personal/... además del directo /personal/...
    """
    if not url_iframe:
        return ''

    url_limpia = limpiar_iframe(url_iframe)

    # /personal/USUARIO en cualquier posición
    match = re.search(
        r'(https?://[^/]+)/(?:[^/]+/)*personal/([^/\?#&]+)',
        url_limpia, re.IGNORECASE
    )
    if match:
        return f"{match.group(1)}/personal/{match.group(2)}"

    # /sites/SITIO en cualquier posición
    match = re.search(
        r'(https?://[^/]+)/(?:[^/]+/)*sites/([^/\?#&]+)',
        url_limpia, re.IGNORECASE
    )
    if match:
        return f"{match.group(1)}/sites/{match.group(2)}"

    # Fallback: primeros 3 segmentos (comportamiento anterior)
    match = re.search(r'(https?://[^/]+/[^/]+/[^/\?#&]+)', url_limpia)
    return match.group(1) if match else ''


def preparar_archivo_sharepoint(url_iframe):
    """Normaliza enlaces de archivo y construye URLs de visualización y descarga."""
    url_original = (url_iframe or '').strip()
    url_limpia = limpiar_iframe(url_original)
    titulo = extraer_titulo_iframe(url_original)
    nombre = titulo or extraer_nombre_archivo(url_original)
    unique_id = extraer_unique_id_sharepoint(url_original)
    base = extraer_base_sharepoint(url_original)
    es_sharepoint = any(x in url_limpia.lower() for x in ['sharepoint.com', 'onedrive.com', 'embed.aspx', 'doc.aspx'])

    if unique_id and base:
        url_visualizacion = f"{base}/_layouts/15/Doc.aspx?sourcedoc=%7B{unique_id}%7D&action=default"
        url_descarga = f"{base}/_layouts/15/download.aspx?UniqueId={unique_id}"
    else:
        url_visualizacion = url_limpia
        url_descarga = url_limpia

    return {
        'url_original': url_original,
        'url_limpia': url_limpia,
        'nombre': nombre,
        'unique_id': unique_id,
        'base': base,
        'es_sharepoint': es_sharepoint,
        'url_visualizacion': url_visualizacion,
        'url_descarga': url_descarga,
    }


def extraer_nombre_archivo(url_iframe):
    """
    Extrae el nombre del archivo del iframe de SharePoint.
    Busca el atributo 'title' en el iframe.
    """
    if not url_iframe:
        return 'Archivo'

    titulo = extraer_titulo_iframe(url_iframe)
    if titulo:
        return titulo

    url_limpia = limpiar_iframe(url_iframe)
    if url_limpia:
        url_base = url_limpia.split('?')[0]
        return url_base.rstrip('/').split('/')[-1]
    
    return 'Archivo'


def generar_id_unico(prefijo=''):
    """Genera un ID único basado en timestamp."""
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    return f"{prefijo}{timestamp}"

#=========================================================
# FUNCIONALIDAD DE GENERAR REPORTE DE LOS CURSOS COMPLETADOS POR MESES
#=========================================================

def get_stats_mes(curso, quiz, year, month):
    from .models import ProgresoUsuario, AsignacionCurso

    # Solo los empleados asignados a ESTE curso
    total_empleados = AsignacionCurso.objects.filter(curso=curso).count()
    usuarios_asignados_ids = AsignacionCurso.objects.filter(
        curso=curso
    ).values_list('usuario_id', flat=True)

    total_completados = ProgresoUsuario.objects.filter(
        quiz=quiz,
        usuario_id__in=usuarios_asignados_ids,
        quiz_completado=True
    ).values('usuario').distinct().count()

    completados_mes = ProgresoUsuario.objects.filter(
        quiz=quiz,
        usuario_id__in=usuarios_asignados_ids,
        quiz_completado=True,
        fecha_respuesta__year=year,
        fecha_respuesta__month=month
    ).values('usuario').distinct().count()

    en_progreso = ProgresoUsuario.objects.filter(
        quiz=quiz,
        usuario_id__in=usuarios_asignados_ids,
        respondida=True,
        quiz_completado=False
    ).values('usuario').distinct().count()

    pendientes = max(total_empleados - total_completados, 0)

    return {
        'total_completados': total_completados,
        'completados_mes':   completados_mes,
        'en_progreso':       en_progreso,
        'pendientes':        pendientes,
        'total_empleados':   total_empleados,
    }


def get_stats_rango(curso, quiz, fecha_inicio, fecha_fin):
    from .models import ProgresoUsuario, AsignacionCurso

    total_empleados = AsignacionCurso.objects.filter(curso=curso).count()
    usuarios_asignados_ids = AsignacionCurso.objects.filter(
        curso=curso
    ).values_list('usuario_id', flat=True)

    total_completados = ProgresoUsuario.objects.filter(
        quiz=quiz,
        usuario_id__in=usuarios_asignados_ids,
        quiz_completado=True
    ).values('usuario').distinct().count()

    completados_rango = ProgresoUsuario.objects.filter(
        quiz=quiz,
        usuario_id__in=usuarios_asignados_ids,
        quiz_completado=True,
        fecha_respuesta__date__gte=fecha_inicio,
        fecha_respuesta__date__lte=fecha_fin
    ).values('usuario').distinct().count()

    en_progreso = ProgresoUsuario.objects.filter(
        quiz=quiz,
        usuario_id__in=usuarios_asignados_ids,
        respondida=True,
        quiz_completado=False
    ).values('usuario').distinct().count()

    pendientes = max(total_empleados - total_completados, 0)

    return {
        'total_completados': total_completados,
        'completados_rango': completados_rango,
        'en_progreso': en_progreso,
        'pendientes': pendientes,
        'total_empleados': total_empleados,
    }


MESES_ES = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
]

def get_meses_historicos(curso, quiz):
    """
    Retorna una lista de stats mes a mes desde la creación del curso
    hasta el mes anterior al actual. Máximo 6 meses hacia atrás.
    """
    hoy = date.today()
    mes_actual_year  = hoy.year
    mes_actual_month = hoy.month

    if curso.fecha_public:
        delta_meses = (
            (hoy.year - curso.fecha_public.year) * 12
            + (hoy.month - curso.fecha_public.month)
        )
    else:
        delta_meses = 0

    n_meses = min(delta_meses, 6)

    historico = []
    for i in range(1, n_meses + 1):
        m = mes_actual_month - i
        y = mes_actual_year
        while m <= 0:
            m += 12
            y -= 1

        if quiz:
            stats = get_stats_mes(curso, quiz, y, m)
        else:
            stats = {
                'total_completados': 0,
                'completados_mes': 0,
                'en_progreso': 0,
                'pendientes': 0,
                'total_empleados': 0,
            }

        historico.append({
            'label': f"{MESES_ES[m-1]} {y}",
            'month': m,
            'year':  y,
            **stats,
        })

    return historico

def get_cursos_stats(year=None, month=None):
    from .models import Curso

    hoy   = date.today()
    year  = year  or hoy.year
    month = month or hoy.month

    cursos    = Curso.objects.prefetch_related('quiz').all()
    resultado = []

    for curso in cursos:
        quiz = getattr(curso, 'quiz', None)

        if quiz:
            stats_actual  = get_stats_mes(curso, quiz, year, month)
            meses_hist    = get_meses_historicos(curso, quiz)
        else:
            stats_actual = {
                'total_completados': 0,
                'completados_mes':   0,
                'en_progreso':       0,
                'pendientes':        0,
                'total_empleados':   0,
            }
            meses_hist = []

        resultado.append({
            'curso':        curso,
            'tiene_quiz':   quiz is not None,
            'mes_actual': {
                'label': f"{MESES_ES[month-1]} {year}",
                **stats_actual,
            },
            'meses_hist':   meses_hist,
        })

    return resultado, {
        'year':      year,
        'month':     month,
        'mes_label': f"{MESES_ES[month-1]} {year}",
    }




def generar_excel(cursos_ids, fecha_inicio, fecha_fin):
    label_rango = f"{fecha_inicio.strftime('%d/%m/%Y')} — {fecha_fin.strftime('%d/%m/%Y')}"

    wb = Workbook()
    ws = wb.active
    ws.title = "Estadísticas Cursos"

    # --- Estilos ---
    fill_titulo    = PatternFill("solid", fgColor="1F4E79")
    fill_header    = PatternFill("solid", fgColor="1F4E79")
    fill_subheader = PatternFill("solid", fgColor="2E75B6")
    fill_alt       = PatternFill("solid", fgColor="EBF3FB")
    fill_blanco    = PatternFill("solid", fgColor="FFFFFF")

    font_titulo    = Font(name="Arial", bold=True,  size=14, color="FFFFFF")
    font_sub_it    = Font(name="Arial", italic=True, size=10, color="FFFFFF")
    font_header    = Font(name="Arial", bold=True,  size=11, color="FFFFFF")
    font_subheader = Font(name="Arial", bold=True,  size=10, color="FFFFFF")
    font_body      = Font(name="Arial", size=10)
    font_pendiente = Font(name="Arial", bold=True,  size=10, color="9A3412")

    al_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    al_left   = Alignment(horizontal="left",   vertical="center")
    thin      = Side(style="thin", color="BFBFBF")
    border    = Border(left=thin, right=thin, top=thin, bottom=thin)

    # --- Filas de título y encabezado ---
    ws.row_dimensions[1].height = 28
    ws.merge_cells("A1:H1")
    c = ws["A1"]
    c.value, c.font, c.fill, c.alignment = (
        f"Reporte de Cursos — {label_rango}", font_titulo, fill_titulo, al_center
    )

    ws.row_dimensions[2].height = 18
    ws.merge_cells("A2:H2")
    c = ws["A2"]
    c.value, c.font, c.fill, c.alignment = (
        f"Generado el {date.today().strftime('%d/%m/%Y')}", font_sub_it, fill_titulo, al_center
    )

    ws.row_dimensions[3].height = 22
    ws.row_dimensions[4].height = 22

    grupos = [
        (1, 1, "Curso"),
        (2, 2, "Creado"),
        (3, 7, label_rango),
        (8, 8, "Estado"),
    ]
    for col_ini, col_fin, texto in grupos:
        c = ws.cell(row=3, column=col_ini)
        c.value, c.font, c.fill, c.alignment, c.border = (
            texto, font_header, fill_header, al_center, border
        )
        if col_ini != col_fin:
            ws.merge_cells(
                start_row=3, start_column=col_ini,
                end_row=3,   end_column=col_fin
            )

    sub_textos = [
        "Nombre del Curso",        # A
        "Fecha Creación",          # B
        "Total Empleados",         # C
        "Total Completados",       # D
        f"Completados en período", # E
        "En Progreso",             # F
        "Pendientes",              # G
        "Tiene Quiz",              # H
    ]
    for col, texto in enumerate(sub_textos, start=1):
        c = ws.cell(row=4, column=col)
        c.value, c.font, c.fill, c.alignment, c.border = (
            texto, font_subheader, fill_subheader, al_center, border
        )

    # --- Datos (bucle integrado) ---
    cursos = Curso.objects.filter(id_curso__in=cursos_ids).prefetch_related('quiz')

    for i, curso in enumerate(cursos):
        row  = 5 + i
        fill = fill_alt if i % 2 == 0 else fill_blanco

        quiz = getattr(curso, 'quiz', None)

        # Llamada corregida: get_stats_rango solo necesita el quiz y las fechas
        if quiz:
            stats = get_stats_rango(curso, quiz, fecha_inicio, fecha_fin)
        else:
            stats = {
                'total_empleados': 0,
                'total_completados': 0,
                'completados_rango': 0,
                'en_progreso': 0,
                'pendientes': 0,
            }

        valores = [
            curso.titulo,
            curso.fecha_public.strftime('%d/%m/%Y') if curso.fecha_public else '',
            stats['total_empleados'],
            stats['total_completados'],
            stats['completados_rango'],
            stats['en_progreso'],
            stats['pendientes'],
            "Sí" if quiz else "No",
        ]

        for col_idx, val in enumerate(valores, start=1):
            c = ws.cell(row=row, column=col_idx, value=val)
            c.fill   = fill
            c.border = border
            if col_idx == 7 and isinstance(val, int) and val > 0:
                c.font      = font_pendiente
                c.alignment = al_center
            else:
                c.font      = font_body
                c.alignment = al_left if col_idx == 1 else al_center

    # --- Ajustar anchos ---
    anchos = [35, 16, 16, 18, 22, 14, 14, 12]
    for idx, w in enumerate(anchos, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = w

    # --- Salida ---
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output