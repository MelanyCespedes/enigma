from core.tokens import PALABRAS_RESERVADAS, Token, TipoToken
from core.errors import ErrorSintactico

TOKENS_TIPO = {
    TipoToken.ENTERO,
    TipoToken.DECIMAL,
    TipoToken.EXPRESION,
    TipoToken.DECLARACION,
    TipoToken.PISTAS,
    TipoToken.TABLERO,
}


# Primer indicio cuando falta un simbolo: orienta sobre el tipo de problema sin nombrar el simbolo
# ni la linea (el detalle exacto sale en la explicacion completa).
INDICIO_FALTA_ALGO = "Parece que falta algo en alguna parte de tu código."
INDICIO_ABRIR_CERRAR = "Parece que algo no quedó bien abierto o cerrado."  # parentesis, corchetes y bloques
INDICIO_EN_INSTRUCCION = "Parece que a una instrucción le falta una de sus partes."
INDICIOS_POR_TOKEN_FALTANTE = {
    TipoToken.SELLO: "Parece que falta algo al final de alguna instrucción.",
    TipoToken.PARENTESIS_IZQ: INDICIO_ABRIR_CERRAR,
    TipoToken.PARENTESIS_DER: INDICIO_ABRIR_CERRAR,
    TipoToken.CORCHETE_IZQ: INDICIO_ABRIR_CERRAR,
    TipoToken.CORCHETE_DER: INDICIO_ABRIR_CERRAR,
    TipoToken.INICIO: INDICIO_ABRIR_CERRAR,
    TipoToken.FIN: INDICIO_ABRIR_CERRAR,
    TipoToken.ABIERTO: INDICIO_ABRIR_CERRAR,
    TipoToken.CERRADO: INDICIO_ABRIR_CERRAR,
    TipoToken.IDENTIFICADOR: "Parece que falta el nombre de algo que estás declarando.",
    TipoToken.IGUAL: "Parece que falta algo al declarar o cambiar una pista.",
    TipoToken.DOS_PUNTOS: INDICIO_EN_INSTRUCCION,
    TipoToken.COMA: INDICIO_EN_INSTRUCCION,
    TipoToken.VALOR: INDICIO_EN_INSTRUCCION,
    TipoToken.SI: "Parece que a un condicional le falta una parte.",
    TipoToken.DESDE: "Parece que a un ciclo le falta una parte.",
    TipoToken.HASTA: "Parece que a un ciclo le falta una parte.",
    TipoToken.MIENTRAS: "Parece que a un ciclo le falta una parte.",
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
        encontrado = self._actual()
        if tipo == TipoToken.IDENTIFICADOR and encontrado.lexema in PALABRAS_RESERVADAS:
            raise ErrorSintactico(
                tipo="Palabra reservada",
                archivo=self.nombre_archivo,
                linea=linea,
                indicio="Parece que usaste una palabra reservada como nombre.",
                descripcion=f"Se esperaba un nombre pero se encontró la palabra reservada '{encontrado.lexema}'.",
                causa_posible=f"'{encontrado.lexema}' ya tiene un significado en Enigma y no puede usarse como "
                              "nombre de pista, parámetro o función. Elige otro nombre.",
            )
        error = ErrorSintactico(
            tipo="Token inesperado",
            archivo=self.nombre_archivo,
            linea=linea,
            indicio=INDICIOS_POR_TOKEN_FALTANTE.get(tipo, INDICIO_FALTA_ALGO),
            descripcion=(
                f"Se esperaba {tipo.name} pero se encontró "
                f"{self._actual().tipo.name} ('{self._actual().lexema}')."
            ),
            causa_posible="Revisa que no falte un símbolo o palabra clave antes de este punto.",
        )
        # Que token faltaba y donde: permite suponer el simbolo olvidado y seguir leyendo el codigo
        # (asi se pueden calcular las advertencias aunque haya un '!' de menos).
        error.esperado = tipo
        error.posicion = self.pos
        raise error

    def _esperar_tipo(self) -> Token:
        token = self._actual()
        if token.tipo not in TOKENS_TIPO:
            raise ErrorSintactico(
                tipo="Tipo inválido",
                archivo=self.nombre_archivo,
                linea=token.linea,
                indicio="Parece que falta el tipo de algo que estás declarando.",
                descripcion=(
                    f"Se esperaba un tipo (entero, decimal, expresion, declaracion, pistas o tablero) pero se encontró {token.tipo.name} "
                    f"('{token.lexema}')."
                ),
                causa_posible="Revisa que el tipo sea uno de los tipos válidos del lenguaje.",
            )
        return self._avanzar()
