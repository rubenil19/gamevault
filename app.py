"""GameVault: app de Flask para llevar la cuenta de mi colección de videojuegos.

Archivos principales:
  - app.py         rutas, validación del formulario y guardado en sesión
  - videojuego.py  clase Videojuego (POO con atributos privados)
  - templates/     plantillas Jinja2
  - static/        CSS

Los datos se guardan en la sesión de Flask, que es una cookie firmada, así que
no hay base de datos. El problema es que una cookie no puede pasar de unos 4 KB,
por eso existe la función cabe_en_cookie().
"""
import logging
import os
from collections import Counter
from datetime import timedelta
from uuid import uuid4

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.exceptions import HTTPException

from videojuego import Videojuego

app = Flask(__name__)

# Clave que firma la cookie. La leo de una variable de entorno; la de por defecto
# vale para probar en local pero no hay que usarla si se publica la app.
app.secret_key = os.environ.get("SECRET_KEY", "clave-solo-para-desarrollo-local")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,   # JavaScript no puede leer la cookie
    SESSION_COOKIE_SAMESITE="Lax",  # no se manda desde otras webs
)

# La colección dura 30 días aunque se cierre el navegador
app.permanent_session_lifetime = timedelta(days=30)

# Los navegadores tiran las cookies de más de ~4093 bytes. Dejo margen porque
# en la misma cookie también van los mensajes flash.
LIMITE_COOKIE_BYTES = 3400

logging.basicConfig(level=logging.INFO)


# Filtro de Jinja2 para pintar las estrellas: {{ 3|estrellas }}
@app.template_filter("estrellas")
def estrellas(valoracion, maximo=5):
    """Convierte la valoración en estrellas llenas y vacías."""
    return "★" * valoracion + "☆" * (maximo - valoracion)


# ---------- Guardar y leer la sesión ----------

def cargar_juegos():
    """Convierte los diccionarios de la sesión en objetos Videojuego."""
    datos_guardados = session.get("juegos", [])
    if not isinstance(datos_guardados, list):
        # si la cookie tiene un formato raro la ignoro para que no pete la página
        app.logger.warning("La clave 'juegos' de la sesión no es una lista.")
        return []

    juegos = []
    for datos in datos_guardados:
        try:
            juegos.append(Videojuego.desde_dict(datos))
        except (KeyError, TypeError, ValueError) as error:
            # si un registro está mal lo salto y el resto se queda
            app.logger.warning("Se ha omitido un registro de sesión no válido: %s", error)
    return juegos


def cabe_en_cookie(juegos):
    """Mira si la colección entra en la cookie (máximo unos 4 KB).

    Uso el mismo serializador que Flask para que el tamaño sea el real.
    """
    serializador = app.session_interface.get_signing_serializer(app)
    contenido = serializador.dumps({"juegos": [juego.a_dict() for juego in juegos]})
    return len(contenido) <= LIMITE_COOKIE_BYTES


def guardar_juegos(juegos):
    """Guarda la lista de juegos en la sesión como diccionarios."""
    session["juegos"] = [juego.a_dict() for juego in juegos]
    session.permanent = True
    session.modified = True  # para que Flask vuelva a mandar la cookie


def buscar_juego(juegos, juego_id):
    """Devuelve el juego con ese id o None si no está."""
    encontrado = None
    for juego in juegos:
        if juego.id == juego_id:
            encontrado = juego
            break
    else:
        # el else del for solo salta si no se hizo break
        app.logger.info("No existe ningún juego con id %s", juego_id)
    return encontrado


def avisar(mensaje, categoria="success"):
    """Mensaje que se enseña en la siguiente página (success o error)."""
    flash(mensaje, categoria)


# ---------- Validación del formulario ----------

def validar_formulario(form):
    """Limpia y valida lo que llega por POST.

    Devuelve (datos, errores). Si errores está vacía, los datos son buenos.
    También compruebo los desplegables porque el navegador se puede manipular.
    """
    errores = []

    # strip() quita los espacios de los extremos
    nombre = form.get("nombre", "").strip()
    plataforma = form.get("plataforma", "").strip()
    genero = form.get("genero", "").strip()
    estado = form.get("estado", "").strip()
    valoracion_texto = form.get("valoracion", "0").strip()
    descripcion = form.get("descripcion", "").strip()
    portada = form.get("portada", "").strip()

    if not nombre:
        errores.append("El nombre del videojuego es obligatorio.")
    elif len(nombre) > 70:
        errores.append("El nombre no puede superar los 70 caracteres.")

    # los valores de los select tienen que estar en las listas del modelo
    if plataforma not in Videojuego.PLATAFORMAS:
        errores.append("Selecciona una plataforma válida.")
    if genero not in Videojuego.GENEROS:
        errores.append("Selecciona un género válido.")
    if estado not in Videojuego.ESTADOS:
        errores.append("Selecciona un estado válido.")

    # la valoración tiene que ser un entero de 0 a 5
    try:
        valoracion = int(valoracion_texto)
    except ValueError:
        valoracion = 0
        errores.append("La valoración debe ser un número entero entre 0 y 5.")
    else:
        if not 0 <= valoracion <= 5:
            errores.append("La valoración debe estar entre 0 y 5.")

    # campos opcionales
    if len(descripcion) > 240:
        errores.append("La descripción no puede superar los 240 caracteres.")
    if portada and not portada.startswith(("http://", "https://")):
        errores.append("La URL de portada debe comenzar por http:// o https://.")

    datos = {
        "nombre": nombre,
        "plataforma": plataforma,
        "genero": genero,
        "estado": estado,
        "valoracion": valoracion,
        "descripcion": descripcion,
        "portada": portada,
    }
    return datos, errores


def ordenar_juegos(juegos, criterio):
    """Ordena según lo elegido en el desplegable (con match)."""
    match criterio:
        case "nombre":
            return sorted(juegos, key=lambda juego: juego.nombre.lower())
        case "valoracion":
            return sorted(juegos, key=lambda juego: juego.valoracion, reverse=True)
        case "estado":
            return sorted(juegos, key=lambda juego: Videojuego.ESTADOS.index(juego.estado))
        case _:
            return juegos  # sin criterio, el orden en que se añadieron


def mostrar_formulario(titulo, juego, accion, codigo=200):
    """Pinta el formulario de añadir/editar. Con errores se usa el código 400."""
    return render_template(
        "formulario.html",
        titulo=titulo,
        juego=juego,
        plataformas=Videojuego.PLATAFORMAS,
        generos=Videojuego.GENEROS,
        estados=Videojuego.ESTADOS,
        accion=accion,
    ), codigo

