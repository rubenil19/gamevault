"""Clase Videojuego de GameVault.

Representa un juego de la biblioteca. Los atributos son privados (doble guion
bajo) y se usan con @property como getters y setters.
"""


class Videojuego:
    """Un videojuego de la colección.

    Desde fuera solo se toca a través de las propiedades, y cada setter valida
    el valor, así que el objeto nunca se queda con datos no válidos.
    """

    # Opciones permitidas. Son tuplas para que no se puedan modificar por error.
    PLATAFORMAS = ("PC", "PlayStation 5", "PlayStation 4", "Xbox", "Nintendo Switch", "Otra")
    GENEROS = ("Acción", "Aventura", "RPG", "Deportes", "Estrategia", "Simulación", "Terror", "Otro")
    ESTADOS = ("Pendiente", "Jugando", "Completado")

    def __init__(self, juego_id, nombre, plataforma, genero, valoracion=0,
                 estado="Pendiente", descripcion="", portada=""):
        """Crea el objeto. Valoración, estado, descripción y portada son opcionales."""
        self.__id = str(juego_id)  # no tiene setter, el id no cambia
        # estas asignaciones llaman a los setters, que validan y lanzan ValueError si algo falla
        self.nombre = nombre
        self.plataforma = plataforma
        self.genero = genero
        self.valoracion = valoracion
        self.estado = estado
        self.descripcion = descripcion
        self.portada = portada

    # ---------- Getters y setters ----------
    @property
    def id(self):
        """Identificador único del juego (solo lectura)."""
        return self.__id

    @property
    def nombre(self):
        """Nombre del videojuego."""
        return self.__nombre

    # setter del nombre: no puede estar vacío ni pasar de 70 caracteres
    @nombre.setter
    def nombre(self, valor):
        valor = str(valor).strip()  # quito espacios sobrantes
        if not valor or len(valor) > 70:
            raise ValueError("El nombre debe tener entre 1 y 70 caracteres.")
        self.__nombre = valor

    @property
    def plataforma(self):
        """Plataforma en la que se juega."""
        return self.__plataforma

    # setter de la plataforma: tiene que ser una de PLATAFORMAS
    @plataforma.setter
    def plataforma(self, valor):
        if valor not in self.PLATAFORMAS:
            raise ValueError("Plataforma no válida.")
        self.__plataforma = valor
