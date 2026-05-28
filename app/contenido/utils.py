import re
from django.utils import timezone


def limpiar_iframe(url_iframe):
    """
    Extrae la URL limpia de un iframe de SharePoint.
    Si es un iframe, extrae el src. Si es una URL, la retorna como está.
    """
    if not url_iframe:
        return ''

    # Buscar src en iframe
    match = re.search(r'src="([^"]+)"', url_iframe)
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
    """Extrae la base del sitio de SharePoint."""
    if not url_iframe:
        return ''

    url_limpia = limpiar_iframe(url_iframe)
    match = re.search(r'(https?://[^/]+/[^/]+/[^/]+)', url_limpia, re.IGNORECASE)
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

