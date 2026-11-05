from core.tokens import Token, TipoToken
from core.errors import ErrorSintactico

TOKENS_TIPO = {
    TipoToken.ENTERO,
    TipoToken.DECIMAL,
    TipoToken.EXPRESION,
    TipoToken.DECLARACION,
    TipoToken.PISTAS,
    TipoToken.TABLERO,
}


class _ParserBase:

    def __init__(self, tokens: list[Token], nombre_archivo: str):
        self.tokens = tokens
        self.nombre_archivo = nombre_archivo
        self.pos = 0

    def _actual(self) -> Token:
        return self.tokens[self.pos]

    def _avanzar(self) -> Token:
        token = self.tokens[self.pos]
        if self._actual().tipo != TipoToken.FIN_DE_ARCHIVO:
            self.pos += 1
        return token

    def _verificar(self, tipo: TipoToken) -> bool:
        return self._actual().tipo == tipo

    def _linea_del_faltante(self) -> int:
        """Linea donde falta un simbolo esperado. Si el token que si aparecio esta en una linea
        posterior, lo que falta iba al final de la linea anterior (p. ej. un '!' olvidado)."""
        actual = self._actual()
        if self.pos > 0 and self.tokens[self.pos - 1].linea < actual.linea:
            return self.tokens[self.pos - 1].linea
        return actual.linea

    def _esperar(self, tipo: TipoToken) -> Token:
        if self._verificar(tipo):
            return self._avanzar()
        linea = self._linea_del_faltante()
        raise ErrorSintactico(
            tipo="Token inesperado",
            archivo=self.nombre_archivo,
            linea=linea,
            pista=f"Se esperaba {tipo.name} cerca de la linea {linea}.",
            descripcion=(
                f"Se esperaba {tipo.name} pero se encontró "
                f"{self._actual().tipo.name} ('{self._actual().lexema}')."
            ),
            causa_posible="Revisa que no falte un símbolo o palabra clave antes de este punto.",
        )

    def _esperar_tipo(self) -> Token:
        token = self._actual()
        if token.tipo not in TOKENS_TIPO:
            raise ErrorSintactico(
                tipo="Tipo invalido",
                archivo=self.nombre_archivo,
                linea=token.linea,
                pista="Se esperaba un tipo (entero, decimal, expresion, declaracion, pistas o tablero).",
                descripcion=(
                    f"Se esperaba un tipo pero se encontro {token.tipo.name} "
                    f"('{token.lexema}')."
                ),
                causa_posible="Revisa que el tipo sea uno de los tipos validos del lenguaje.",
            )
        return self._avanzar()
