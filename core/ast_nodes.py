from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union

# ---------- Programa ----------


@dataclass
class Importacion:
    archivo: str
    linea: int


@dataclass
class CasoPrincipal:
    nombre: str
    cuerpo: list
    linea: int


@dataclass
class Programa:
    importaciones: list[Importacion]
    declaraciones_globales: list["DeclaracionPista"]
    funciones: dict[str, Union["Escena", "Proceso"]]
    caso_principal: CasoPrincipal
    archivo_origen: str


# ---------- Declaraciones ----------


@dataclass
class DeclaracionPista:
    nombre: str
    valor: "Expresion"
    es_constante: bool
    linea: int


@dataclass
class Asignacion:
    nombre: str
    valor: "Expresion"
    linea: int


# ---------- Entrada / Salida ----------


@dataclass
class Revelar:
    argumentos: list["Expresion"]
    linea: int


@dataclass
class Consultar:
    variable: str
    linea: int


# ---------- Condicionales ----------


@dataclass
class RamaCondicional:
    condicion: "Expresion"
    cuerpo: list


@dataclass
class EvaluarSi:
    rama_si: RamaCondicional
    ramas_sino_evaluar: list[RamaCondicional]
    cuerpo_sino: Optional[list]
    linea: int


@dataclass
class CasoSuceso:
    numero: int
    condicion: "Expresion"
    cuerpo: list


@dataclass
class Suceso:
    variable: "Expresion"
    casos: list[CasoSuceso]
    linea: int


# ---------- Ciclos ----------


@dataclass
class Rastrear:
    variable: str
    desde: "Expresion"
    hasta: "Expresion"
    cuerpo: list
    linea: int


@dataclass
class SeguirMientras:
    condicion: "Expresion"
    cuerpo: list
    linea: int


# ---------- Funciones ----------


@dataclass
class Parametro:
    nombre: str
    tipo: str


@dataclass
class Escena:  # funcion CON retorno
    nombre: str
    parametros: list[Parametro]
    tipo_retorno: str
    cuerpo: list
    linea: int


@dataclass
class Proceso:  # funcion SIN retorno
    nombre: str
    parametros: list[Parametro]
    cuerpo: list
    linea: int


@dataclass
class Resolver:  # llamada a funcion
    nombre: str
    argumentos: list["Expresion"]
    linea: int


@dataclass
class Concluir:
    valor: "Expresion"
    linea: int


# ---------- Expresiones ----------


@dataclass
class Literal:
    tipo: str  # "entero" | "decimal" | "expresion" | "declaracion" | "sin_pista"
    valor: object


@dataclass
class Identificador:
    nombre: str


@dataclass
class OperacionAritmetica:
    operador: str  # conectar | descartar | intensificar | repartir
    operandos: list["Expresion"]
    linea: int = 0


@dataclass
class OperacionLogica:
    operador: str  # y | o | no
    izquierda: "Expresion"
    derecha: Optional["Expresion"]  # None cuando operador == 'no'


@dataclass
class OperacionRelacional:
    operador: str  # == | <> | > | < | >= | <=
    izquierda: "Expresion"
    derecha: "Expresion"


@dataclass
class ListaLiteral:  # pistas entero[2, 4, 6]
    tipo_elemento: str
    elementos: list["Expresion"]


@dataclass
class TableroLiteral:  # tablero entero[4][4]
    tipo_elemento: str
    filas: "Expresion"
    columnas: "Expresion"


@dataclass
class AccesoIndice:  # variable[i] o tablero[i][j]
    base: "Expresion"
    indices: list["Expresion"]


Sentencia = Union[
    DeclaracionPista,
    Asignacion,
    Revelar,
    Consultar,
    EvaluarSi,
    Suceso,
    Rastrear,
    SeguirMientras,
    Resolver,
    Concluir,
]

Expresion = Union[
    Literal,
    Identificador,
    OperacionAritmetica,
    OperacionLogica,
    OperacionRelacional,
    ListaLiteral,
    TableroLiteral,
    AccesoIndice,
]
