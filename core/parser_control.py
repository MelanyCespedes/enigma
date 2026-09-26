from core.tokens import TipoToken
from core.errors import ErrorSintactico
from core.ast_nodes import (
    RamaCondicional,
    EvaluarSi,
    CasoSuceso,
    Suceso,
    Rastrear,
    SeguirMientras,
)


class _ControlMixin:

    def _parsear_bloque_inicio_fin(self) -> list:
        self._esperar(TipoToken.INICIO)
        cuerpo = self._parsear_sentencias_hasta(TipoToken.FIN)
        self._esperar(TipoToken.FIN)
        self._esperar(TipoToken.SELLO)
        return cuerpo

    # condicionales

    def _parsear_evaluar_si(self) -> EvaluarSi:
        token_evaluar = self._esperar(TipoToken.EVALUAR)
        self._esperar(TipoToken.SI)
        self._esperar(TipoToken.PARENTESIS_IZQ)
        condicion = self._parsear_expresion()
        self._esperar(TipoToken.PARENTESIS_DER)
        cuerpo = self._parsear_bloque_inicio_fin()
        rama_si = RamaCondicional(condicion=condicion, cuerpo=cuerpo)

        ramas_sino_evaluar = []
        cuerpo_sino = None

        while self._verificar(TipoToken.SINO):
            self._avanzar()

            if self._verificar(TipoToken.EVALUAR):
                self._avanzar()
                self._esperar(TipoToken.PARENTESIS_IZQ)
                condicion_rama = self._parsear_expresion()
                self._esperar(TipoToken.PARENTESIS_DER)
                cuerpo_rama = self._parsear_bloque_inicio_fin()
                ramas_sino_evaluar.append(RamaCondicional(condicion=condicion_rama, cuerpo=cuerpo_rama))
                continue

            if self._verificar(TipoToken.INICIO):
                cuerpo_sino = self._parsear_bloque_inicio_fin()
                break

            raise ErrorSintactico(
                tipo="Token inesperado despues de sino",
                archivo=self.nombre_archivo,
                linea=self._actual().linea,
                pista="Despues de 'sino' se esperaba 'evaluar' o 'inicio'.",
                descripcion=(
                    f"Se esperaba EVALUAR o INICIO despues de 'sino' pero se "
                    f"encontro {self._actual().tipo.name} ('{self._actual().lexema}')."
                ),
                causa_posible="Revisa que la rama 'sino' tenga la forma 'sino evaluar (...) inicio...fin!' o 'sino inicio...fin!'.",
            )

        return EvaluarSi(
            rama_si=rama_si,
            ramas_sino_evaluar=ramas_sino_evaluar,
            cuerpo_sino=cuerpo_sino,
            linea=token_evaluar.linea,
        )

    def _parsear_suceso(self) -> Suceso:
        token_suceso = self._esperar(TipoToken.SUCESO)
        self._esperar(TipoToken.PARENTESIS_IZQ)
        variable = self._parsear_expresion()
        self._esperar(TipoToken.PARENTESIS_DER)
        self._esperar(TipoToken.INICIO)

        casos = []
        while self._verificar(TipoToken.NUMERO_ENTERO):
            token_numero = self._avanzar()
            self._esperar(TipoToken.PARENTESIS_IZQ)
            condicion = self._parsear_expresion()
            self._esperar(TipoToken.PARENTESIS_DER)
            self._esperar(TipoToken.DOS_PUNTOS)
            cuerpo = self._parsear_sentencias_hasta(TipoToken.NUMERO_ENTERO, TipoToken.FIN)
            casos.append(CasoSuceso(numero=token_numero.valor, condicion=condicion, cuerpo=cuerpo))

        self._esperar(TipoToken.FIN)
        self._esperar(TipoToken.SELLO)
        return Suceso(variable=variable, casos=casos, linea=token_suceso.linea)

    # ciclos

    def _parsear_rastrear(self) -> Rastrear:
        token_rastrear = self._esperar(TipoToken.RASTREAR)
        variable = self._esperar(TipoToken.IDENTIFICADOR)
        self._esperar(TipoToken.DESDE)
        desde = self._parsear_expresion()
        self._esperar(TipoToken.HASTA)
        hasta = self._parsear_expresion()
        cuerpo = self._parsear_bloque_inicio_fin()
        return Rastrear(
            variable=variable.lexema,
            desde=desde,
            hasta=hasta,
            cuerpo=cuerpo,
            linea=token_rastrear.linea,
        )

    def _parsear_seguir_mientras(self) -> SeguirMientras:
        token_seguir = self._esperar(TipoToken.SEGUIR)
        self._esperar(TipoToken.MIENTRAS)
        self._esperar(TipoToken.PARENTESIS_IZQ)
        condicion = self._parsear_expresion()
        self._esperar(TipoToken.PARENTESIS_DER)
        cuerpo = self._parsear_bloque_inicio_fin()
        return SeguirMientras(condicion=condicion, cuerpo=cuerpo, linea=token_seguir.linea)
