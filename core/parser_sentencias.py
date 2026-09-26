from core.tokens import TipoToken
from core.errors import ErrorSintactico
from core.ast_nodes import DeclaracionPista, Asignacion, Revelar, Consultar


class _SentenciasMixin:
    """Sentencias simples: declaraciones, asignacion, revelar, consultar,
    y el despachador general de sentencias (delega en otros mixins para
    condicionales, ciclos y funciones)."""

    def _parsear_sentencias_hasta(self, *tipos_fin: TipoToken) -> list:
        sentencias = []
        while self._actual().tipo not in tipos_fin and not self._verificar(TipoToken.FIN_DE_ARCHIVO):
            sentencias.append(self._parsear_sentencia())
        return sentencias

    def _parsear_sentencia(self):
        if self._verificar(TipoToken.PISTA) or self._verificar(TipoToken.HECHO):
            return self._parsear_declaracion_pista()
        if self._verificar(TipoToken.IDENTIFICADOR):
            return self._parsear_asignacion()
        if self._verificar(TipoToken.REVELAR):
            return self._parsear_revelar()
        if self._verificar(TipoToken.CONSULTAR):
            return self._parsear_consultar()
        if self._verificar(TipoToken.EVALUAR):
            return self._parsear_evaluar_si()
        if self._verificar(TipoToken.SUCESO):
            return self._parsear_suceso()
        if self._verificar(TipoToken.RASTREAR):
            return self._parsear_rastrear()
        if self._verificar(TipoToken.SEGUIR):
            return self._parsear_seguir_mientras()
        if self._verificar(TipoToken.RESOLVER):
            return self._parsear_resolver()
        if self._verificar(TipoToken.CONCLUIR):
            return self._parsear_concluir()

        raise ErrorSintactico(
            tipo="Sentencia no reconocida",
            archivo=self.nombre_archivo,
            linea=self._actual().linea,
            pista="Hay una instruccion que el parser no reconoce en este punto.",
            descripcion=(
                f"No se esperaba el token {self._actual().tipo.name} "
                f"('{self._actual().lexema}') al inicio de una sentencia."
            ),
            causa_posible="Revisa que la instruccion sea una de las soportadas en este punto.",
        )

    def _parsear_declaracion_pista(self) -> DeclaracionPista:
        token_inicial = self._actual()
        es_constante = token_inicial.tipo == TipoToken.HECHO
        self._avanzar()

        nombre = self._esperar(TipoToken.IDENTIFICADOR)
        self._esperar(TipoToken.IGUAL)
        valor = self._parsear_expresion()
        self._esperar(TipoToken.SELLO)

        return DeclaracionPista(
            nombre=nombre.lexema,
            valor=valor,
            es_constante=es_constante,
            linea=token_inicial.linea,
        )

    def _parsear_asignacion(self) -> Asignacion:
        nombre = self._esperar(TipoToken.IDENTIFICADOR)

        indices = None
        if self._verificar(TipoToken.CORCHETE_IZQ):
            indices = []
            while self._verificar(TipoToken.CORCHETE_IZQ):
                self._avanzar()
                indices.append(self._parsear_expresion())
                self._esperar(TipoToken.CORCHETE_DER)

        self._esperar(TipoToken.IGUAL)
        valor = self._parsear_expresion()
        self._esperar(TipoToken.SELLO)
        return Asignacion(nombre=nombre.lexema, valor=valor, linea=nombre.linea, indices=indices)

    def _parsear_revelar(self) -> Revelar:
        token_revelar = self._esperar(TipoToken.REVELAR)
        self._esperar(TipoToken.PARENTESIS_IZQ)
        argumentos = self._parsear_argumentos()
        self._esperar(TipoToken.PARENTESIS_DER)
        self._esperar(TipoToken.SELLO)
        return Revelar(argumentos=argumentos, linea=token_revelar.linea)

    def _parsear_consultar(self) -> Consultar:
        token_consultar = self._esperar(TipoToken.CONSULTAR)
        self._esperar(TipoToken.PARENTESIS_IZQ)
        variable = self._esperar(TipoToken.IDENTIFICADOR)
        self._esperar(TipoToken.PARENTESIS_DER)
        self._esperar(TipoToken.SELLO)
        return Consultar(variable=variable.lexema, linea=token_consultar.linea)
