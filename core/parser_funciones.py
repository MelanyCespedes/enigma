from core.tokens import TipoToken
from core.ast_nodes import Parametro, Escena, Proceso, Resolver, Concluir


class _FuncionesMixin:

    # definicion de funciones

    def _parsear_parametro(self) -> Parametro:
        nombre = self._esperar(TipoToken.IDENTIFICADOR)
        self._esperar(TipoToken.DOS_PUNTOS)
        tipo = self._esperar_tipo()
        return Parametro(nombre=nombre.lexema, tipo=tipo.lexema)

    def _parsear_parametros(self) -> list:
        parametros = []
        if self._verificar(TipoToken.PARENTESIS_DER):
            return parametros
        parametros.append(self._parsear_parametro())
        while self._verificar(TipoToken.COMA):
            self._avanzar()
            parametros.append(self._parsear_parametro())
        return parametros

    def _parsear_escena(self) -> Escena:
        token_escena = self._esperar(TipoToken.ESCENA)
        nombre = self._esperar(TipoToken.IDENTIFICADOR)
        self._esperar(TipoToken.PARENTESIS_IZQ)
        parametros = self._parsear_parametros()
        self._esperar(TipoToken.PARENTESIS_DER)
        self._esperar(TipoToken.DOS_PUNTOS)
        self._esperar(TipoToken.DOS_PUNTOS)
        tipo_retorno = self._esperar_tipo()
        cuerpo = self._parsear_bloque_inicio_fin()
        return Escena(
            nombre=nombre.lexema,
            parametros=parametros,
            tipo_retorno=tipo_retorno.lexema,
            cuerpo=cuerpo,
            linea=token_escena.linea,
        )

    def _parsear_proceso(self) -> Proceso:
        token_proceso = self._esperar(TipoToken.PROCESO)
        nombre = self._esperar(TipoToken.IDENTIFICADOR)
        self._esperar(TipoToken.PARENTESIS_IZQ)
        parametros = self._parsear_parametros()
        self._esperar(TipoToken.PARENTESIS_DER)
        cuerpo = self._parsear_bloque_inicio_fin()
        return Proceso(
            nombre=nombre.lexema,
            parametros=parametros,
            cuerpo=cuerpo,
            linea=token_proceso.linea,
        )

    # llamada y retorno

    def _parsear_resolver(self) -> Resolver:
        token_resolver = self._esperar(TipoToken.RESOLVER)
        nombre = self._esperar(TipoToken.IDENTIFICADOR)
        self._esperar(TipoToken.PARENTESIS_IZQ)
        argumentos = [] if self._verificar(TipoToken.PARENTESIS_DER) else self._parsear_argumentos()
        self._esperar(TipoToken.PARENTESIS_DER)
        self._esperar(TipoToken.SELLO)
        return Resolver(nombre=nombre.lexema, argumentos=argumentos, linea=token_resolver.linea)

    def _parsear_concluir(self) -> Concluir:
        token_concluir = self._esperar(TipoToken.CONCLUIR)
        valor = self._parsear_expresion()
        self._esperar(TipoToken.SELLO)
        return Concluir(valor=valor, linea=token_concluir.linea)
