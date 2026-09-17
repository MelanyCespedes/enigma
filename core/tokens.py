from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional


class TipoToken(Enum):
    PISTA = auto()
    HECHO = auto()
    VALOE = auto()

    CASO = auto()
    ABIERTO = auto()
    CERRADP = auto()

    REVELAR = auto()
    CONSULTAR = auto()

    EVALUAR = auto()
    SI = auto()
    SINO = auto()
    SUCESO = auto()

    INICIO = auto()
    FIN = auto()

    RASTREAR = auto()
    DESDE = auto()
    HASTA = auto()
    SEGUIR = auto()
    MIENTRAS = auto()

    ESCENA = auto()
    PROCESO = auto()
    RESOLVER = auto()
    CONCLUIR = auto()

    CONECTAR = auto()
    DESCARTAR = auto()
    INTENSIFICAR = auto()
    REPARTIR = auto()

    O = auto()
    Y = auto()
    NO = auto()
    ENTERO = auto()
    DECIMAL = auto()
    EXPRESION = auto()
    DECLARACION = auto()
    PISTAS = auto()
    TABLERO = auto()

    CULPABLE = auto()
    NO_CULPABLE = auto()
    SIN_PISTA = auto()

    INDENTIFICADOR = auto()
    NUMERO_ENTERO = auto()
    NUMERO_DECIMAL = auto()
    CADENA_TEXTO = auto()

    IGUAL_IGUAL = auto()
    DIFERENTE = auto()
    MAYOR = auto()
    MENOR = auto()
    MAYOR_IGUAL = auto()
    MENOR_IGUAL = auto()

    IGUAL = auto()
    PARENTESIS_IZQ = auto()
    PARENTESIS_DER = auto()
    CORCHETE_IZQ = auto()
    CORCHETE_DER = auto()
    DOS_PUNTOS = auto()
    COMA = auto()
    SELLO = auto()
    NUMERAL = auto()
    EXPEDIENTE = auto()
    RUTA_ARCHIVO = auto()

    FIN_DE_ARCHIVO = auto()


# Palabras reservadas -> tipo de token
PALABRAS_RESERVADAS: dict[str, TipoToken] = {
    "pista": TipoToken.PISTA,
    "hecho": TipoToken.HECHO,
    "valor": TipoToken.VALOR,
    "caso": TipoToken.CASO,
    "abierto": TipoToken.ABIERTO,
    "cerrado": TipoToken.CERRADO,
    "revelar": TipoToken.REVELAR,
    "consultar": TipoToken.CONSULTAR,
    "evaluar": TipoToken.EVALUAR,
    "si": TipoToken.SI,
    "sino": TipoToken.SINO,
    "suceso": TipoToken.SUCESO,
    "inicio": TipoToken.INICIO,
    "fin": TipoToken.FIN,
    "rastrear": TipoToken.RASTREAR,
    "desde": TipoToken.DESDE,
    "hasta": TipoToken.HASTA,
    "seguir": TipoToken.SEGUIR,
    "mientras": TipoToken.MIENTRAS,
    "escena": TipoToken.ESCENA,
    "proceso": TipoToken.PROCESO,
    "resolver": TipoToken.RESOLVER,
    "concluir": TipoToken.CONCLUIR,
    "conectar": TipoToken.CONECTAR,
    "descartar": TipoToken.DESCARTAR,
    "intensificar": TipoToken.INTENSIFICAR,
    "repartir": TipoToken.REPARTIR,
    "o": TipoToken.O,
    "y": TipoToken.Y,
    "no": TipoToken.NO,
    "entero": TipoToken.ENTERO,
    "decimal": TipoToken.DECIMAL,
    "expresion": TipoToken.EXPRESION,
    "declaracion": TipoToken.DECLARACION,
    "pistas": TipoToken.PISTAS,
    "tablero": TipoToken.TABLERO,
    "culpable": TipoToken.CULPABLE,
    "NoCulpable": TipoToken.NO_CULPABLE,
    "sin_pista": TipoToken.SIN_PISTA,
}


@dataclass
class Token:
    tipo: TipoToken
    lexema: str
    valor: Any
    linea: int
    columna: int

    def __repr__(self) -> str:
        return f"Token({self.tipo.name}, {self.lexema!r}, linea={self.linea})"
