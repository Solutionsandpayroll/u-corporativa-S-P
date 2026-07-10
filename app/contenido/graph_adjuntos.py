"""
graph_adjuntos.py
==================

Módulo de integración con Microsoft Graph para:
1. Crear (si no existe) dos carpetas separadas en el OneDrive de una cuenta específica:
   - "U corporativa - Admin" (para archivos subidos por administradores)
   - "U corporativa - Empleados" (para archivos subidos por empleados)
2. Compartir cada carpeta con un grupo de Azure AD, asignando distintos permisos:
   - Admin: solo lectura (read)
   - Empleados: lectura y escritura (write)
3. Subir archivos dentro de la carpeta correspondiente según el rol.
4. Generar el link de tipo "embed" del archivo subido (el mismo formato
   que antes se pegaba manualmente como iframe).

Uso típico desde una vista de Django:

    from .graph_adjuntos import subir_archivo_admin, subir_archivo_empleado

    # Para archivos de apoyo de preguntas (subidos por admin)
    resultado = subir_archivo_admin(
        nombre_archivo="imagen.png",
        contenido_bytes=archivo.read(),
    )
    # resultado["embed_html"]  -> el <iframe ...></iframe> completo
    # resultado["embed_url"]   -> solo la URL del src

    # Para archivos de respuestas de empleados
    resultado = subir_archivo_empleado(
        nombre_archivo="respuesta.pdf",
        contenido_bytes=archivo.read(),
    )

Requiere:
    pip install msal requests

Variables de entorno / settings necesarias:
    GRAPH_TENANT_ID_ADJUNTOS
    GRAPH_CLIENT_ID_ADJUNTOS
    GRAPH_CLIENT_SECRET_ADJUNTOS
    GRAPH_USER_ID_ADJUNTOS            (correo o id del usuario dueño del OneDrive)
    GRAPH_GROUP_ID_ADJUNTOS           (object id del grupo de Azure AD)
    GRAPH_CARPETA_ADMIN               (nombre de la carpeta para admin, default "U corporativa - Admin")
    GRAPH_CARPETA_EMPLEADOS           (nombre de la carpeta para empleados, default "U corporativa - Empleados")
"""

import os
import time
import logging
import requests
import msal

logger = logging.getLogger(__name__)


# =========================================================
# CONFIGURACIÓN
# =========================================================

TENANT_ID = os.environ.get("GRAPH_TENANT_ID_ADJUNTOS", "")
CLIENT_ID = os.environ.get("GRAPH_CLIENT_ID_ADJUNTOS", "")
CLIENT_SECRET = os.environ.get("GRAPH_CLIENT_SECRET_ADJUNTOS", "")

GRAPH_USER_ID = os.environ.get("GRAPH_USER_ID_ADJUNTOS", "pjimenez@solutionsandpayroll.com")

# Grupo de empleados al que se comparten ambas carpetas (con distinto rol cada una)
GRAPH_GROUP_ID = os.environ.get("GRAPH_GROUP_ID_ADJUNTOS", "")

# Dos carpetas separadas según quién sube el archivo
CARPETA_ADMIN = os.environ.get("GRAPH_CARPETA_ADMIN", "U corporativa - Admin")
CARPETA_EMPLEADOS = os.environ.get("GRAPH_CARPETA_EMPLEADOS", "U corporativa - Empleados")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]
GRAPH_BASE = "https://graph.microsoft.com/v1.0"


# =========================================================
# AUTENTICACIÓN (client credentials flow)
# =========================================================

_token_cache = {"access_token": None, "expires_at": 0}


def _obtener_token():
    """
    Obtiene (y cachea en memoria del proceso) el access_token de la app.
    Usa MSAL con client credentials flow (permisos tipo Application).
    """
    ahora = time.time()
    if _token_cache["access_token"] and ahora < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    app = msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=AUTHORITY,
    )

    resultado = app.acquire_token_for_client(scopes=SCOPE)

    if "access_token" not in resultado:
        error_desc = resultado.get("error_description", "Error desconocido al autenticar contra Graph")
        logger.error("Error obteniendo token de Graph: %s", error_desc)
        raise GraphError(f"No se pudo autenticar contra Microsoft Graph: {error_desc}")

    _token_cache["access_token"] = resultado["access_token"]
    _token_cache["expires_at"] = ahora + resultado.get("expires_in", 3600)
    return _token_cache["access_token"]


def _headers(extra=None):
    headers = {
        "Authorization": f"Bearer {_obtener_token()}",
        "Content-Type": "application/json",
    }
    if extra:
        headers.update(extra)
    return headers


class GraphError(Exception):
    """Error genérico al interactuar con Microsoft Graph."""
    pass


# =========================================================
# PASO 1: OBTENER O CREAR LA CARPETA (con rol específico)
# =========================================================

def obtener_o_crear_carpeta(nombre_carpeta, rol="read"):
    """
    Verifica si la carpeta ya existe en el OneDrive del usuario configurado.
    Si existe, retorna sus datos. Si no existe, la crea y la comparte
    con el grupo usando el rol indicado ('read' o 'write').
    Retorna: dict con al menos {'id': ..., 'name': ..., 'webUrl': ...,
                                 'creada_ahora': bool}
    """
    url_buscar = f"{GRAPH_BASE}/users/{GRAPH_USER_ID}/drive/root:/{nombre_carpeta}"
    resp = requests.get(url_buscar, headers=_headers())

    if resp.status_code == 200:
        data = resp.json()
        logger.info("La carpeta '%s' ya existe (id=%s)", nombre_carpeta, data.get("id"))
        data["creada_ahora"] = False
        return data

    if resp.status_code != 404:
        raise GraphError(f"Error verificando la carpeta: {resp.status_code} - {resp.text}")

    # No existe -> se crea
    url_crear = f"{GRAPH_BASE}/users/{GRAPH_USER_ID}/drive/root/children"
    body = {
        "name": nombre_carpeta,
        "folder": {},
        "@microsoft.graph.conflictBehavior": "fail",
    }
    resp_crear = requests.post(url_crear, headers=_headers(), json=body)

    if resp_crear.status_code not in (200, 201):
        raise GraphError(f"Error creando la carpeta: {resp_crear.status_code} - {resp_crear.text}")

    data = resp_crear.json()
    logger.info("Carpeta '%s' creada (id=%s) con rol '%s'", nombre_carpeta, data.get("id"), rol)
    data["creada_ahora"] = True

    compartir_carpeta_con_grupo(data["id"], roles=[rol])

    return data


# =========================================================
# PASO 2: COMPARTIR LA CARPETA CON EL GRUPO (con roles)
# =========================================================

def compartir_carpeta_con_grupo(folder_id, group_id=None, roles=None):
    """
    Comparte la carpeta con el grupo indicado.
    roles=["read"]  -> solo lectura (ver/descargar)
    roles=["write"] -> lectura y escritura (ver/descargar/subir/borrar)
    """
    group_id = group_id or GRAPH_GROUP_ID
    roles = roles or ["read"]

    if not group_id:
        logger.warning("GRAPH_GROUP_ID_ADJUNTOS no configurado, se omite el paso de compartir carpeta.")
        return None

    url = f"{GRAPH_BASE}/users/{GRAPH_USER_ID}/drive/items/{folder_id}/invite"
    body = {
        "recipients": [{"objectId": group_id}],
        "message": "Se ha compartido la carpeta corporativa.",
        "requireSignIn": True,
        "sendInvitation": False,
        "roles": roles,
    }

    resp = requests.post(url, headers=_headers(), json=body)

    if resp.status_code not in (200, 201):
        raise GraphError(f"Error compartiendo la carpeta con el grupo: {resp.status_code} - {resp.text}")

    logger.info("Carpeta %s compartida con el grupo %s (roles=%s)", folder_id, group_id, roles)
    return resp.json()


# =========================================================
# PASO 3: SUBIR EL ARCHIVO DENTRO DE LA CARPETA (con rol)
# =========================================================

def subir_archivo(nombre_archivo, contenido_bytes, carpeta_nombre, rol="read"):
    """
    Sube el archivo dentro de la carpeta (creándola primero si hace falta).
    Para archivos pequeños/medianos (<4MB) usa PUT simple.
    Para archivos grandes, usa upload session.

    Retorna el dict del "driveItem" creado en Graph.
    """
    obtener_o_crear_carpeta(carpeta_nombre, rol=rol)

    tamano_mb = len(contenido_bytes) / (1024 * 1024)

    if tamano_mb < 4:
        return _subir_archivo_simple(nombre_archivo, contenido_bytes, carpeta_nombre)
    else:
        return _subir_archivo_grande(nombre_archivo, contenido_bytes, carpeta_nombre)


def _subir_archivo_simple(nombre_archivo, contenido_bytes, carpeta_nombre):
    url = f"{GRAPH_BASE}/users/{GRAPH_USER_ID}/drive/root:/{carpeta_nombre}/{nombre_archivo}:/content"
    headers = {
        "Authorization": f"Bearer {_obtener_token()}",
        "Content-Type": "application/octet-stream",
    }
    resp = requests.put(url, headers=headers, data=contenido_bytes)

    if resp.status_code not in (200, 201):
        raise GraphError(f"Error subiendo el archivo: {resp.status_code} - {resp.text}")

    logger.info("Archivo '%s' subido correctamente", nombre_archivo)
    return resp.json()


def _subir_archivo_grande(nombre_archivo, contenido_bytes, carpeta_nombre):
    """
    Sube archivos >4MB usando una upload session, en fragmentos de 5MB
    tal como lo exige Microsoft Graph para archivos grandes.
    """
    url_sesion = (
        f"{GRAPH_BASE}/users/{GRAPH_USER_ID}/drive/root:/{carpeta_nombre}/{nombre_archivo}:"
        "/createUploadSession"
    )
    body = {"item": {"@microsoft.graph.conflictBehavior": "replace"}}
    resp = requests.post(url_sesion, headers=_headers(), json=body)

    if resp.status_code not in (200, 201):
        raise GraphError(f"Error creando sesión de subida: {resp.status_code} - {resp.text}")

    upload_url = resp.json()["uploadUrl"]

    tamano_total = len(contenido_bytes)
    fragmento = 5 * 1024 * 1024  # 5MB
    inicio = 0
    ultima_respuesta = None

    while inicio < tamano_total:
        fin = min(inicio + fragmento, tamano_total) - 1
        chunk = contenido_bytes[inicio:fin + 1]
        headers_chunk = {
            "Content-Length": str(len(chunk)),
            "Content-Range": f"bytes {inicio}-{fin}/{tamano_total}",
        }
        resp_chunk = requests.put(upload_url, headers=headers_chunk, data=chunk)

        if resp_chunk.status_code not in (200, 201, 202):
            raise GraphError(f"Error subiendo fragmento: {resp_chunk.status_code} - {resp_chunk.text}")

        ultima_respuesta = resp_chunk
        inicio = fin + 1

    logger.info("Archivo grande '%s' subido correctamente", nombre_archivo)
    return ultima_respuesta.json()

def obtener_sharepoint_ids(item_id):
    """
    Obtiene los sharepointIds del archivo subido (incluye el UniqueId real
    y la URL del sitio), necesarios para construir el link embed.aspx correcto.
    """
    url = f"{GRAPH_BASE}/users/{GRAPH_USER_ID}/drive/items/{item_id}?$select=sharepointIds"
    resp = requests.get(url, headers=_headers())

    if resp.status_code != 200:
        raise GraphError(f"Error obteniendo sharepointIds: {resp.status_code} - {resp.text}")

    data = resp.json()
    sp_ids = data.get("sharepointIds", {})
    unique_id = sp_ids.get("listItemUniqueId", "")
    site_url = sp_ids.get("siteUrl", "")

    if not unique_id or not site_url:
        raise GraphError(f"No se pudo obtener UniqueId/siteUrl del archivo: {sp_ids}")

    return unique_id, site_url

# =========================================================
# PASO 4: GENERAR EL LINK EMBED
# =========================================================

def generar_link_embed(item_id):
    """
    Construye el link tipo embed.aspx (el mismo formato que antes se pegaba
    manualmente como iframe), usando el UniqueId real del archivo en SharePoint.

    Retorna dict con: {'embed_url': ..., 'embed_html': ...}
    """
    unique_id, site_url = obtener_sharepoint_ids(item_id)

    embed_url = f"{site_url}/_layouts/15/embed.aspx?UniqueId={unique_id}"
    embed_html = (
        f'<iframe src="{embed_url}" width="640" height="360" '
        f'frameborder="0" scrolling="no" allowfullscreen></iframe>'
    )

    return {
        "embed_url": embed_url,
        "embed_html": embed_html,
        "raw": {"unique_id": unique_id, "site_url": site_url},
    }

# =========================================================
# ORQUESTADORES SEGÚN QUIÉN SUBE EL ARCHIVO
# =========================================================

def subir_archivo_admin(nombre_archivo, contenido_bytes):
    """
    Usar cuando el ADMIN sube el archivo de apoyo de una pregunta.
    Va a 'U corporativa - Admin', compartida con el grupo en SOLO LECTURA.
    """
    item = subir_archivo(nombre_archivo, contenido_bytes, CARPETA_ADMIN, rol="read")
    embed = generar_link_embed(item["id"])
    return {
        "nombre": item.get("name", nombre_archivo),
        "item_id": item["id"],
        "web_url": item.get("webUrl", ""),
        "embed_url": embed["embed_url"],
        "embed_html": embed["embed_html"],
    }


def subir_archivo_empleado(nombre_archivo, contenido_bytes):
    """
    Usar cuando el EMPLEADO sube su archivo como respuesta al quiz.
    Va a 'U corporativa - Empleados', compartida con el grupo en LECTURA Y ESCRITURA.
    """
    item = subir_archivo(nombre_archivo, contenido_bytes, CARPETA_EMPLEADOS, rol="write")
    embed = generar_link_embed(item["id"])
    return {
        "nombre": item.get("name", nombre_archivo),
        "item_id": item["id"],
        "web_url": item.get("webUrl", ""),
        "embed_url": embed["embed_url"],
        "embed_html": embed["embed_html"],
    }

