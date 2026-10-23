"""Logica del Constructor de pistas: arma codigo Enigma a partir de formularios y
lo valida con el propio compilador. No usa tkinter (tiene pruebas en tests/)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from core.errors import ErrorSemantico, PistaFallidaDeRazonamiento
from core.lexer import tokenizar
from core.parser import parsear
from core.semantic import analizar
from gui.pistas import es_orientadora

TIPOS = ("entero", "decimal", "expresion", "declaracion")
SANGRIA = "    "


@dataclass(frozen=True)
class Campo:
    clave: str
    etiqueta: str
    tipo: str = "texto"           # "texto" | "opciones" | "casilla"
    por_defecto: object = ""
    opciones: tuple[str, ...] = ()
    ayuda: str = ""
    multilinea: bool = False      # varias instrucciones (una por linea)


@dataclass(frozen=True)
class Bloque:
    id: str
    titulo: str
    descripcion: str
    campos: tuple[Campo, ...]


BLOQUES: tuple[Bloque, ...] = (
    Bloque("declarar", "Declarar una pista", "Crea una variable (pista) o una constante (hecho).", (
        Campo("nombre", "Nombre", por_defecto="sospechoso"),
        Campo("tipo", "Tipo", "opciones", "entero", TIPOS),
        Campo("valor", "Valor inicial", por_defecto="15",
              ayuda="Para declaracion: culpable o NoCulpable. Vacío o sin_pista = sin valor."),
        Campo("constante", "Es un hecho (constante)", "casilla", False),
    )),
    Bloque("revelar", "Mostrar un mensaje", "Escribe un texto (y, si quieres, una pista) en la salida.", (
        Campo("mensaje", "Mensaje", por_defecto="Hola, detective."),
        Campo("variable", "Pista a mostrar (opcional)", por_defecto=""),
    )),
    Bloque("consultar", "Preguntar un dato", "Lee un valor del usuario y lo guarda en una pista ya declarada.", (
        Campo("variable", "Pista donde guardarlo", por_defecto="edad"),
    )),
    Bloque("asignar", "Cambiar una pista", "Le da un nuevo valor a una pista declarada.", (
        Campo("variable", "Pista", por_defecto="edad"),
        Campo("valor", "Nuevo valor", por_defecto="conectar(edad, 1)"),
    )),
    Bloque("condicional", "Condicional (evaluar si)", "Ejecuta algo solo si se cumple una condición.", (
        Campo("condicion", "Condición", por_defecto="edad >= 18"),
        Campo("entonces", "Si se cumple", por_defecto="revelar('Mayor de edad')!", multilinea=True),
        Campo("con_sino", "Con alternativa (sino)", "casilla", True),
        Campo("sino", "Si no se cumple", por_defecto="revelar('Menor de edad')!", multilinea=True),
    )),
    Bloque("rastrear", "Ciclo contado (rastrear)", "Repite un bloque contando de un valor a otro.", (
        Campo("contador", "Contador", por_defecto="paso"),
        Campo("desde", "Desde", por_defecto="1"),
        Campo("hasta", "Hasta", por_defecto="10"),
        Campo("cuerpo", "Qué repetir", por_defecto="revelar(paso)!", multilinea=True),
    )),
    Bloque("mientras", "Ciclo con condición (seguir mientras)", "Repite mientras la condición sea verdadera.", (
        Campo("condicion", "Condición", por_defecto="n > 0"),
        Campo("cuerpo", "Qué repetir", por_defecto="n = descartar(n, 1)!", multilinea=True),
    )),
    Bloque("escena", "Función con retorno (escena)", "Una función que devuelve un valor.", (
        Campo("nombre", "Nombre", por_defecto="Promedio"),
        Campo("parametros", "Parámetros", por_defecto="a: entero, b: entero", ayuda="nombre: tipo, nombre: tipo"),
        Campo("retorno", "Tipo que devuelve", "opciones", "decimal", TIPOS),
        Campo("expresion", "Valor que devuelve", por_defecto="repartir(conectar(a, b), 2)"),
    )),
    Bloque("proceso", "Función sin retorno (proceso)", "Una función que hace algo pero no devuelve nada.", (
        Campo("nombre", "Nombre", por_defecto="Saludar"),
        Campo("parametros", "Parámetros", por_defecto="nombre: expresion", ayuda="nombre: tipo, nombre: tipo"),
        Campo("cuerpo", "Qué hace", por_defecto="revelar('Hola', nombre)!", multilinea=True),
    )),
    Bloque("importar", "Importar otro archivo", "Usa las funciones de otro archivo del proyecto.", (
        Campo("archivo", "Archivo", por_defecto="pistas.eng"),
    )),
    Bloque("caso", "Esqueleto de un caso", "El programa principal con su apertura y cierre.", (
        Campo("nombre", "Nombre del caso", por_defecto="MiCaso"),
        Campo("cuerpo", "Contenido", por_defecto="revelar('Hola, detective.')!", multilinea=True),
    )),
)

POR_ID = {b.id: b for b in BLOQUES}


# --------------------------------------------------------------------------- #
# Generacion
# --------------------------------------------------------------------------- #

def valores_iniciales(bloque: Bloque) -> dict:
    return {c.clave: c.por_defecto for c in bloque.campos}


def _texto(valores: dict, clave: str) -> str:
    return str(valores.get(clave, "") or "").strip()


def _instrucciones(texto: str) -> str:
    """Cada linea es una instruccion: se garantiza el '!' final."""
    lineas = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        lineas.append(linea if linea.endswith(("!", "}")) else linea + "!")
    return "\n".join(lineas)


def _sangrar(texto: str) -> str:
    return "\n".join(SANGRIA + linea for linea in texto.splitlines())


def literal(tipo: str, valor: str) -> str:
    """Escribe el valor en la forma que pide Enigma: entero(valor: 15), etc."""
    valor = (valor or "").strip()
    if valor == "" or valor.lower() == "sin_pista":
        return f"{tipo}(valor: sin_pista)"
    if tipo == "expresion":
        return f"expresion(valor: '{valor.strip(chr(39)).replace(chr(39), '’')}')"
    if tipo == "declaracion":
        verdadero = valor.lower() in ("culpable", "verdadero", "true", "si", "sí", "1")
        return f"declaracion(valor: {'culpable' if verdadero else 'NoCulpable'})"
    return f"{tipo}(valor: {valor})"


def generar(id_bloque: str, valores: dict) -> str:
    v = lambda clave: _texto(valores, clave)  # noqa: E731

    if id_bloque == "declarar":
        palabra = "hecho" if valores.get("constante") else "pista"
        return f"{palabra} {v('nombre')} = {literal(v('tipo') or 'entero', v('valor'))}!"

    if id_bloque == "revelar":
        partes = []
        if v("mensaje"):
            partes.append("'" + v("mensaje").replace("'", "’") + "'")
        if v("variable"):
            partes.append(v("variable"))
        return f"revelar({', '.join(partes)})!"

    if id_bloque == "consultar":
        return f"consultar({v('variable')})!"

    if id_bloque == "asignar":
        return f"{v('variable')} = {v('valor')}!"

    if id_bloque == "condicional":
        codigo = f"evaluar si ({v('condicion')}) inicio\n{_sangrar(_instrucciones(v('entonces')))}\nfin!"
        if valores.get("con_sino"):
            codigo += f"\nsino inicio\n{_sangrar(_instrucciones(v('sino')))}\nfin!"
        return codigo

    if id_bloque == "rastrear":
        return (
            f"rastrear {v('contador')} desde {v('desde')} hasta {v('hasta')} inicio\n"
            f"{_sangrar(_instrucciones(v('cuerpo')))}\nfin!"
        )

    if id_bloque == "mientras":
        return f"seguir mientras ({v('condicion')}) inicio\n{_sangrar(_instrucciones(v('cuerpo')))}\nfin!"

    if id_bloque == "escena":
        return (
            f"escena {v('nombre')}({v('parametros')})::{v('retorno') or 'entero'} inicio\n"
            f"{SANGRIA}concluir {v('expresion')}!\nfin!"
        )

    if id_bloque == "proceso":
        return f"proceso {v('nombre')}({v('parametros')}) inicio\n{_sangrar(_instrucciones(v('cuerpo')))}\nfin!"

    if id_bloque == "importar":
        return f"#expediente <{v('archivo')}>"

    if id_bloque == "caso":
        nombre = v("nombre")
        return f"caso {nombre} abierto\n{_sangrar(_instrucciones(v('cuerpo')))}\ncaso {nombre} cerrado!"

    raise KeyError(id_bloque)


# --------------------------------------------------------------------------- #
# Validacion con el compilador
# --------------------------------------------------------------------------- #

def _envolver(codigo: str) -> str:
    if re.search(r"^\s*caso\s", codigo, re.M):
        return codigo
    if re.search(r"^\s*(escena|proceso|#expediente)\b", codigo, re.M):
        return codigo + "\ncaso T abierto\ncaso T cerrado!\n"
    return "caso T abierto\n" + _sangrar(codigo) + "\ncaso T cerrado!\n"


def validar(codigo: str) -> str | None:
    """None si el codigo es valido; si no, un mensaje corto con el motivo.

    El codigo sale del formulario, asi que puede referirse a pistas que ya existen
    en el archivo donde se insertara: por eso no se reporta 'variable no declarada'."""
    try:
        programa = parsear(tokenizar(_envolver(codigo), "constructor.eng"), "constructor.eng")
        analizar(programa)
    except ErrorSemantico as error:
        if "ninguna variable" in error.descripcion or "no existe" in error.descripcion.lower():
            return None
        return _mensaje(error)
    except PistaFallidaDeRazonamiento as error:
        return _mensaje(error)
    return None


def _mensaje(error: PistaFallidaDeRazonamiento) -> str:
    """Motivo corto y legible (sin lineas ni nombres internos del compilador)."""
    if es_orientadora(error.pista):
        return error.pista.strip()
    return "El bloque no tiene una sintaxis válida. Revisa los valores del formulario."
