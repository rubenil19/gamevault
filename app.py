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

# ---------- Rutas ----------

@app.route("/")
def index():
    """Página principal: lista de juegos con búsqueda, filtros, orden y estadísticas."""
    juegos = cargar_juegos()

    # parámetros del formulario de filtros (GET)
    filtro_plataforma = request.args.get("plataforma", "")
    filtro_estado = request.args.get("estado", "")
    orden = request.args.get("orden", "")
    busqueda = request.args.get("q", "").strip()

    # solo filtro si el valor es una opción válida
    filtrados = juegos
    if filtro_plataforma in Videojuego.PLATAFORMAS:
        filtrados = [j for j in filtrados if j.plataforma == filtro_plataforma]
    if filtro_estado in Videojuego.ESTADOS:
        filtrados = [j for j in filtrados if j.estado == filtro_estado]
    if busqueda:
        filtrados = [j for j in filtrados if busqueda.lower() in j.nombre.lower()]
    filtrados = ordenar_juegos(filtrados, orden)

    # Counter cuenta cuántos juegos hay de cada estado
    por_estado = Counter(j.estado for j in juegos)
    estadisticas = {
        "total": len(juegos),
        "jugando": por_estado["Jugando"],
        "completados": por_estado["Completado"],
        "pendientes": por_estado["Pendiente"],
    }

    # con un set me quito las plataformas repetidas
    plataformas_en_uso = sorted({j.plataforma for j in juegos})

    return render_template(
        "index.html",
        juegos=filtrados,
        estadisticas=estadisticas,
        plataformas=Videojuego.PLATAFORMAS,
        estados=Videojuego.ESTADOS,
        plataformas_en_uso=plataformas_en_uso,
        filtro_plataforma=filtro_plataforma,
        filtro_estado=filtro_estado,
        orden=orden,
        busqueda=busqueda,
    )


@app.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    """CREATE: enseña el formulario (GET) y guarda el juego (POST)."""
    if request.method == "GET":
        return mostrar_formulario("Añadir videojuego", {}, url_for("nuevo"))

    datos, errores = validar_formulario(request.form)
    if errores:
        for error in errores:
            avisar(error, "error")
        # se devuelve el formulario con lo que había escrito para que no lo pierda
        return mostrar_formulario("Añadir videojuego", datos, url_for("nuevo"), 400)

    try:
        juegos = cargar_juegos()
        juego = Videojuego(
            juego_id=str(uuid4()),
            nombre=datos["nombre"],
            plataforma=datos["plataforma"],
            genero=datos["genero"],
            valoracion=datos["valoracion"],
            estado=datos["estado"],
            descripcion=datos["descripcion"],
            portada=datos["portada"],
        )
    except ValueError as error:
        # el modelo valida otra vez, por si se escapa algo
        app.logger.warning("Datos rechazados por el modelo: %s", error)
        avisar(str(error), "error")
        return mostrar_formulario("Añadir videojuego", datos, url_for("nuevo"), 400)

    juegos.append(juego)
    if not cabe_en_cookie(juegos):
        # si no, el navegador descartaría la cookie y se perdería todo
        avisar("La biblioteca está llena: la cookie de sesión no admite más datos. "
               "Elimina algún juego o acorta las notas y las URL.", "error")
        return mostrar_formulario("Añadir videojuego", datos, url_for("nuevo"), 400)

    guardar_juegos(juegos)
    avisar(f"«{juego.nombre}» se ha añadido a tu biblioteca.")
    return redirect(url_for("index"))


@app.route("/editar/<juego_id>", methods=["GET", "POST"])
def editar(juego_id):
    """UPDATE: formulario con los datos actuales y guardado de los cambios."""
    juegos = cargar_juegos()
    juego = buscar_juego(juegos, juego_id)
    if juego is None:
        avisar("No se ha encontrado ese videojuego.", "error")
        return redirect(url_for("index"))

    accion = url_for("editar", juego_id=juego_id)

    if request.method == "GET":
        return mostrar_formulario("Editar videojuego", juego.a_dict(), accion)

    datos, errores = validar_formulario(request.form)
    if errores:
        for error in errores:
            avisar(error, "error")
        return mostrar_formulario("Editar videojuego", datos, accion, 400)

    try:
        # cada asignación pasa por el setter, que valida
        juego.nombre = datos["nombre"]
        juego.plataforma = datos["plataforma"]
        juego.genero = datos["genero"]
        juego.valoracion = datos["valoracion"]
        juego.estado = datos["estado"]
        juego.descripcion = datos["descripcion"]
        juego.portada = datos["portada"]
    except ValueError as error:
        # la lista se vuelve a cargar en cada petición, así que no se guarda nada a medias
        app.logger.warning("Datos rechazados por el modelo: %s", error)
        avisar(str(error), "error")
        return mostrar_formulario("Editar videojuego", datos, accion, 400)

    if not cabe_en_cookie(juegos):
        avisar("Los cambios no caben en la cookie de sesión. Acorta las notas o la URL.", "error")
        return mostrar_formulario("Editar videojuego", datos, accion, 400)

    guardar_juegos(juegos)
    avisar(f"«{juego.nombre}» se ha actualizado.")
    return redirect(url_for("index"))


@app.route("/eliminar/<juego_id>", methods=["POST"])
def eliminar(juego_id):
    """DELETE: solo por POST para que un simple enlace no pueda borrar datos."""
    juegos = cargar_juegos()
    juego = buscar_juego(juegos, juego_id)
    if juego is None:
        avisar("No se ha encontrado ese videojuego.", "error")
    else:
        # me quedo con todos menos el borrado
        guardar_juegos([j for j in juegos if j.id != juego_id])
        avisar(f"«{juego.nombre}» se ha eliminado.")
    return redirect(url_for("index"))


# ---------- Errores ----------

@app.errorhandler(404)
def pagina_no_encontrada(_error):
    """Error 404: la página no existe."""
    return render_template("error.html", codigo=404, mensaje="La página que buscas no existe."), 404


@app.errorhandler(Exception)
def error_inesperado(error):
    """Para cualquier otra excepción: página de error en vez de la traza."""
    if isinstance(error, HTTPException):
        # errores HTTP normales (405, 400...): con su código
        return render_template("error.html", codigo=error.code, mensaje=error.description), error.code
    app.logger.exception("Error inesperado")
    return render_template("error.html", codigo=500, mensaje="Ha ocurrido un error inesperado."), 500


if __name__ == "__main__":
    # debug solo si se pone FLASK_DEBUG=1
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")

