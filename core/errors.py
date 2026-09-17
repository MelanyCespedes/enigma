class PistaFallidaDeRazonamiento(Exception):
    """Clase base de todos los errores de Enigma."""

    def __init__(
        self,
        tipo: str,
        archivo: str,
        linea: int,
        pista: str,
        descripcion: str,
        causa_posible: str,
    ):
        self.tipo = tipo
        self.archivo = archivo
        self.linea = linea
        self.pista = pista
        self.descripcion = descripcion
        self.causa_posible = causa_posible
        super().__init__(self.mostrar_completo())

    def mostrar_pista(self) -> str:
        """Primer aviso: solo la pista"""
        return f"Pista: {self.pista}"

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


class ErrorLexico(PistaFallidaDeRazonamiento):
    """Caracter no reconocido, cadena sin cerrar, numero mal formado, etc."""


class ErrorSintactico(PistaFallidaDeRazonamiento):
    """Token inesperado, bloque sin cerrar, falta el sello, etc."""


class ErrorSemantico(PistaFallidaDeRazonamiento):
    """Variable no declarada, tipos incompatibles, reasignar un hecho, etc."""


class ErrorDeImportacion(PistaFallidaDeRazonamiento):
    """Archivo o funcion no encontrada, importacion circular, etc."""


class ErrorDeEjecucion(PistaFallidaDeRazonamiento):
    """Division entre cero, indice fuera de rango, etc."""
