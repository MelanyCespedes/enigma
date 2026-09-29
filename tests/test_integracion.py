import contextlib
import io

from core.lexer import tokenizar
from core.parser import parsear
from core.semantic import analizar
from core.interpreter import ejecutar

PROGRAMA_EJEMPLO = """
escena CalcularPromedio(a: entero, b: entero)::decimal inicio
    concluir repartir(conectar(a, b), 2)!
fin!

caso CasoPromedio abierto
    pista nota1 = entero(valor: 15)!
    pista nota2 = entero(valor: 18)!
    hecho notaMinima = entero(valor: 10)!

    evaluar si (nota1 < notaMinima) inicio
        revelar('El sospechoso reprobo la primera nota.')!
    fin!
    sino inicio
        revelar('El sospechoso aprobo la primera nota.')!
    fin!

    rastrear intento desde 1 hasta 3 inicio
        revelar('Intento numero:', intento)!
    fin!

    resolver CalcularPromedio(nota1, nota2)!
caso CasoPromedio cerrado!
"""


def test_pipeline_completo_lexer_parser_semantico_interprete():
    tokens = tokenizar(PROGRAMA_EJEMPLO, "ejemplo.eng")
    programa = parsear(tokens, "ejemplo.eng")

    analizar(programa)

    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        ejecutar(programa)

    texto = salida.getvalue()
    assert "aprobo la primera nota" in texto
    assert "Intento numero: 1" in texto
    assert "Intento numero: 3" in texto