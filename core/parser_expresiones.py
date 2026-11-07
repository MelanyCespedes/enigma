from core.tokens import TipoToken
from core.errors import ErrorSintactico
from core.ast_nodes import (
    Literal,
    Identificador,
    OperacionAritmetica,
    OperacionLogica,
    OperacionRelacional,
    ListaLiteral,
    TableroLiteral,
    AccesoIndice,
)

TOKENS_TIPO_LITERAL_CON_VALOR = {
    TipoToken.ENTERO: "entero",
    TipoToken.DECIMAL: "decimal",
    TipoToken.EXPRESION: "expresion",
    TipoToken.DECLARACION: "declaracion",
}

TOKENS_RELACIONALES = {
    TipoToken.IGUAL_IGUAL: "==",
    TipoToken.DIFERENTE: "<>",
    TipoToken.MAYOR: ">",
    TipoToken.MENOR: "<",
    TipoToken.MAYOR_IGUAL: ">=",
    TipoToken.MENOR_IGUAL: "<=",
}

TOKENS_LOGICOS = {
    TipoToken.Y: "y",
    TipoToken.O: "o",
}

TOKENS_ARITMETICOS_BINARIOS = {
    TipoToken.DESCARTAR: "descartar",
    TipoToken.INTENSIFICAR: "intensificar",
    TipoToken.REPARTIR: "repartir",
}


class _ExpresionesMixin:
    """Gramatica de expresiones: logica -> relacional -> aritmetica -> primaria."""

    # niveles de precedencia

    def _parsear_expresion(self):
        return self._parsear_expr_logica()

    def _parsear_expr_logica(self):
        if self._verificar(TipoToken.NO):
            self._avanzar()
            self._esperar(TipoToken.PARENTESIS_IZQ)
            operando = self._parsear_expresion()
            self._esperar(TipoToken.PARENTESIS_DER)
            return OperacionLogica(operador="no", izquierda=operando, derecha=None)

        izquierda = self._parsear_expr_relacional()
        while self._actual().tipo in TOKENS_LOGICOS:
            operador = TOKENS_LOGICOS[self._avanzar().tipo]
            derecha = self._parsear_expr_relacional()
            izquierda = OperacionLogica(operador=operador, izquierda=izquierda, derecha=derecha)
        return izquierda

    def _parsear_expr_relacional(self):
        izquierda = self._parsear_expr_aritmetica()
        if self._actual().tipo in TOKENS_RELACIONALES:
            operador = TOKENS_RELACIONALES[self._avanzar().tipo]
            derecha = self._parsear_expr_aritmetica()
            return OperacionRelacional(operador=operador, izquierda=izquierda, derecha=derecha)
        return izquierda

    def _parsear_expr_aritmetica(self):
        if self._verificar(TipoToken.CONECTAR):
            token_op = self._avanzar()
            self._esperar(TipoToken.PARENTESIS_IZQ)
            operandos = self._parsear_argumentos()
            self._esperar(TipoToken.PARENTESIS_DER)
            return OperacionAritmetica(operador="conectar", operandos=operandos, linea=token_op.linea)

        if self._actual().tipo in TOKENS_ARITMETICOS_BINARIOS:
            operador = TOKENS_ARITMETICOS_BINARIOS[self._actual().tipo]
            token_op = self._avanzar()
            self._esperar(TipoToken.PARENTESIS_IZQ)
            izquierda = self._parsear_expresion()
            self._esperar(TipoToken.COMA)
            derecha = self._parsear_expresion()
            self._esperar(TipoToken.PARENTESIS_DER)
            return OperacionAritmetica(operador=operador, operandos=[izquierda, derecha], linea=token_op.linea)

        return self._parsear_primaria()

    # primarias

    def _parsear_primaria(self):
        token = self._actual()

        if token.tipo == TipoToken.PARENTESIS_IZQ:
            self._avanzar()
            expresion = self._parsear_expresion()
            self._esperar(TipoToken.PARENTESIS_DER)
            return expresion

        if token.tipo in TOKENS_TIPO_LITERAL_CON_VALOR:
            return self._parsear_constructor_tipo()

        if token.tipo == TipoToken.PISTAS:
            return self._parsear_pistas_literal()

        if token.tipo == TipoToken.TABLERO:
            return self._parsear_tablero_literal()

        if token.tipo == TipoToken.IDENTIFICADOR:
            self._avanzar()
            base = Identificador(nombre=token.lexema)
            return self._parsear_acceso_indice_opcional(base)

        if token.tipo == TipoToken.NUMERO_ENTERO:
            self._avanzar()
            return Literal(tipo="entero", valor=token.valor)

        if token.tipo == TipoToken.NUMERO_DECIMAL:
            self._avanzar()
            return Literal(tipo="decimal", valor=token.valor)

        if token.tipo == TipoToken.CADENA_TEXTO:
            self._avanzar()
            return Literal(tipo="expresion", valor=token.valor)

        if token.tipo == TipoToken.CULPABLE:
            self._avanzar()
            return Literal(tipo="declaracion", valor=True)

        if token.tipo == TipoToken.NO_CULPABLE:
            self._avanzar()
            return Literal(tipo="declaracion", valor=False)

        if token.tipo == TipoToken.SIN_PISTA:
            self._avanzar()
            return Literal(tipo="sin_pista", valor=None)

        if token.tipo == TipoToken.RESOLVER:
            return self._parsear_llamada_resolver()

        raise ErrorSintactico(
            tipo="Expresión inválida",
            archivo=self.nombre_archivo,
            linea=token.linea,
            indicio="Parece que falta un valor en alguna expresión.",
            descripcion=(
                f"Se esperaba una expresión pero se encontró {token.tipo.name} "
                f"('{token.lexema}')."
            ),
            causa_posible="Revisa que no falte un valor, identificador o que sobre un símbolo.",
        )

    def _parsear_constructor_tipo(self) -> Literal:
        token_tipo = self._avanzar()
        nombre_tipo = TOKENS_TIPO_LITERAL_CON_VALOR[token_tipo.tipo]

        self._esperar(TipoToken.PARENTESIS_IZQ)
        self._esperar(TipoToken.VALOR)
        self._esperar(TipoToken.DOS_PUNTOS)

        token_valor = self._actual()
        if token_valor.tipo == TipoToken.SIN_PISTA:
            self._avanzar()
            literal = Literal(tipo="sin_pista", valor=None, tipo_declarado=nombre_tipo)
        elif token_valor.tipo == TipoToken.CULPABLE:
            self._avanzar()
            literal = Literal(tipo=nombre_tipo, valor=True)
        elif token_valor.tipo == TipoToken.NO_CULPABLE:
            self._avanzar()
            literal = Literal(tipo=nombre_tipo, valor=False)
        elif token_valor.tipo in (
            TipoToken.NUMERO_ENTERO,
            TipoToken.NUMERO_DECIMAL,
            TipoToken.CADENA_TEXTO,
        ):
            self._avanzar()
            literal = Literal(tipo=nombre_tipo, valor=token_valor.valor)
        else:
            raise ErrorSintactico(
                tipo="Valor literal inválido",
                archivo=self.nombre_archivo,
                linea=token_valor.linea,
                indicio="Parece que un valor escrito dentro de un tipo no es válido.",
                descripcion=(
                    f"Se esperaba un valor literal después de 'valor:' pero se "
                    f"encontró {token_valor.tipo.name} ('{token_valor.lexema}')."
                ),
                causa_posible="Revisa el valor dentro del constructor de tipo.",
            )

        self._esperar(TipoToken.PARENTESIS_DER)
        return literal

    # listas de argumentos

    def _parsear_argumentos(self) -> list:
        argumentos = [self._parsear_expresion()]
        while self._verificar(TipoToken.COMA):
            self._avanzar()
            argumentos.append(self._parsear_expresion())
        return argumentos

    # tipos compuestos: pistas (arreglo) y tablero (matriz)

    def _parsear_pistas_literal(self) -> ListaLiteral:
        self._esperar(TipoToken.PISTAS)
        tipo_elemento = self._esperar_tipo()
        self._esperar(TipoToken.CORCHETE_IZQ)
        elementos = self._parsear_argumentos()
        self._esperar(TipoToken.CORCHETE_DER)
        return ListaLiteral(tipo_elemento=tipo_elemento.lexema, elementos=elementos)

    def _parsear_tablero_literal(self) -> TableroLiteral:
        self._esperar(TipoToken.TABLERO)
        tipo_elemento = self._esperar_tipo()
        self._esperar(TipoToken.CORCHETE_IZQ)
        filas = self._parsear_expresion()
        self._esperar(TipoToken.CORCHETE_DER)
        self._esperar(TipoToken.CORCHETE_IZQ)
        columnas = self._parsear_expresion()
        self._esperar(TipoToken.CORCHETE_DER)
        return TableroLiteral(tipo_elemento=tipo_elemento.lexema, filas=filas, columnas=columnas)

    # acceso por indice

    def _parsear_acceso_indice_opcional(self, base):
        if not self._verificar(TipoToken.CORCHETE_IZQ):
            return base

        indices = []
        while self._verificar(TipoToken.CORCHETE_IZQ):
            self._avanzar()
            indices.append(self._parsear_expresion())
            self._esperar(TipoToken.CORCHETE_DER)
        return AccesoIndice(base=base, indices=indices)