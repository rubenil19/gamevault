# GameVault — Colección de videojuegos

Proyecto de Flask para la U.T.2 (Generación de documentos web). Es una app para llevar la cuenta de los juegos que tengo, los que estoy jugando y los que ya he terminado.

## Requisitos

- Python 3.10 o superior (uso `match`)
- pip

## Cómo ejecutarlo en Windows

Abre una terminal dentro de la carpeta `GameVault` y ejecuta:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py app.py
```

## Cómo ejecutarlo en Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Después abre `http://127.0.0.1:5000` en el navegador.

Variables de entorno (son opcionales):

- `SECRET_KEY`: clave con la que se firma la cookie de sesión. Si no la defines se usa una de desarrollo.
- `FLASK_DEBUG=1`: activa el modo debug (solo para probar en local).

## Qué hace

- CRUD completo: añadir, ver, editar y eliminar videojuegos.
- Búsqueda por nombre y filtros por plataforma y estado.
- Ordenación por nombre, valoración o estado.
- Estadísticas: total de juegos, jugando, completados y pendientes.
- Formulario por POST con validación en el servidor.
- Mensajes de confirmación y de error.
- Clase `Videojuego` con atributos privados y `@property` como getters y setters, con validación.
- Los datos se guardan en la sesión de Flask (cookie firmada) y duran 30 días.
- Aviso cuando la cookie está a punto de llenarse (límite de unos 4 KB), para no perder datos.
- Control de excepciones y páginas de error 404/500.
- Diseño responsive con plantillas Jinja2.

### Menú superior

La barra de arriba aparece en todas las páginas y tiene tres elementos:

- **GameVault** (logo, arriba a la izquierda): lleva siempre a la página principal.
- **Biblioteca**: abre la página principal con todos tus juegos.
- **＋ Añadir juego**: abre el formulario para meter un videojuego nuevo.

### Página principal (Biblioteca)

1. **Cabecera con botón**: el botón **＋ Añadir videojuego** hace lo mismo que el del menú.
2. **Estadísticas**: cuatro tarjetas con el total de juegos, los que estás jugando, los completados y los pendientes. Se actualizan solas al añadir, editar o eliminar.
3. **Mi biblioteca**: muestra cuántos juegos se están viendo y en cuántas plataformas distintas.
4. **Buscador y filtros** (se aplican al pulsar **Filtrar**):
   - **Buscar un videojuego**: busca por nombre, sin importar mayúsculas.
   - **Plataforma**: enseña solo los juegos de esa plataforma.
   - **Estado**: enseña solo los pendientes, los que estás jugando o los completados.
   - **Orden**: por orden de añadido (por defecto), nombre (A-Z), mejor valorados o estado.
   - **Limpiar**: aparece cuando hay algún filtro activo y lo quita todo.
5. **Tarjetas de juego**: cada tarjeta enseña la portada, la plataforma, el estado (con un color distinto para cada uno), el nombre, las estrellas, el género y tus notas.
   - ** Editar**: abre el formulario con los datos del juego para cambiarlos.
   - **Eliminar**: borra el juego tras pedir confirmación.
6. Si no hay juegos, o los filtros no encuentran nada, aparece un mensaje que lo indica y un botón para añadir uno.

### Formulario (añadir y editar)

| Campo | Obligatorio | Qué poner |
|-------|-------------|-----------|
| Nombre del videojuego | Sí | Hasta 70 caracteres |
| Plataforma | Sí | Se elige de la lista |
| Género | Sí | Se elige de la lista |
| Estado | Sí | Pendiente, Jugando o Completado |
| Valoración | Sí | De 0 (sin valorar) a 5 |
| URL de portada | No | Enlace a una imagen que empiece por http:// o https://. Si se deja vacío o no carga, se crea una portada con la inicial del juego |
| Notas personales | No | Hasta 240 caracteres |

- **Guardar videojuego**: valida los datos y, si todo está bien, vuelve a la biblioteca con un mensaje verde. Si algo falla, el formulario se queda con lo escrito y salen mensajes rojos explicando qué corregir.
- **Cancelar** y **← Volver a la biblioteca**: salen sin guardar nada.

### Mensajes y límites

- Verde: la acción se ha hecho (juego añadido, actualizado o eliminado). Rojo: hay algún error.
- Los juegos se guardan en el navegador durante 30 días. Si la biblioteca se llena, la app avisa y hay que eliminar algún juego o acortar notas y URL.
- Si se entra en una dirección que no existe, sale una página de error con un botón para volver.

## Cómo se guardan los datos

No hay base de datos: uso la sesión de Flask, que por defecto es una cookie firmada del navegador. Cada objeto `Videojuego` se pasa a diccionario y se guarda la lista en `session["juegos"]`; al leerla se vuelven a crear los objetos.

Lo bueno es que no hace falta base de datos y cada navegador tiene su propia colección. Lo malo es que el tamaño está limitado, los datos no se comparten entre navegadores ni dispositivos, y quien inspeccione la cookie puede leerla (aunque no modificarla sin la clave). Por eso no hay que guardar contraseñas ni datos sensibles. En un proyecto real lo mejor sería guardar los datos en el servidor.

## Estructura

```text
GameVault/
├── app.py
├── videojuego.py
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── formulario.html
│   └── error.html
└── static/
    └── style.css
```

