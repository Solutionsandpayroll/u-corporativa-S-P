"""
blob_adjuntos.py
================

Sustituye a graph_adjuntos.py usando Vercel Blob como almacén de archivos.

Sube archivos (imágenes, videos, documentos) a un Blob Store de Vercel vía su
API HTTP y devuelve un dict con la MISMA forma que el módulo anterior
(embed_url, embed_html, nombre, web_url) para no romper vistas ni templates.

Requiere la variable de entorno:
    BLOB_READ_WRITE_TOKEN   (la crea Vercel automáticamente al crear el Blob Store)

Uso:
    from .blob_adjuntos import subir_archivo_admin, subir_archivo_empleado
"""

import os
import re
import uuid
import mimetypes
import logging

import requests

logger = logging.getLogger(__name__)

BLOB_TOKEN = os.environ.get("BLOB_READ_WRITE_TOKEN", "")
BLOB_ENDPOINT = "https://blob.vercel-storage.com/put"

# Prefijos de carpeta según quién sube el archivo (equivalente a las
# antiguas carpetas "U corporativa - Admin" / "U corporativa - Empleados").
CARPETA_ADMIN = os.environ.get("BLOB_CARPETA_ADMIN", "u-corporativa/admin")
CARPETA_EMPLEADOS = os.environ.get("BLOB_CARPETA_EMPLEADOS", "u-corporativa/empleados")


class BlobError(Exception):
    """Error al interactuar con Vercel Blob."""
    pass


def _sanitizar_nombre(nombre):
    """Deja el nombre seguro para usarlo como pathname, conservando la extensión."""
    nombre = (nombre or "archivo").strip()
    base, ext = os.path.splitext(nombre)
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", base)[:80] or "archivo"
    ext = re.sub(r"[^A-Za-z0-9.]+", "", ext).lower()
    return f"{base}{ext}"


def _subir_blob(nombre_archivo, contenido_bytes, carpeta):
    """
    Sube los bytes a Vercel Blob y devuelve el driveItem-like dict.
    Genera un pathname único (uuid + nombre) para evitar colisiones.
    """
    if not BLOB_TOKEN:
        raise BlobError(
            "No está configurada la variable de entorno BLOB_READ_WRITE_TOKEN."
        )

    nombre_limpio = _sanitizar_nombre(nombre_archivo)
    pathname = f"{carpeta}/{uuid.uuid4().hex}-{nombre_limpio}"

    content_type = (
        mimetypes.guess_type(nombre_archivo)[0]
        or "application/octet-stream"
    )

    files = {
        "content": (nombre_limpio, contenido_bytes, content_type),
    }
    data = {
        "pathname": pathname,
        "access": "public",
        "addUniqueSuffix": "true",
    }
    headers = {"Authorization": f"Bearer {BLOB_TOKEN}"}

    resp = requests.post(
        BLOB_ENDPOINT, headers=headers, files=files, data=data, timeout=120
    )

    if resp.status_code not in (200, 201):
        raise BlobError(f"Error subiendo el archivo: {resp.status_code} - {resp.text}")

    try:
        payload = resp.json()
    except ValueError:
        raise BlobError(f"Respuesta no válida de Vercel Blob: {resp.text}")

    url = payload.get("url")
    if not url:
        raise BlobError(f"Vercel Blob no devolvió una URL: {payload}")

    logger.info("Archivo '%s' subido a Blob: %s", nombre_archivo, url)
    return {
        "nombre": payload.get("pathname", nombre_archivo),
        "url": url,
    }


def _empaquetar(item):
    """Devuelve el dict con la forma compatible con graph_adjuntos."""
    url = item["url"]
    return {
        "nombre": item["nombre"],
        "item_id": url,
        "web_url": url,
        "embed_url": url,
        "embed_html": url,
    }


def subir_archivo_admin(nombre_archivo, contenido_bytes):
    """Sube un archivo de admin a la carpeta pública de Blob correspondiente."""
    item = _subir_blob(nombre_archivo, contenido_bytes, CARPETA_ADMIN)
    return _empaquetar(item)


def subir_archivo_empleado(nombre_archivo, contenido_bytes):
    """Sube un archivo de empleado a la carpeta pública de Blob correspondiente."""
    item = _subir_blob(nombre_archivo, contenido_bytes, CARPETA_EMPLEADOS)
    return _empaquetar(item)
