"""Los mensajes que ve el estudiante deben llevar sus tildes."""
import ast
import glob
import os
import re

from core.errors import ErrorSemantico, ErrorSintactico

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMPOS = {"tipo", "indicio", "descripcion", "causa", "causa_posible"}

# Palabras que en espanol llevan tilde y que ya se escaparon sin ella alguna vez.
# (No incluye 'expresion' ni 'declaracion': asi se escriben las palabras del lenguaje.)
SIN_TILDE = re.compile(
    r"\b(encontro|despues|invalido|invalida|validos|simbolo|caracter|funcion|ambito|instruccion|abrio|"
    r"declaro|falto|linea|importacion|ejecucion|semantica|descripcion|sintactico|semantico)\b",
    re.IGNORECASE,
)


def _textos_de(valor):
    """Las partes de texto de un literal o f-string (sin los nombres entre llaves)."""
    if isinstance(valor, ast.Constant) and isinstance(valor.value, str):
        yield valor.value
    elif isinstance(valor, ast.JoinedStr):
        for parte in valor.values:
            if isinstance(parte, ast.Constant) and isinstance(parte.value, str):
                yield parte.value


def test_los_mensajes_de_error_del_compilador_llevan_tildes():
    sin_tilde = []
    revisados = 0
    for ruta in glob.glob(os.path.join(RAIZ, "core", "*.py")):
        arbol = ast.parse(open(ruta, encoding="utf-8").read())
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Call):
                continue
            for kw in nodo.keywords:
                if kw.arg in CAMPOS:
                    for texto in _textos_de(kw.value):
                        revisados += 1
                        for m in SIN_TILDE.finditer(texto):
                            sin_tilde.append(f"{os.path.basename(ruta)}:{nodo.lineno} {m.group(0)!r} en {texto[:60]!r}")
    assert revisados > 100  # el recorrido encontro los mensajes
    assert not sin_tilde, "mensajes sin tilde:\n" + "\n".join(sin_tilde)


def test_las_etiquetas_del_mensaje_completo_llevan_tilde():
    error = ErrorSintactico("Token inesperado", "p.eng", 3, "indicio", "descripción", "causa")
    texto = error.mostrar_completo()
    assert "Línea: 3" in texto and "Descripción: descripción" in texto
    assert "Linea:" not in texto and "Descripcion:" not in texto


def test_el_tipo_de_los_errores_semanticos_lleva_tilde():
    error = ErrorSemantico("semántica", "p.eng", 1, "indicio", "descripción", "causa")
    assert error.mostrar_completo().startswith("Error de semántica")
