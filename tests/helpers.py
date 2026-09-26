from core.lexer import tokenizar
from core.parser import parsear


def parsear_codigo(codigo: str, nombre_archivo: str = "prueba.eng"):
    tokens = tokenizar(codigo, nombre_archivo)
    return parsear(tokens, nombre_archivo)
