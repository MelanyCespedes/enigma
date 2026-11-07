from __future__ import annotations

from core.ast_nodes import (
    AccesoIndice,
    Asignacion,
    CasoSuceso,
    Concluir,
    Consultar,
    DeclaracionPista,
    EvaluarSi,
    Escena,
    Expresion,
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
    recorrer,
)
from core.errors import ErrorSemantico
from core.symbols import TablaSimbolos

TIPOS_NO_OPERABLES = {"expresion", "declaracion", "sin_pista"}
OPERADORES_DE_ORDEN = {">", "<", ">=", "<="}

# Tipo de Python que debe tener el valor de cada literal: entero(valor: 15), etc.
_VALOR_POR_TIPO = {
    "entero": (int,),
    "decimal": (int, float),
    "expresion": (str,),
    "declaracion": (bool,),
}


class AnalizadorSemantico:
    def __init__(self, programa: Programa):
        self.programa = programa
        self.archivo = programa.archivo_origen
        self.tabla = TablaSimbolos(self.archivo)
        self._linea_actual = 0
        self._tipo_retorno: str | None = None

    def analizar(self) -> None:
        self._registrar_funciones()
        self._validar_globales()
        self._validar_funciones()
        self._validar_caso_principal()

    def _registrar_funciones(self) -> None:
        for nombre, funcion in self.programa.funciones.items():
            tipo = "escena" if isinstance(funcion, Escena) else "proceso"
            self.tabla.declarar(nombre, tipo, es_constante=False, linea=funcion.linea)

    def _validar_globales(self) -> None:
        for declaracion in self.programa.declaraciones_globales:
            self._validar_sentencia(declaracion)

    def _validar_funciones(self) -> None:
        for nombre, funcion in self.programa.funciones.items():
            self._usar_archivo(funcion.archivo or self.programa.archivo_origen)
            if isinstance(funcion, Escena) and not any(isinstance(n, Concluir) for n in recorrer(funcion.cuerpo)):
                self._linea_actual = funcion.linea
                raise self._error(
                    indicio="Parece que una escena no entrega el valor que promete.",
                    descripcion=f"La escena '{nombre}' debe devolver '{funcion.tipo_retorno}' y no tiene ningún 'concluir'.",
                    causa="Falta 'concluir' para entregar el valor; si no devuelve nada, debería ser un proceso.",
                )
            self.tabla.entrar_ambito(nombre)
            for parametro in funcion.parametros:
                self.tabla.declarar(parametro.nombre, parametro.tipo, False, funcion.linea)

            self._tipo_retorno = funcion.tipo_retorno if isinstance(funcion, Escena) else None
            self._validar_cuerpo(funcion.cuerpo)
            self._tipo_retorno = None
            self.tabla.salir_ambito()
        self._usar_archivo(self.programa.archivo_origen)

    def _usar_archivo(self, archivo: str) -> None:
        """Los errores se reportan con el archivo de lo que se esta validando
        (una funcion importada puede venir de otro archivo)."""
        self.archivo = archivo
        self.tabla.archivo = archivo

    def _validar_caso_principal(self) -> None:
        caso = self.programa.caso_principal
        self.tabla.entrar_ambito(caso.nombre)
        self._validar_cuerpo(caso.cuerpo)
        self.tabla.salir_ambito()

    def _validar_cuerpo(self, sentencias: list) -> None:
        for sentencia in sentencias:
            self._validar_sentencia(sentencia)

    def _validar_sentencia(self, sentencia) -> None:
        self._linea_actual = getattr(sentencia, "linea", self._linea_actual)

        if isinstance(sentencia, DeclaracionPista):
            self._validar_declaracion(sentencia)
        elif isinstance(sentencia, Asignacion):
            self._validar_asignacion(sentencia)
        elif isinstance(sentencia, Revelar):
            for argumento in sentencia.argumentos:
                self._tipo_de(argumento)
        elif isinstance(sentencia, Consultar):
            self._validar_consultar(sentencia)
        elif isinstance(sentencia, Resolver):
            self._validar_llamada(sentencia)
        elif isinstance(sentencia, Concluir):
            self._validar_concluir(sentencia)
        elif isinstance(sentencia, EvaluarSi):
            self._validar_evaluar_si(sentencia)
        elif isinstance(sentencia, Suceso):
            self._validar_suceso(sentencia)
        elif isinstance(sentencia, Rastrear):
            self._validar_rastrear(sentencia)
        elif isinstance(sentencia, SeguirMientras):
            self._validar_seguir_mientras(sentencia)

    def _validar_declaracion(self, decl: DeclaracionPista) -> None:
        tipo = self._tipo_de(decl.valor)
        declarado = decl.valor.tipo_declarado if isinstance(decl.valor, Literal) else ""
        self.tabla.declarar(decl.nombre, tipo, decl.es_constante, decl.linea, declarado)

    # ---------- Asignacion (simple e indexada) ----------

    def _validar_asignacion(self, asig: Asignacion) -> None:
        simbolo = self._buscar_variable(asig.nombre)

        if asig.indices is not None:
            self._validar_asignacion_indexada(asig, simbolo)
            return

        if simbolo.es_constante:
            raise self._error(
                indicio="Parece que intentas cambiar algo que debía quedar fijo.",
                descripcion=f"'{asig.nombre}' fue declarada con 'hecho' en la línea {simbolo.linea}.",
                causa="Se intentó reasignar una constante.",
            )

        tipo_valor = self._tipo_de(asig.valor)
        if simbolo.tipo == "sin_pista" and tipo_valor != "sin_pista":
            self._dar_valor_a_sin_pista(simbolo, tipo_valor, asig.nombre)
        if not self._compatible(simbolo.tipo, tipo_valor):
            raise self._error(
                indicio="Parece que le das a una pista un valor de otro tipo.",
                descripcion=f"'{asig.nombre}' es de tipo '{simbolo.tipo}' pero se le asignó '{tipo_valor}'.",
                causa="La expresión que se asigna no es compatible con el tipo de la variable.",
            )

    def _validar_asignacion_indexada(self, asig: Asignacion, simbolo) -> None:
        if simbolo.es_constante:
            raise self._error(
                indicio="Parece que intentas cambiar algo que debía quedar fijo.",
                descripcion=f"'{asig.nombre}' fue declarada con 'hecho' en la línea {simbolo.linea}.",
                causa="Se intentó modificar una celda de una constante.",
            )

        if not (simbolo.tipo.startswith("pistas:") or simbolo.tipo.startswith("tablero:")):
            raise self._error(
                indicio="Parece que tratas como lista o tablero algo que no lo es.",
                descripcion=f"Solo se puede usar [] sobre 'pistas' o 'tablero'; '{asig.nombre}' es '{simbolo.tipo}'.",
                causa="Se usaron corchetes sobre una variable que no es una colección.",
            )

        for indice in asig.indices:
            if self._tipo_de(indice) != "entero":
                raise self._error(
                    indicio="Los índices deben ser enteros.",
                    descripcion="Un índice usado en la asignación no es de tipo 'entero'.",
                    causa="Se usó un decimal o un texto como posición.",
                )

        tipo_elemento = simbolo.tipo.split(":", 1)[1]
        tipo_valor = self._tipo_de(asig.valor)
        if not self._compatible(tipo_elemento, tipo_valor):
            raise self._error(
                indicio="Parece que un valor no coincide con el tipo de los elementos de una lista.",
                descripcion=f"Los elementos de '{asig.nombre}' son de tipo '{tipo_elemento}' pero se asignó '{tipo_valor}'.",
                causa="Tipo incompatible al asignar una celda.",
            )

    def _validar_consultar(self, consulta: Consultar) -> None:
        simbolo = self._buscar_variable(consulta.variable)
        if simbolo.tipo == "sin_pista" and simbolo.tipo_declarado:
            simbolo.tipo = simbolo.tipo_declarado  # consultar le dara un valor
        if simbolo.es_constante:
            raise self._error(
                indicio="Parece que quieres guardar un dato en algo que debía quedar fijo.",
                descripcion=f"'{consulta.variable}' es una constante y no acepta nuevos valores.",
                causa="Se usó 'consultar' sobre una variable declarada con 'hecho'.",
            )

    def _validar_llamada(self, llamada: Resolver) -> None:
        funcion = self.programa.funciones.get(llamada.nombre)
        if funcion is None:
            raise self._error(
                indicio="Parece que llamas a una función que no existe.",
                descripcion=f"No existe ninguna escena o proceso llamado '{llamada.nombre}'.",
                causa="Nombre mal escrito o función no definida.",
            )

        if len(llamada.argumentos) != len(funcion.parametros):
            raise self._error(
                indicio="Parece que una función recibe más o menos datos de los que espera.",
                descripcion=f"'{llamada.nombre}' espera {len(funcion.parametros)} argumento(s) pero se enviaron {len(llamada.argumentos)}.",
                causa="La cantidad de argumentos no coincide con los parámetros de la función.",
            )

        for argumento, parametro in zip(llamada.argumentos, funcion.parametros):
            tipo_arg = self._tipo_de(argumento)
            if not self._compatible(parametro.tipo, tipo_arg):
                raise self._error(
                    indicio="Parece que un dato enviado a una función no es del tipo que espera.",
                    descripcion=f"El parámetro '{parametro.nombre}' espera '{parametro.tipo}' pero se envió '{tipo_arg}'.",
                    causa="Tipo de argumento incompatible con el parámetro.",
                )

    def _validar_concluir(self, concluir: Concluir) -> None:
        if self._tipo_retorno is None:
            raise self._error(
                indicio="'concluir' solo puede usarse dentro de una escena.",
                descripcion="Se encontró 'concluir' fuera de una escena o dentro de un proceso.",
                causa="Un proceso no devuelve valor; solo las escenas pueden usar 'concluir'.",
            )

        tipo_valor = self._tipo_de(concluir.valor)
        if not self._compatible(self._tipo_retorno, tipo_valor):
            raise self._error(
                indicio="El valor devuelto no coincide con el tipo de la escena.",
                descripcion=f"La escena devuelve '{self._tipo_retorno}' pero se concluyó con '{tipo_valor}'.",
                causa="Tipo de retorno incompatible.",
            )

    def _validar_evaluar_si(self, bloque: EvaluarSi) -> None:
        self._validar_condicion(bloque.rama_si.condicion)
        self._validar_bloque_en_ambito("evaluar si", bloque.rama_si.cuerpo)

        for rama in bloque.ramas_sino_evaluar:
            self._validar_condicion(rama.condicion)
            self._validar_bloque_en_ambito("sino evaluar", rama.cuerpo)

        if bloque.cuerpo_sino is not None:
            self._validar_bloque_en_ambito("sino", bloque.cuerpo_sino)

    def _validar_suceso(self, bloque: Suceso) -> None:
        self._tipo_de(bloque.variable)
        for caso in bloque.casos:
            self._validar_condicion(caso.condicion)
            self._validar_bloque_en_ambito(f"suceso {caso.numero}", caso.cuerpo)

    def _validar_rastrear(self, bloque: Rastrear) -> None:
        for limite in (bloque.desde, bloque.hasta):
            if self._tipo_de(limite) != "entero":
                raise self._error(
                    indicio="Los límites de 'rastrear' deben ser enteros.",
                    descripcion=f"El límite es de tipo '{self._tipo_de(limite)}'.",
                    causa="Un decimal no puede usarse como contador de un ciclo 'rastrear'.",
                )

        self.tabla.entrar_ambito("rastrear")
        self.tabla.declarar(bloque.variable, "entero", es_constante=False, linea=bloque.linea)
        self._validar_cuerpo(bloque.cuerpo)
        self.tabla.salir_ambito()

    def _validar_seguir_mientras(self, bloque: SeguirMientras) -> None:
        self._validar_condicion(bloque.condicion)
        self._validar_bloque_en_ambito("seguir mientras", bloque.cuerpo)

    def _validar_condicion(self, condicion) -> None:
        tipo = self._tipo_de(condicion)
        if tipo != "declaracion":
            raise self._error(
                indicio="Una condición debe ser verdadera o falsa.",
                descripcion=f"La condición produce un valor de tipo '{tipo}', no 'declaracion'.",
                causa="Se usó un valor que no es lógico como condición.",
            )

    def _validar_bloque_en_ambito(self, nombre: str, sentencias: list) -> None:
        self.tabla.entrar_ambito(nombre)
        self._validar_cuerpo(sentencias)
        self.tabla.salir_ambito()

    def _validar_literal(self, literal: Literal) -> None:
        """El valor entre parentesis debe corresponder al tipo: entero(valor: 1.5)
        o expresion(valor: 3) son errores."""
        esperados = _VALOR_POR_TIPO.get(literal.tipo)
        if esperados is None:
            return
        valor = literal.valor
        es_bool = isinstance(valor, bool)
        correcto = isinstance(valor, esperados) and (es_bool == (literal.tipo == "declaracion"))
        if correcto:
            return
        detalle = {
            "entero": "un número sin decimales",
            "decimal": "un número",
            "expresion": "un texto entre comillas simples",
            "declaracion": "culpable o NoCulpable",
        }[literal.tipo]
        raise self._error(
            indicio="Parece que un valor no corresponde al tipo con que lo declaraste.",
            descripcion=f"'{literal.tipo}' espera {detalle}, pero se escribió {valor!r}.",
            causa=f"Revisa el valor dentro de {literal.tipo}(valor: ...).",
        )

    def _tipo_de(self, expr: Expresion) -> str:
        if isinstance(expr, Literal):
            self._validar_literal(expr)
            return expr.tipo

        if isinstance(expr, Identificador):
            return self._buscar_variable(expr.nombre).tipo

        if isinstance(expr, OperacionAritmetica):
            return self._tipo_aritmetico(expr)

        if isinstance(expr, OperacionLogica):
            self._validar_condicion(expr.izquierda)
            if expr.derecha is not None:
                self._validar_condicion(expr.derecha)
            return "declaracion"

        if isinstance(expr, OperacionRelacional):
            tipo_izq = self._tipo_de(expr.izquierda)
            tipo_der = self._tipo_de(expr.derecha)
            if expr.operador in OPERADORES_DE_ORDEN:
                for tipo in (tipo_izq, tipo_der):
                    if tipo in TIPOS_NO_OPERABLES:
                        raise self._error(
                            indicio="Parece que comparas por orden valores que no se pueden ordenar.",
                            descripcion=(
                                f"'{expr.operador}' solo compara 'entero' y 'decimal'; "
                                f"se encontró '{tipo}'."
                            ),
                            causa="Los textos y las declaraciones solo se comparan con == y <>.",
                        )
            if not (self._compatible(tipo_izq, tipo_der) or self._compatible(tipo_der, tipo_izq)):
                raise self._error(
                    indicio="Solo se pueden comparar valores del mismo tipo.",
                    descripcion=f"Se comparó '{tipo_izq}' con '{tipo_der}'.",
                    causa="Comparación entre tipos incompatibles.",
                )
            return "declaracion"

        if isinstance(expr, ListaLiteral):
            for elemento in expr.elementos:
                tipo_elemento = self._tipo_de(elemento)
                if not self._compatible(expr.tipo_elemento, tipo_elemento):
                    raise self._error(
                        indicio="Una lista no puede mezclar tipos de datos.",
                        descripcion=(
                            f"La lista es de '{expr.tipo_elemento}' pero tiene un elemento "
                            f"de tipo '{tipo_elemento}'."
                        ),
                        causa="Todos los elementos de una lista deben ser del mismo tipo.",
                    )
            return f"pistas:{expr.tipo_elemento}"

        if isinstance(expr, TableroLiteral):
            return f"tablero:{expr.tipo_elemento}"

        if isinstance(expr, AccesoIndice):
            return self._tipo_de_acceso(expr)

        if isinstance(expr, Resolver):
            return self._tipo_de_llamada(expr)

        raise self._error(
            indicio="Expresión no reconocida.",
            descripcion=f"El nodo '{type(expr).__name__}' no es una expresión válida.",
            causa="Error interno del parser o del árbol.",
        )

    def _tipo_de_llamada(self, llamada: Resolver) -> str:
        """Permite usar 'resolver Nombre(...)' dentro de una expresión,
        una vez que el parser lo soporte (ver nota de integración)."""
        self._validar_llamada(llamada)
        funcion = self.programa.funciones[llamada.nombre]
        if isinstance(funcion, Proceso):
            raise self._error(
                indicio="Parece que usas como valor algo que no devuelve nada.",
                descripcion=f"'{llamada.nombre}' es un proceso y un proceso no puede usarse dentro de una expresión.",
                causa="Se intentó usar el resultado de un proceso como si fuera un valor.",
            )
        return funcion.tipo_retorno

    def _tipo_aritmetico(self, expr: OperacionAritmetica) -> str:
        tipos = [self._tipo_de(operando) for operando in expr.operandos]

        for tipo in tipos:
            if tipo in TIPOS_NO_OPERABLES:
                raise self._error(
                    indicio="Parece que operas con un valor que no es un número.",
                    descripcion=f"No se puede aplicar '{expr.operador}' a un valor de tipo '{tipo}': solo 'entero' y 'decimal' participan en operaciones aritméticas.",
                    causa="Se usó un valor no numérico en una operación.",
                )

        if expr.operador in ("descartar", "intensificar", "repartir") and len(tipos) != 2:
            raise self._error(
                indicio="Parece que a una operación le faltan o le sobran valores.",
                descripcion=f"'{expr.operador}' necesita exactamente dos valores y se enviaron {len(tipos)}.",
                causa="Cantidad incorrecta de argumentos en una operación.",
            )

        if expr.operador == "repartir":
            return "decimal"

        return "decimal" if "decimal" in tipos else "entero"

    def _tipo_de_acceso(self, expr: AccesoIndice) -> str:
        tipo_base = self._tipo_de(expr.base)
        if not (tipo_base.startswith("pistas:") or tipo_base.startswith("tablero:")):
            raise self._error(
                indicio="Solo las listas y tableros se pueden indexar.",
                descripcion=f"Se intentó indexar un valor de tipo '{tipo_base}'.",
                causa="Uso de [] sobre una variable que no es lista ni tablero.",
            )

        for indice in expr.indices:
            if self._tipo_de(indice) != "entero":
                raise self._error(
                    indicio="Los índices deben ser enteros.",
                    descripcion="Un índice no es de tipo 'entero'.",
                    causa="Se usó un decimal o un texto como posición.",
                )

        return tipo_base.split(":", 1)[1]

    def _buscar_variable(self, nombre: str):
        simbolo = self.tabla.buscar(nombre)
        if simbolo is None:
            raise self._error(
                indicio="Parece que usas algo que no declaraste.",
                descripcion=f"No se encontró ninguna variable llamada '{nombre}' en este alcance.",
                causa="Falta declarar la variable con 'pista' o 'hecho', o el nombre está mal escrito.",
            )
        return simbolo

    def _dar_valor_a_sin_pista(self, simbolo, tipo_valor: str, nombre: str) -> None:
        """Una pista nacida como 'entero(valor: sin_pista)' pasa a ser un 'entero'
        al recibir su primer valor (que debe ser compatible con lo declarado)."""
        if simbolo.tipo_declarado and not self._compatible(simbolo.tipo_declarado, tipo_valor):
            raise self._error(
                indicio="Parece que le das a una pista un valor de otro tipo.",
                descripcion=(
                    f"'{nombre}' se declaró como '{simbolo.tipo_declarado}' pero se le asignó '{tipo_valor}'."
                ),
                causa="Se asignó un valor de otro tipo a una pista declarada sin valor inicial.",
            )
        simbolo.tipo = simbolo.tipo_declarado or tipo_valor

    def _compatible(self, destino: str, origen: str) -> bool:
        if origen == "sin_pista":
            return True
        if destino == origen:
            return True
        if destino == "decimal" and origen == "entero":
            return True
        if destino in ("pistas", "tablero") and origen.startswith(destino + ":"):
            return True
        return False

    def _error(self, indicio: str, descripcion: str, causa: str) -> ErrorSemantico:
        return ErrorSemantico(
            tipo="semántica",
            archivo=self.archivo,
            linea=self._linea_actual,
            indicio=indicio,
            descripcion=descripcion,
            causa_posible=causa,
        )


def analizar(programa: Programa) -> None:
    AnalizadorSemantico(programa).analizar()