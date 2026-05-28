from django import template

register = template.Library()

@register.filter(name='filename')
def filename(value):
    """Devuelve el nombre del archivo a partir de una URL (último segmento tras la última /)."""
    if not value:
        return ''
    # Si termina en '/', quitamos ese último carácter vacío
    url = value.rstrip('/')
    return url.split('/')[-1] if '/' in url else url


@register.filter(name='get_item')
def get_item(dictionary, key):
    """Devuelve un valor de diccionario por clave."""
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)