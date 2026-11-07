from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from typing import Iterator, Optional, Union

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
    indices: Optional[list["Expresion"]] = None  # None = asignacion simple; lista = celda[i][j] = valor


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
    archivo: str = ""  # archivo donde se declaro (para reportar errores)


@dataclass
class Proceso:  # funcion SIN retorno
    nombre: str
    parametros: list[Parametro]
    cuerpo: list
    linea: int
    archivo: str = ""  # archivo donde se declaro (para reportar errores)


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
    # Solo para 'entero(valor: sin_pista)': el tipo con que se declaro (aqui "entero")
    tipo_declarado: str = ""


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

def recorrer(obj) -> Iterator[object]:
    """Todos los nodos que cuelgan de 'obj' (incluido el propio), a cualquier profundidad.
    'obj' puede ser un nodo o una lista de nodos (por ejemplo, el cuerpo de una funcion)."""
    if isinstance(obj, list):
        for elemento in obj:
            yield from recorrer(elemento)
    elif is_dataclass(obj):
        yield obj
        for campo in fields(obj):
            yield from recorrer(getattr(obj, campo.name))
