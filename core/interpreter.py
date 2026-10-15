from __future__ import annotations

from core.ast_nodes import (
    AccesoIndice,
    Asignacion,
    Concluir,
    Consultar,
    DeclaracionPista,
    EvaluarSi,
    Escena,
    Identificador,
    ListaLiteral,
    Literal,
    OperacionAritmetica,
    OperacionLogica,
    OperacionRelacional,
    Programa,
    Proceso,
    Rastrear,
    Resolver,
    Revelar,
    SeguirMientras,
    Suceso,
    TableroLiteral,
)
from core.errors import ErrorDeEjecucion


class _SenalRetorno(Exception):
    def __init__(self, valor):
        self.valor = valor


class Entorno:
    def __init__(self):
        self._ambitos: list[dict[str, object]] = [{}]

    def entrar_ambito(self) -> None:
        self._ambitos.append({})

    def salir_ambito(self) -> None:
        self._ambitos.pop()

    def declarar(self, nombre: str, valor) -> None:
        self._ambitos[-1][nombre] = valor

    def asignar(self, nombre: str, valor) -> None:
        for ambito in reversed(self._ambitos):
            if nombre in ambito:
                ambito[nombre] = valor
                return
        self._ambitos[0][nombre] = valor

    def obtener(self, nombre: str):
        for ambito in reversed(self._ambitos):
            if nombre in ambito:
                return ambito[nombre]
        raise KeyError(nombre)


class Interprete:
    def __init__(self, programa: Programa):
        self.programa = programa
        self.archivo = programa.archivo_origen
        self.entorno = Entorno()
        self._linea_actual = 0

    def ejecutar(self) -> None:
        for declaracion in self.programa.declaraciones_globales:
            self._ejecutar_sentencia(declaracion, self.entorno)

        self.entorno.entrar_ambito()
        try:
            for sentencia in self.programa.caso_principal.cuerpo:
                self._ejecutar_sentencia(sentencia, self.entorno)
        except _SenalRetorno:
            pass
        finally:
            self.entorno.salir_ambito()

    def _ejecutar_sentencia(self, sentencia, entorno: Entorno) -> None:
        self._linea_actual = getattr(sentencia, "linea", self._linea_actual)

        if isinstance(sentencia, DeclaracionPista):
            valor = self._evaluar(sentencia.valor, entorno)
            entorno.declarar(sentencia.nombre, valor)

        elif isinstance(sentencia, Asignacion):
            valor = self._evaluar(sentencia.valor, entorno)
            if sentencia.indices:
                self._asignar_indexado(sentencia, valor, entorno)
            else:
                entorno.asignar(sentencia.nombre, valor)

        elif isinstance(sentencia, Revelar):
            valores = [self._evaluar(arg, entorno) for arg in sentencia.argumentos]
            print(*[self._formatear(v) for v in valores])

        elif isinstance(sentencia, Consultar):
            entrada = input()
            actual = entorno.obtener(sentencia.variable)
            entorno.asignar(sentencia.variable, self._convertir_entrada(entrada, actual, sentencia))

        elif isinstance(sentencia, Resolver):
            self._llamar_funcion(sentencia)

        elif isinstance(sentencia, Concluir):
            valor = self._evaluar(sentencia.valor, entorno)
            raise _SenalRetorno(valor)

        elif isinstance(sentencia, EvaluarSi):
            self._ejecutar_evaluar_si(sentencia, entorno)

        elif isinstance(sentencia, Suceso):
            self._ejecutar_suceso(sentencia, entorno)

        elif isinstance(sentencia, Rastrear):
            self._ejecutar_rastrear(sentencia, entorno)

        elif isinstance(sentencia, SeguirMientras):
            self._ejecutar_seguir_mientras(sentencia, entorno)

    def _asignar_indexado(self, asignacion: Asignacion, valor, entorno: Entorno) -> None:
        coleccion = entorno.obtener(asignacion.nombre)
        indices = [self._evaluar(indice, entorno) for indice in asignacion.indices]

        for indice in indices[:-1]:
            try:
                coleccion = coleccion[indice]
            except IndexError:
                raise self._error_ejecucion(
                    pista="El índice se sale del rango de la colección.",
                    descripcion=f"Se intentó acceder a la posición {indice} al asignar.",
                    causa="El índice es mayor o igual al tamaño de la lista o tablero.",
                )

        try:
            coleccion[indices[-1]] = valor
        except IndexError:
            raise self._error_ejecucion(
                pista="El índice se sale del rango de la colección.",
                descripcion=f"Se intentó asignar en la posición {indices[-1]}.",
                causa="El índice es mayor o igual al tamaño de la lista o tablero.",
            )

    def _ejecutar_bloque(self, sentencias: list, entorno: Entorno) -> None:
        entorno.entrar_ambito()
        try:
            for sentencia in sentencias:
                self._ejecutar_sentencia(sentencia, entorno)
        finally:
            entorno.salir_ambito()

    def _ejecutar_evaluar_si(self, bloque: EvaluarSi, entorno: Entorno) -> None:
        if self._evaluar(bloque.rama_si.condicion, entorno):
            self._ejecutar_bloque(bloque.rama_si.cuerpo, entorno)
            return

        for rama in bloque.ramas_sino_evaluar:
            if self._evaluar(rama.condicion, entorno):
                self._ejecutar_bloque(rama.cuerpo, entorno)
                return

        if bloque.cuerpo_sino is not None:
            self._ejecutar_bloque(bloque.cuerpo_sino, entorno)

    def _ejecutar_suceso(self, bloque: Suceso, entorno: Entorno) -> None:
        for caso in bloque.casos:
            if self._evaluar(caso.condicion, entorno):
                self._ejecutar_bloque(caso.cuerpo, entorno)
                return

    def _ejecutar_rastrear(self, bloque: Rastrear, entorno: Entorno) -> None:
        inicio = self._evaluar(bloque.desde, entorno)
        limite = self._evaluar(bloque.hasta, entorno)

        entorno.entrar_ambito()
        try:
            paso = 1 if limite >= inicio else -1
            contador = inicio
            while (contador <= limite) if paso == 1 else (contador >= limite):
                entorno.declarar(bloque.variable, contador)
                self._ejecutar_bloque(bloque.cuerpo, entorno)
                contador += paso
        finally:
            entorno.salir_ambito()

    def _ejecutar_seguir_mientras(self, bloque: SeguirMientras, entorno: Entorno) -> None:
        while self._evaluar(bloque.condicion, entorno):
            self._ejecutar_bloque(bloque.cuerpo, entorno)

    def _evaluar(self, expr, entorno: Entorno):
        if isinstance(expr, Literal):
            return expr.valor

        if isinstance(expr, Identificador):
            return entorno.obtener(expr.nombre)

        if isinstance(expr, OperacionAritmetica):
            return self._evaluar_aritmetica(expr, entorno)

        if isinstance(expr, OperacionLogica):
            return self._evaluar_logica(expr, entorno)

        if isinstance(expr, OperacionRelacional):
            return self._evaluar_relacional(expr, entorno)

        if isinstance(expr, ListaLiteral):
            return [self._evaluar(e, entorno) for e in expr.elementos]

        if isinstance(expr, TableroLiteral):
            filas = self._evaluar(expr.filas, entorno)
            columnas = self._evaluar(expr.columnas, entorno)
            valor_inicial = 0 if expr.tipo_elemento == "entero" else 0.0
            return [[valor_inicial for _ in range(columnas)] for _ in range(filas)]

        if isinstance(expr, AccesoIndice):
            return self._evaluar_acceso(expr, entorno)

        if isinstance(expr, Resolver):
            return self._llamar_funcion(expr)

        raise self._error_ejecucion(
            pista="No se pudo evaluar una expresión.",
            descripcion=f"Nodo no reconocido: {type(expr).__name__}.",
            causa="Error interno del intérprete.",
        )

    def _evaluar_aritmetica(self, expr: OperacionAritmetica, entorno: Entorno):
        valores = [self._evaluar(op, entorno) for op in expr.operandos]

        if expr.operador == "conectar":
            resultado = valores[0]
            for v in valores[1:]:
                resultado += v
            return resultado

        if expr.operador == "descartar":
            return valores[0] - valores[1]

        if expr.operador == "intensificar":
            return valores[0] * valores[1]

        if expr.operador == "repartir":
            if valores[1] == 0:
                raise self._error_ejecucion(
                    pista="No se puede repartir entre cero.",
                    descripcion=f"repartir({valores[0]}, {valores[1]}) es indefinido.",
                    causa="El segundo valor de una división es cero.",
                )
            return valores[0] / valores[1]

        raise self._error_ejecucion(
            pista="Operador aritmético desconocido.",
            descripcion=f"'{expr.operador}' no es un operador válido.",
            causa="Error interno del intérprete.",
        )

    def _evaluar_logica(self, expr: OperacionLogica, entorno: Entorno) -> bool:
        izquierda = self._evaluar(expr.izquierda, entorno)

        if expr.operador == "no":
            return not izquierda

        if expr.operador == "y":
            return bool(izquierda and self._evaluar(expr.derecha, entorno))

        if expr.operador == "o":
            return bool(izquierda or self._evaluar(expr.derecha, entorno))

        raise self._error_ejecucion(
            pista="Operador lógico desconocido.",
            descripcion=f"'{expr.operador}' no es un operador válido.",
            causa="Error interno del intérprete.",
        )

    def _evaluar_relacional(self, expr: OperacionRelacional, entorno: Entorno) -> bool:
        izq = self._evaluar(expr.izquierda, entorno)
        der = self._evaluar(expr.derecha, entorno)

        operadores = {
            "==": lambda a, b: a == b,
            "<>": lambda a, b: a != b,
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
        }
        return operadores[expr.operador](izq, der)

    def _evaluar_acceso(self, expr: AccesoIndice, entorno: Entorno):
        valor = self._evaluar(expr.base, entorno)
        for indice_expr in expr.indices:
            indice = self._evaluar(indice_expr, entorno)
            try:
                valor = valor[indice]
            except IndexError:
                raise self._error_ejecucion(
                    pista="El índice se sale del rango de la lista o tablero.",
                    descripcion=f"Se intentó acceder a la posición {indice}.",
                    causa="El índice es mayor o igual al tamaño de la colección.",
                )
        return valor

    def _llamar_funcion(self, llamada: Resolver):
        funcion = self.programa.funciones[llamada.nombre]
        argumentos = [self._evaluar(arg, self.entorno) for arg in llamada.argumentos]

        self.entorno.entrar_ambito()
        try:
            for parametro, valor in zip(funcion.parametros, argumentos):
                self.entorno.declarar(parametro.nombre, valor)

            try:
                for sentencia in funcion.cuerpo:
                    self._ejecutar_sentencia(sentencia, self.entorno)
            except _SenalRetorno as retorno:
                if isinstance(funcion, Proceso):
                    raise self._error_ejecucion(
                        pista=f"'{llamada.nombre}' no debería devolver un valor.",
                        descripcion="Un proceso no puede usar 'concluir'.",
                        causa="Error interno: el semántico debió detectar esto antes.",
                    )
                return retorno.valor

            if isinstance(funcion, Escena):
                raise self._error_ejecucion(
                    pista=f"'{llamada.nombre}' terminó sin 'concluir'.",
                    descripcion="La escena debía devolver un valor y no lo hizo.",
                    causa="Falta un 'concluir' en algún camino de ejecución.",
                )
            return None
        finally:
            self.entorno.salir_ambito()

    def _formatear(self, valor) -> str:
        if valor is True:
            return "culpable"
        if valor is False:
            return "NoCulpable"
        if valor is None:
            return "sin_pista"
        return str(valor)

    def _convertir_entrada(self, texto: str, valor_actual, sentencia):
        """Convierte lo escrito por el usuario al tipo con que se declaro la
        variable (deducido de su valor actual). Si no coincide, es un error de
        ejecucion; asi un 'entero' nunca termina guardando texto."""
        texto = texto.strip()
        nombre = sentencia.variable

        if isinstance(valor_actual, bool):
            if texto == "culpable":
                return True
            if texto == "NoCulpable":
                return False
            raise self._error_ejecucion(
                pista=f"'{nombre}' solo acepta culpable o NoCulpable.",
                descripcion=f"Se escribió '{texto}', pero '{nombre}' es una declaracion (booleano).",
                causa="Escribe exactamente culpable o NoCulpable.",
            )
        if isinstance(valor_actual, int):
            try:
                return int(texto)
            except ValueError:
                raise self._error_ejecucion(
                    pista=f"'{nombre}' espera un número entero.",
                    descripcion=f"Se escribió '{texto}', pero '{nombre}' es un entero.",
                    causa="Escribe un número sin decimales, por ejemplo 25.",
                ) from None
        if isinstance(valor_actual, float):
            try:
                return float(texto)
            except ValueError:
                raise self._error_ejecucion(
                    pista=f"'{nombre}' espera un número decimal.",
                    descripcion=f"Se escribió '{texto}', pero '{nombre}' es un decimal.",
                    causa="Escribe un número, por ejemplo 15.5.",
                ) from None
        if isinstance(valor_actual, str):
            return texto

        # sin_pista: no hay tipo que respetar todavia
        return self._interpretar_entrada(texto)

    def _interpretar_entrada(self, texto: str):
        texto = texto.strip()
        try:
            return int(texto)
        except ValueError:
            pass
        try:
            return float(texto)
        except ValueError:
            pass
        return texto

    def _error_ejecucion(self, pista: str, descripcion: str, causa: str) -> ErrorDeEjecucion:
        return ErrorDeEjecucion(
            tipo="ejecucion",
            archivo=self.archivo,
            linea=self._linea_actual,
            pista=pista,
            descripcion=descripcion,
            causa_posible=causa,
        )


def ejecutar(programa: Programa) -> None:
    Interprete(programa).ejecutar()