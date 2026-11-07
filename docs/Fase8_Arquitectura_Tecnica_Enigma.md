# Enigma — Fase 8: Arquitectura Técnica (Python)

Este documento describe la arquitectura del compilador/intérprete de Enigma en Python, basado en el diseño de palabras reservadas y semántica del proyecto. Nació como plano previo a programar y **ya está actualizado con lo implementado**: donde el código difiere del plano original, el texto indica lo que se hizo. Lo que sigue pendiente aparece marcado como **Pendiente**.

---

## 1. Decisión general: intérprete de árbol (tree-walking interpreter)

Para un proyecto de curso con tiempo limitado, la arquitectura clásica de 5 etapas es la más segura y la más fácil de explicar en la defensa (sección F de la rúbrica pide justificar decisiones técnicas):

1. **Analizador léxico (Lexer):** texto → lista de tokens.
2. **Analizador sintáctico (Parser):** tokens → árbol de sintaxis abstracta (AST), usando **descenso recursivo** (recursive descent) — es el método que se enseña en el curso y es el más fácil de depurar en vivo si el profesor pide "modificar una funcionalidad" en la defensa.
3. **Analizador semántico:** recorre el AST, construye tablas de símbolos, valida tipos, alcances, duplicados e importaciones circulares.
4. **Resolución de módulos:** antes del análisis semántico, resuelve todas las directivas `#expediente` y arma un solo AST global.
5. **Intérprete (tree-walking):** recorre el AST ya validado y ejecuta cada nodo directamente (sin generar bytecode ni código máquina — más simple y suficiente para el alcance del curso).

No se necesita generar código intermedio ni una máquina virtual — eso sería sobre-ingeniería para lo que pide la rúbrica.

---

## 2. Analizador léxico — diseño de tokens

Tabla completa de tipos de token, extraída directamente de tu tabla de palabras reservadas:

```python
from enum import Enum, auto

class TipoToken(Enum):
    # Declaraciones
    PISTA = auto()
    HECHO = auto()
    VALOR = auto()

    # Programa principal
    CASO = auto()
    ABIERTO = auto()
    CERRADO = auto()

    # Entrada/salida
    REVELAR = auto()
    CONSULTAR = auto()

    # Condicionales
    EVALUAR = auto()
    SI = auto()
    SINO = auto()
    SUCESO = auto()

    # Bloques
    INICIO = auto()
    FIN = auto()

    # Ciclos
    RASTREAR = auto()
    DESDE = auto()
    HASTA = auto()
    SEGUIR = auto()
    MIENTRAS = auto()

    # Funciones
    ESCENA = auto()
    PROCESO = auto()
    RESOLVER = auto()
    CONCLUIR = auto()

    # Aritmética
    CONECTAR = auto()      # suma
    DESCARTAR = auto()     # resta
    INTENSIFICAR = auto()  # multiplicación
    REPARTIR = auto()      # división

    # Lógicos
    O = auto()
    Y = auto()
    NO = auto()

    # Tipos
    ENTERO = auto()
    DECIMAL = auto()
    EXPRESION = auto()
    DECLARACION = auto()   # tipo booleano (revisar si se renombra a VEREDICTO)
    PISTAS = auto()        # lista
    TABLERO = auto()       # matriz

    # Valores literales especiales
    CULPABLE = auto()
    NO_CULPABLE = auto()
    SIN_PISTA = auto()

    # Literales e identificadores
    IDENTIFICADOR = auto()
    NUMERO_ENTERO = auto()
    NUMERO_DECIMAL = auto()
    CADENA_TEXTO = auto()

    # Operadores relacionales
    IGUAL_IGUAL = auto()      # ==
    DIFERENTE = auto()        # <>
    MAYOR = auto()            # >
    MENOR = auto()            # <
    MAYOR_IGUAL = auto()      # >=
    MENOR_IGUAL = auto()      # <=

    # Símbolos
    IGUAL = auto()             # =  (asignación)
    PARENTESIS_IZQ = auto()    # (
    PARENTESIS_DER = auto()    # )
    CORCHETE_IZQ = auto()      # [
    CORCHETE_DER = auto()      # ]
    DOS_PUNTOS = auto()        # :
    COMA = auto()              # ,
    SELLO = auto()             # !  (terminador de instrucción)
    NUMERAL = auto()           # #  (inicio de importación)
    RUTA_ARCHIVO = auto()      # <archivo.eng>  (token especial, ver 2.1)

    FIN_DE_ARCHIVO = auto()

# Los comentarios { ... } no generan token: el lexer los descarta (conservando el conteo
# de líneas y columnas). Una '{' sin '}' o una '}' suelta lanza ErrorLexico.

@dataclass
class Token:
    tipo: TipoToken
    lexema: str
    valor: object       # valor ya convertido (int, float, str, None)
    linea: int
    columna: int
```

### 2.1 Caso especial: `#expediente <archivo.eng>`

El símbolo `#` activa un **modo especial del lexer**: en vez de tokenizar `<` y `>` como operadores relacionales, el lexer entra en "modo importación" y lee todo el contenido entre `<` y `>` como un solo token `RUTA_ARCHIVO`. Esto es exactamente como funciona `#include <archivo.h>` en C, así que es un patrón bien conocido y fácil de justificar en la defensa.

### 2.2 Caso resuelto: `!` vs `<>`

Como ya decidieron usar `<>` para "diferente" en vez de `!=`, el lexer no tiene ambigüedad: `!` **siempre** es `SELLO` (terminador), sin necesidad de lookahead. Esto simplifica mucho el lexer.

---

## 3. Analizador sintáctico — gramática simplificada (EBNF)

```ebnf
programa        ::= (importacion)* (declaracion_global)* (funcion)* caso_principal

importacion     ::= "#" "expediente" RUTA_ARCHIVO

caso_principal  ::= "caso" IDENTIFICADOR "abierto" sentencia* "caso" IDENTIFICADOR "cerrado" "!"

funcion         ::= escena | proceso
escena          ::= "escena" IDENTIFICADOR "(" parametros? ")" "::" tipo "inicio" sentencia* "fin" "!"
proceso         ::= "proceso" IDENTIFICADOR "(" parametros? ")" "inicio" sentencia* "fin" "!"
parametros      ::= parametro ("," parametro)*
parametro       ::= IDENTIFICADOR ":" IDENTIFICADOR

sentencia       ::= declaracion_pista
                  | asignacion
                  | revelar_stmt
                  | consultar_stmt
                  | evaluar_si
                  | suceso_stmt
                  | rastrear_stmt
                  | seguir_mientras
                  | resolver_stmt
                  | concluir_stmt

declaracion_pista ::= ("pista" | "hecho") IDENTIFICADOR "=" expresion "!"
asignacion        ::= IDENTIFICADOR "=" expresion "!"
revelar_stmt      ::= "revelar" "(" argumentos ")" "!"
consultar_stmt    ::= "consultar" "(" IDENTIFICADOR ")" "!"

evaluar_si   ::= "evaluar" "si" "(" expresion ")" "inicio" sentencia* "fin" "!"
                 ("sino" "evaluar" "(" expresion ")" "inicio" sentencia* "fin" "!")*
                 ("sino" "inicio" sentencia* "fin" "!")?

suceso_stmt  ::= "suceso" "(" expresion ")" "inicio"
                 (NUMERO_ENTERO "(" expresion ")" ":" sentencia*)*
                 "fin" "!"

rastrear_stmt     ::= "rastrear" IDENTIFICADOR "desde" expresion "hasta" expresion "inicio" sentencia* "fin" "!"
seguir_mientras   ::= "seguir" "mientras" "(" expresion ")" "inicio" sentencia* "fin" "!"

resolver_stmt     ::= "resolver" IDENTIFICADOR "(" argumentos? ")" "!"
concluir_stmt     ::= "concluir" expresion "!"

expresion         ::= expr_logica
expr_logica       ::= expr_relacional (("y" | "o") expr_relacional)* | "no" "(" expresion ")"
expr_relacional   ::= expr_aritmetica (("==" | "<>" | ">" | "<" | ">=" | "<=") expr_aritmetica)?
expr_aritmetica   ::= "conectar" "(" argumentos ")"
                    | "descartar" "(" expresion "," expresion ")"
                    | "intensificar" "(" expresion "," expresion ")"
                    | "repartir" "(" expresion "," expresion ")"
                    | constructor_tipo | IDENTIFICADOR | acceso_indice

constructor_tipo  ::= ("entero"|"decimal"|"expresion"|"declaracion") "(" "valor" ":" valor_literal ")"
                    | "pistas" IDENTIFICADOR "[" lista_valores "]"
                    | "tablero" IDENTIFICADOR "[" expresion "]" "[" expresion "]"

acceso_indice     ::= IDENTIFICADOR "[" expresion "]" ("[" expresion "]")?
argumentos        ::= expresion ("," expresion)*
```

**Decisión tomada:** **todo** `fin` lleva `!` (incluidos los `fin` intermedios de `sino evaluar`) y también `caso X cerrado!`, tal como dice la sección 5.4 del documento de diseño. Es uniforme, simplifica el parser y es lo que implementa `core/parser*.py`. La tabla de palabras reservadas del `.docx` escribe algunos ejemplos sin `!`; hay que corregirlos para que coincidan con el lenguaje.

**Listas:** la sintaxis vigente es `pistas entero[2, 4, 6]` (la tabla de tipos del `.docx` todavía dice `lista entero(2, 4, 6)`; también se debe corregir).

---

## 4. Diseño del AST (nodos)

```python
from dataclasses import dataclass, field
from typing import Optional, Union

# ---------- Programa ----------
@dataclass
class Programa:
    importaciones: list["Importacion"]
    declaraciones_globales: list["DeclaracionPista"]
    funciones: dict[str, Union["Escena", "Proceso"]]
    caso_principal: "CasoPrincipal"
    archivo_origen: str

@dataclass
class Importacion:
    archivo: str
    linea: int

@dataclass
class CasoPrincipal:
    nombre: str
    cuerpo: list["Sentencia"]
    linea: int

# ---------- Declaraciones ----------
@dataclass
class DeclaracionPista:
    nombre: str
    valor: "Expresion"
    es_constante: bool   # True si se declaró con "hecho"
    linea: int

@dataclass
class Asignacion:
    nombre: str
    valor: "Expresion"
    linea: int
    indices: Optional[list["Expresion"]] = None  # None = simple; lista = celda[i][j] = valor

# ---------- Entrada/Salida ----------
@dataclass
class Revelar:
    argumentos: list["Expresion"]
    linea: int

@dataclass
class Consultar:
    variable: str
    linea: int

# ---------- Condicionales ----------
@dataclass
class RamaCondicional:
    condicion: "Expresion"
    cuerpo: list["Sentencia"]

@dataclass
class EvaluarSi:
    rama_si: RamaCondicional
    ramas_sino_evaluar: list[RamaCondicional]
    cuerpo_sino: Optional[list["Sentencia"]]
    linea: int

@dataclass
class CasoSuceso:
    numero: int
    condicion: "Expresion"
    cuerpo: list["Sentencia"]

@dataclass
class Suceso:
    variable: "Expresion"
    casos: list[CasoSuceso]
    linea: int

# ---------- Ciclos ----------
@dataclass
class Rastrear:
    variable: str
    desde: "Expresion"
    hasta: "Expresion"
    cuerpo: list["Sentencia"]
    linea: int

@dataclass
class SeguirMientras:
    condicion: "Expresion"
    cuerpo: list["Sentencia"]
    linea: int

# ---------- Funciones ----------
@dataclass
class Parametro:
    nombre: str
    tipo: str

@dataclass
class Escena:   # función CON retorno
    nombre: str
    parametros: list[Parametro]
    tipo_retorno: str
    cuerpo: list["Sentencia"]
    linea: int
    archivo: str = ""   # archivo donde se declaró (para reportar errores de funciones importadas)

@dataclass
class Proceso:  # función SIN retorno
    nombre: str
    parametros: list[Parametro]
    cuerpo: list["Sentencia"]
    linea: int
    archivo: str = ""   # igual que en Escena

@dataclass
class Resolver:   # llamada a función
    nombre: str
    argumentos: list["Expresion"]
    linea: int

@dataclass
class Concluir:
    valor: "Expresion"
    linea: int

# ---------- Expresiones ----------
@dataclass
class Literal:
    tipo: str      # "entero" | "decimal" | "expresion" | "declaracion" | "sin_pista"
    valor: object
    tipo_declarado: str = ""   # tipo del constructor: entero(valor: sin_pista) -> "entero"

@dataclass
class Identificador:
    nombre: str

@dataclass
class OperacionAritmetica:
    operador: str            # conectar | descartar | intensificar | repartir
    operandos: list["Expresion"]
    linea: int = 0

@dataclass
class OperacionLogica:
    operador: str            # y | o | no
    izquierda: "Expresion"
    derecha: Optional["Expresion"]

@dataclass
class OperacionRelacional:
    operador: str            # == | <> | > | < | >= | <=
    izquierda: "Expresion"
    derecha: "Expresion"

@dataclass
class ListaLiteral:          # pistas entero[2, 4, 6]
    tipo_elemento: str
    elementos: list["Expresion"]

@dataclass
class TableroLiteral:        # tablero entero[4][4]
    tipo_elemento: str
    filas: "Expresion"
    columnas: "Expresion"

@dataclass
class AccesoIndice:
    base: "Expresion"
    indices: list["Expresion"]

Sentencia = Union[DeclaracionPista, Asignacion, Revelar, Consultar,
                   EvaluarSi, Suceso, Rastrear, SeguirMientras,
                   Resolver, Concluir]
Expresion = Union[Literal, Identificador, OperacionAritmetica,
                   OperacionLogica, OperacionRelacional,
                   ListaLiteral, TableroLiteral, AccesoIndice]
```

---

## 5. Analizador semántico

### 5.1 Tabla de símbolos

```python
@dataclass
class Simbolo:
    nombre: str
    tipo: str
    es_constante: bool
    linea_declaracion: int

class Alcance:
    def __init__(self, padre: Optional["Alcance"] = None):
        self.padre = padre
        self.simbolos: dict[str, Simbolo] = {}

    def declarar(self, simbolo: Simbolo):
        if simbolo.nombre in self.simbolos:
            raise IndicioFallidoDeRazonamiento(
                tipo="Declaración duplicada", ...)
        self.simbolos[simbolo.nombre] = simbolo

    def buscar(self, nombre: str) -> Optional[Simbolo]:
        if nombre in self.simbolos:
            return self.simbolos[nombre]
        if self.padre:
            return self.padre.buscar(nombre)
        return None
```

- **Alcance global:** pistas declaradas fuera de `escena`/`proceso`/`caso`.
- **Alcance local:** un `Alcance` hijo se crea al entrar a `escena`, `proceso`, `evaluar si`, `rastrear` o `seguir mientras`, y se descarta al salir del bloque — igual a como lo describe la sección 5.4 del documento.

### 5.2 Validaciones que debe correr el analizador semántico

1. Variable usada sin declarar → error.
2. Reasignación de un `hecho` → error ("Hecho Inalterable").
3. Tipos incompatibles en `conectar/descartar/intensificar/repartir` (solo `entero`/`decimal`) → error ("Incompatibilidad de Evidencias").
4. Declaración duplicada en el mismo alcance → error.
5. `escena` sin `concluir` en todos los caminos posibles → error.
6. `proceso` que use `concluir` → error (no está permitido).
7. Operación aritmética sobre `sin_pista` sin reasignar antes → error.
8. Acceso a `tablero`/`pistas` fuera de los límites declarados → error.
9. **Exactamente un `caso` principal en todo el proyecto** (ver sección 6.3 — punto pendiente de definir con el equipo).

**Estado de cada validación:**

| # | Validación | Estado |
|---|---|---|
| 1 | Variable sin declarar | ✅ |
| 2 | Reasignar un `hecho` | ✅ |
| 3 | Tipos incompatibles en aritmética | ✅ |
| 4 | Declaración duplicada en el mismo alcance | ✅ |
| 5 | `escena` sin `concluir` en todos los caminos | **Pendiente** (hoy solo falla al ejecutar) |
| 6 | `concluir` fuera de una escena o dentro de un proceso | ✅ |
| 7 | Operar un `sin_pista` sin reasignarlo antes | ✅ |
| 8 | Límites de `tablero` / `pistas` | Solo en ejecución; **pendiente** en el semántico |
| 9 | Exactamente un `caso` en el proyecto | **Pendiente** (hoy todo archivo exige su `caso`) |

Validaciones añadidas durante la implementación: el valor de `entero(...)`, `decimal(...)`, etc. debe corresponder al tipo; las listas no pueden mezclar tipos; el texto y las declaraciones no se ordenan con `> < >= <=`; el límite de `rastrear` debe ser entero; una pista `entero(valor: sin_pista)` solo puede reasignarse a su tipo declarado.

Todas las validaciones lanzan una subclase de la misma excepción base (`core/errors.py`), para que el formato de error sea consistente. La base guarda además un **indicio** corto (el campo `indicio`), que usa la innovación (sección 11):

```python
class IndicioFallidoDeRazonamiento(Exception):
    def __init__(self, tipo, archivo, linea, indicio, descripcion, causa_posible): ...
    def mostrar_indicio(self) -> str:    # primer aviso: solo el indicio
    def mostrar_completo(self) -> str:   # segundo aviso: tipo, archivo, línea, descripción, causa

class ErrorLexico(IndicioFallidoDeRazonamiento): ...
class ErrorSintactico(IndicioFallidoDeRazonamiento): ...
class ErrorSemantico(IndicioFallidoDeRazonamiento): ...
class ErrorDeImportacion(IndicioFallidoDeRazonamiento): ...
class ErrorDeEjecucion(IndicioFallidoDeRazonamiento): ...
```

---

## 6. Resolución de módulos (`#expediente`)

### 6.1 Algoritmo

1. Empezar por el archivo marcado como principal del proyecto (`resolver_importaciones(programa, directorio_base)` en `core/module_resolver.py`).
2. Parsear sus directivas `#expediente <archivo.eng>`. La ruta se busca **junto al archivo que la escribe** y acepta subcarpetas y `../`.
3. Por cada archivo importado, parsearlo recursivamente y registrar sus `escena`/`proceso` en una tabla global de funciones.
4. Detectar ciclos con el algoritmo clásico de DFS de 3 colores (blanco/gris/negro):

```python
def detectar_ciclo(grafo: dict[str, list[str]]) -> Optional[list[str]]:
    BLANCO, GRIS, NEGRO = 0, 1, 2
    estado = {archivo: BLANCO for archivo in grafo}
    pila: list[str] = []

    def visitar(nodo):
        estado[nodo] = GRIS
        pila.append(nodo)
        for vecino in grafo.get(nodo, []):
            if estado[vecino] == GRIS:
                return pila[pila.index(vecino):] + [vecino]   # ciclo encontrado
            if estado[vecino] == BLANCO:
                resultado = visitar(vecino)
                if resultado:
                    return resultado
        pila.pop()
        estado[nodo] = NEGRO
        return None

    for nodo in grafo:
        if estado[nodo] == BLANCO:
            ciclo = visitar(nodo)
            if ciclo:
                return ciclo
    return None
```

   El caso **diamante** (A importa B y C, y ambos importan D) no es un error: D se carga una sola vez y no produce un falso «función duplicada».

5. Validar, por cada `resolver NombreFuncion(...)`: que la función exista en la tabla global, que la cantidad de argumentos coincida, y que los tipos sean compatibles con los parámetros declarados.

### 6.2 Validaciones exigidas por el PDF del curso (sección 8)

- Existencia del archivo importado.
- Existencia de la función dentro de ese archivo.
- Cantidad de argumentos correcta.
- Compatibilidad de tipos.
- Declaraciones duplicadas (dos archivos definiendo la misma función).
- Importaciones circulares.
- Errores dentro de los archivos importados (se deben reportar con el nombre del archivo real donde ocurrió el error, no el archivo que lo importó).

### 6.3 Archivo principal (decidido)

Se eligió la **Opción A**: el archivo principal lo marca el usuario en el árbol de archivos del IDE (★, clic derecho) y se guarda en `.enigma_proyecto.json` dentro del proyecto, con la forma `{"principal": "ruta/relativa.eng"}`. Ese archivo no se sube a git (está en `.gitignore`), porque es una preferencia de cada persona. Permite nombres de caso descriptivos como `caso ResolverExamen`.

**Pendiente:** hoy todo archivo exige un bloque `caso`. Falta permitir archivos sin `caso` (bibliotecas de funciones), exigir **exactamente uno** en el principal y rechazar un `caso` en otro archivo (PDF §7, validación 9 de la sección 5.2).

---

## 7. Intérprete (tree-walking)

Patrón recomendado: **visitor pattern manual** con un diccionario de despacho, más simple de mantener que una jerarquía de clases con `accept()`/`visit()`:

```python
class Interprete:
    def __init__(self, programa: Programa):
        self.programa = programa
        self.alcance_global = Alcance()
        self.despachador = {
            DeclaracionPista: self.ejecutar_declaracion,
            Asignacion: self.ejecutar_asignacion,
            Revelar: self.ejecutar_revelar,
            Consultar: self.ejecutar_consultar,
            EvaluarSi: self.ejecutar_evaluar_si,
            Suceso: self.ejecutar_suceso,
            Rastrear: self.ejecutar_rastrear,
            SeguirMientras: self.ejecutar_seguir_mientras,
            Resolver: self.ejecutar_resolver,
            Concluir: self.ejecutar_concluir,
        }

    def ejecutar_bloque(self, sentencias: list, alcance: Alcance):
        for sentencia in sentencias:
            self.despachador[type(sentencia)](sentencia, alcance)

    def ejecutar(self):
        self.ejecutar_bloque(self.programa.caso_principal.cuerpo, self.alcance_global)
```

`ejecutar_resolver` invoca `escena`/`proceso` creando un nuevo `Alcance` hijo para los parámetros; si es `escena`, captura la excepción de control interna `RetornoEscena` que lanza `ejecutar_concluir` para propagar el valor de retorno hacia arriba (patrón estándar de "return como excepción" en intérpretes de árbol).

---

## 8. Decisión de framework para el GUI

| Opción | Ventajas | Desventajas |
|---|---|---|
| **Tkinter** (recomendada) | Viene con Python, cero instalación extra, todo el equipo puede correrlo sin configurar nada, suficiente para árbol de archivos + editor + output + botones | Resaltado de sintaxis se hace a mano con `Text.tag_add` + expresiones regulares (más trabajo manual, pero controlable) |
| **PyQt6 / PySide6** | Resaltado de sintaxis profesional con `QSyntaxHighlighter`, look más pulido, widgets más completos | Requiere instalar dependencias pesadas, curva de aprendizaje más alta, licenciamiento de PyQt6 puede complicar la entrega si alguien no configura bien el entorno |

**Recomendación:** empezar con **Tkinter**, dado el tiempo del curso y que ya van a invertir bastante esfuerzo en el compilador. El resaltado de sintaxis en Tkinter se resuelve con un `re.finditer` sobre las palabras reservadas y `text_widget.tag_add("palabra_clave", inicio, fin)` — es menos elegante que Qt pero perfectamente funcional y defendible.

Si el equipo tiene tiempo de sobra después de tener el compilador funcionando, migrar a PyQt6 es un "upgrade" razonable, no un rediseño completo (la lógica del compilador no cambia, solo la capa de presentación).

---

## 9. Estructura de carpetas del proyecto

Estructura real (la lista completa de archivos de `gui/` está en el `README.md`):

```
enigma/
├── main.py                       # Punto de entrada, lanza el IDE
├── requirements.txt              # Solo pytest; el IDE usa tkinter (incluido en Python)
├── README.md
│
├── core/                         # El lenguaje, sin dependencias externas
│   ├── tokens.py                 # TipoToken, Token
│   ├── lexer.py                  # Analizador léxico (y comentarios { })
│   ├── ast_nodes.py              # Dataclasses del AST
│   ├── parser.py                 # Punto de entrada del parser
│   ├── parser_base.py            # Utilidades comunes
│   ├── parser_sentencias.py      # Declaraciones, asignaciones, E/S
│   ├── parser_control.py         # Condicionales y ciclos
│   ├── parser_expresiones.py     # Expresiones y tipos compuestos
│   ├── parser_funciones.py       # escena / proceso / resolver / concluir
│   ├── symbols.py                # Simbolo, Alcance
│   ├── semantic.py               # Analizador semántico
│   ├── module_resolver.py        # Resolución de #expediente + detección de ciclos
│   ├── interpreter.py            # Intérprete de árbol
│   └── errors.py                 # IndicioFallidoDeRazonamiento y subclases
│
├── gui/                          # El IDE en tkinter
│   ├── main_window.py            # Ventana principal
│   ├── editor_widget.py, pestana_editor.py, barra_pestanas.py, barra_busqueda.py, resaltado.py
│   ├── file_tree.py              # Árbol de archivos y archivo principal
│   ├── output_panel.py           # Salida / Terminal, compilar y ejecutar
│   ├── indicios.py               # Innovación: indicios de error
│   ├── constructor_codigo.py, constructor_bloques.py   # Constructor de bloques
│   ├── guia_contenido.py, guia_detective.py, guia_rapida.py, panel_derecho.py
│   └── cabecera.py, ajustes.py, dialogos.py, botones.py, recursos.py, tema.py, assets/
│
├── herramientas/                 # Scripts que generan el logo y los iconos
├── ejemplos/caso_promedio/       # Programa de ejemplo
├── ejemplo_gui/                  # Proyecto de ejemplo para abrir en el IDE
├── tests/                        # Pruebas con pytest
│   └── programas_prueba/         # Los 20 .eng de la sección 18 del PDF + su catálogo (casos.py)
└── docs/                         # Documentación del proyecto
```

---

## 10. Orden de implementación y estado

| Etapa | Estado |
|---|---|
| 1. `tokens.py` + `lexer.py` | ✅ |
| 2. `ast_nodes.py` + `parser*.py` | ✅ |
| 3. `errors.py` | ✅ |
| 4. `symbols.py` + `semantic.py` | ✅ (validaciones 5, 8 y 9 pendientes) |
| 5. `module_resolver.py` | ✅ |
| 6. `interpreter.py` | ✅ |
| 7. GUI | ✅ (faltan nuevo proyecto, ubicar errores y advertencias) |
| 8. Los 20 programas de prueba (§18 del PDF) | ✅ (`python herramientas/informe_pruebas.py` genera `docs/Pruebas_Programas.md`) |

El trabajo se repartió en paralelo entre las dos personas del equipo.

---

## 11. Innovación: errores en dos pasos

El IDE no muestra el error completo de inmediato. Ante un error:

1. **Primera vez:** muestra solo un **indicio** (`mostrar_indicio()`), generado en `gui/indicios.py`. Orienta sin decir en qué línea está el error y sin usar nombres internos del compilador.
2. **Si el mismo error se repite:** muestra la explicación completa (`mostrar_completo()`): tipo, archivo, línea, descripción y posible causa.

Está integrada con el panel de salida y la Guía rápida (que conserva el indicio del último error). Se complementa con el **Constructor de bloques**, que arma código con formularios y lo valida con el compilador antes de insertarlo en el editor, y con la **Guía del detective** (F1), cuyos ejemplos se insertan en el editor y se comprueban en las pruebas (`tests/test_guia.py`).
