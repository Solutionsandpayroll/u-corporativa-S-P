"""
blob_adjuntos.py
================

Almacena los archivos subidos (imagenes, videos, documentos) en Vercel Blob
usando el SDK oficial de Python (`vercel-blob`), en su API sincronica
(adeccion para Django/WSGI).

Devuelve un dict con la MISMA forma que el modulo anterior de Graph
(embed_url, embed_html, nombre, web_url) para no romper vistas ni templates.

Credenciales (resueltas automaticamente por el SDK en este orden):
    1. OIDC: VERCEL_OIDC_TOKEN + BLOB_STORE_ID (Vercel las pone solo)
    2. BLOB_READ_WRITE_TOKEN (token estatico de lectura/escritura)

IMPORTANTE: para que las imagenes se muestren con <img src=URL> sin autenticacion,
el Blob Store debe ser de acceso PUBLICO. Se puede fijar con BLOB_ACCESS=public.
"""

import os
import re
import uuid
import logging

from vercel.blob import sync as blob

logger = logging.getLogger(__name__)

# "public" (URL abierta, ideal para imagenes) o "private" (debe coincidir con
# el modo de acceso con el que se creo el Blob Store).
BLOB_ACCESS = os.environ.get("BLOB_ACCESS", "public")

# Prefijos de carpeta segun quien sube el archivo (antes: carpetas de OneDrive).
CARPETA_ADMIN = os.environ.get("BLOB_CARPETA_ADMIN", "u-corporativa/admin")
CARPETA_EMPLEADOS = os.environ.get("BLOB_CARPETA_EMPLEADOS", "u-corporativa/empleados")


class BlobError(Exception):
    """Error al interactuar con Vercel Blob."""
    pass


def _sanitizar_nombre(nombre):
    """Nombre seguro para usarlo como pathname, conservando la extension."""
    nombre = (nombre or "archivo").strip()
    base, ext = os.path.splitext(nombre)
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", base)[:80] or "archivo"
    ext = re.sub(r"[^A-Za-z0-9.]+", "", ext).lower()
    return f"{base}{ext}"


def _subir(nombre_archivo, contenido_bytes, carpeta):
    if not contenido_bytes:
        raise BlobError("El archivo esta vacio.")

    nombre_limpio = _sanitizar_nombre(nombre_archivo)
    pathname = f"{carpeta}/{uuid.uuid4().hex}-{nombre_limpio}"

    try:
        resultado = blob.put_blob(
            pathname,
            contenido_bytes,
            access=BLOB_ACCESS,
        )
    except Exception as e:
        raise BlobError(f"Error subiendo el archivo: {type(e).__name__}: {e}")

    url = getattr(resultado, "url", None)
    if not url:
        raise BlobError(f"Vercel Blob no devolvio una URL: {resultado}")

    logger.info("Archivo '%s' subido a Blob: %s", nombre_archivo, url)
    return {
        "nombre": getattr(resultado, "pathname", nombre_archivo),
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
    """Sube un archivo de admin al Blob Store (carpeta de admin)."""
    return _empaquetar(_subir(nombre_archivo, contenido_bytes, CARPETA_ADMIN))


def subir_archivo_empleado(nombre_archivo, contenido_bytes):
    """Sube un archivo de empleado al Blob Store (carpeta de empleados)."""
    return _empaquetar(_subir(nombre_archivo, contenido_bytes, CARPETA_EMPLEADOS))
