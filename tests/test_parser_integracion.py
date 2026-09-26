from pathlib import Path

from core.lexer import tokenizar
from core.parser import parsear
from core.ast_nodes import Programa, Escena, EvaluarSi, Rastrear, Resolver

RUTA_EJEMPLO = Path(__file__).resolve().parent.parent / "ejemplos" / "caso_promedio" / "caso_principal.eng"


def test_caso_promedio_completo_parsea_sin_excepciones():
    codigo = RUTA_EJEMPLO.read_text(encoding="utf-8")
    tokens = tokenizar(codigo, str(RUTA_EJEMPLO))
    programa = parsear(tokens, str(RUTA_EJEMPLO))

    assert isinstance(programa, Programa)
    assert programa.caso_principal.nombre == "CasoPromedio"

    assert "CalcularPromedio" in programa.funciones
    assert isinstance(programa.funciones["CalcularPromedio"], Escena)

    cuerpo = programa.caso_principal.cuerpo
    assert any(isinstance(s, EvaluarSi) for s in cuerpo)
    assert any(isinstance(s, Rastrear) for s in cuerpo)
    assert any(isinstance(s, Resolver) for s in cuerpo)
