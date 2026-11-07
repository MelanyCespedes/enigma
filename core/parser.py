from core.tokens import Token, TipoToken
from core.errors import ErrorSintactico
from core.ast_nodes import Programa, CasoPrincipal, Importacion, DeclaracionPista
from core.parser_base import _ParserBase
from core.parser_expresiones import _ExpresionesMixin
from core.parser_sentencias import _SentenciasMixin
from core.parser_control import _ControlMixin
from core.parser_funciones import _FuncionesMixin


def parsear(tokens: list[Token], nombre_archivo: str) -> Programa:
    analizador = _Parser(tokens, nombre_archivo)
    return analizador.parsear_programa()


class _Parser(_ParserBase, _SentenciasMixin, _ExpresionesMixin, _ControlMixin, _FuncionesMixin):

    # punto de entrada

    def parsear_programa(self) -> Programa:
        importaciones: list[Importacion] = []
        declaraciones_globales: list[DeclaracionPista] = []
        funciones: dict = {}

        while self._verificar(TipoToken.NUMERAL):
            importaciones.append(self._parsear_importacion())

        while self._verificar(TipoToken.PISTA) or self._verificar(TipoToken.HECHO):
            declaraciones_globales.append(self._parsear_declaracion_pista())

        while self._verificar(TipoToken.ESCENA) or self._verificar(TipoToken.PROCESO):
            funcion = self._parsear_escena() if self._verificar(TipoToken.ESCENA) else self._parsear_proceso()
            if funcion.nombre in funciones:
                raise ErrorSintactico(
                    tipo="Función duplicada",
                    archivo=self.nombre_archivo,
                    linea=funcion.linea,
                    indicio="Parece que dos funciones tienen el mismo nombre.",
                    descripcion=f"La función '{funcion.nombre}' está declarada más de una vez en {self.nombre_archivo}.",
                    causa_posible="Revisa que no hayas repetido el nombre de una escena/proceso.",
                )
            funciones[funcion.nombre] = funcion

        caso_principal = self._parsear_caso_principal()
        self._esperar(TipoToken.FIN_DE_ARCHIVO)

        return Programa(
            importaciones=importaciones,
            declaraciones_globales=declaraciones_globales,
            funciones=funciones,
            caso_principal=caso_principal,
            archivo_origen=self.nombre_archivo,
        )

    # importaciones

    def _parsear_importacion(self) -> Importacion:
        token_numeral = self._esperar(TipoToken.NUMERAL)
        self._esperar(TipoToken.EXPEDIENTE)
        ruta = self._esperar(TipoToken.RUTA_ARCHIVO)
        return Importacion(archivo=ruta.lexema, linea=token_numeral.linea)

    # caso principal

    def _parsear_caso_principal(self) -> CasoPrincipal:
        token_caso = self._esperar(TipoToken.CASO)
        nombre = self._esperar(TipoToken.IDENTIFICADOR)
        self._esperar(TipoToken.ABIERTO)

        cuerpo = self._parsear_sentencias_hasta(TipoToken.CASO)

        self._esperar(TipoToken.CASO)
        nombre_cierre = self._esperar(TipoToken.IDENTIFICADOR)
        if nombre_cierre.lexema != nombre.lexema:
            raise ErrorSintactico(
                tipo="Nombre de caso no coincide",
                archivo=self.nombre_archivo,
                linea=nombre_cierre.linea,
                indicio="El nombre del caso al cerrar debe ser igual al de la apertura.",
                descripcion=(
                    f"El caso se abrió como '{nombre.lexema}' pero se cierra "
                    f"como '{nombre_cierre.lexema}'."
                ),
                causa_posible="Revisa que el nombre del caso sea el mismo en la apertura y el cierre.",
            )
        self._esperar(TipoToken.CERRADO)
        self._esperar(TipoToken.SELLO)

        return CasoPrincipal(nombre=nombre.lexema, cuerpo=cuerpo, linea=token_caso.linea)