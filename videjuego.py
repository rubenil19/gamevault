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

 @property
    def genero(self):
        """Género del juego."""
        return self.__genero

    # setter del género: tiene que ser uno de GENEROS
    @genero.setter
    def genero(self, valor):
        if valor not in self.GENEROS:
            raise ValueError("Género no válido.")
        self.__genero = valor

    @property
    def valoracion(self):
        """Valoración personal, un entero entre 0 y 5."""
        return self.__valoracion

    # setter de la valoración: entero entre 0 y 5
    @valoracion.setter
    def valoracion(self, valor):
        try:
            valor = int(valor)
        except (ValueError, TypeError):
            # int("abc") da ValueError e int(None) da TypeError,
            # los junto en un solo ValueError con un mensaje claro
            raise ValueError("La valoración debe ser un número entero.")
        if not 0 <= valor <= 5:
            raise ValueError("La valoración debe estar entre 0 y 5.")
        self.__valoracion = valor

    @property
    def estado(self):
        """Estado de progreso: Pendiente, Jugando o Completado."""
        return self.__estado

    # setter del estado: tiene que ser uno de ESTADOS
    @estado.setter
    def estado(self, valor):
        if valor not in self.ESTADOS:
            raise ValueError("Estado no válido.")
        self.__estado = valor

    @property
    def descripcion(self):
        """Notas personales (máximo 240 caracteres)."""
        return self.__descripcion

    # setter de la descripción: máximo 240 caracteres
    @descripcion.setter
    def descripcion(self, valor):
        valor = str(valor).strip()
        if len(valor) > 240:
            raise ValueError("La descripción no puede superar 240 caracteres.")
        self.__descripcion = valor
