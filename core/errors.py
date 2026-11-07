class IndicioFallidoDeRazonamiento(Exception):
    """Clase base de todos los errores de Enigma."""

    def __init__(
        self,
        tipo: str,
        archivo: str,
        linea: int,
        indicio: str,
        descripcion: str,
        causa_posible: str,
    ):
        self.tipo = tipo
        self.archivo = archivo
        self.linea = linea
        self.indicio = indicio
        self.descripcion = descripcion
        self.causa_posible = causa_posible
        super().__init__(self.mostrar_completo())

    def mostrar_indicio(self) -> str:
        """Primer aviso: solo el indicio"""
        return f"Indicio: {self.indicio}"

    def mostrar_completo(self) -> str:
        """Segundo aviso: error completo"""
        return (
            f"Error de {self.tipo}\n"
            f"Archivo: {self.archivo}\n"
            f"Linea: {self.linea}\n"
            f"Descripcion: {self.descripcion}\n"
            f"Posible causa: {self.causa_posible}"
        )

    def __str__(self) -> str:
        return self.mostrar_completo()


class ErrorLexico(IndicioFallidoDeRazonamiento):
    """Caracter no reconocido, cadena sin cerrar, numero mal formado, etc."""


class ErrorSintactico(IndicioFallidoDeRazonamiento):
    """Token inesperado, bloque sin cerrar, falta el sello, etc."""


class ErrorSemantico(IndicioFallidoDeRazonamiento):
    """Variable no declarada, tipos incompatibles, reasignar un hecho, etc."""


class ErrorDeImportacion(IndicioFallidoDeRazonamiento):
    """Archivo o funcion no encontrada, importacion circular, etc."""


class ErrorDeEjecucion(IndicioFallidoDeRazonamiento):
    """Division entre cero, indice fuera de rango, etc."""
