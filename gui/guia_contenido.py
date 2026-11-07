"""Contenido de la Guia del detective (menu de consulta del PDF, seccion 10).

Son solo datos, sin tkinter: asi tests/test_guia.py comprueba que TODOS los
ejemplos de la guia compilan (y los programas completos, ademas, se ejecutan).
La guia no puede mentir sobre el lenguaje.

Tipos de bloque:
  Parrafo, Subtitulo, Nota, Lista   texto explicativo
  Codigo                            codigo; si es 'ejecutable' es un programa
                                    completo que se prueba corriendolo; si es
                                    'plantilla' lleva <marcas> y no se prueba
  Termino                           palabra reservada (nombre, que hace, uso, ejemplo)
  Ficha                             un tipo de dato (declaracion, uso, operaciones, restricciones)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Parrafo:
    texto: str


@dataclass(frozen=True)
class Subtitulo:
    texto: str


@dataclass(frozen=True)
class Nota:
    texto: str


@dataclass(frozen=True)
class Lista:
    items: tuple[str, ...]


@dataclass(frozen=True)
class Codigo:
    texto: str
    titulo: str = ""
    ejecutable: bool = False          # programa completo: se compila y se corre en las pruebas
    plantilla: bool = False           # tiene <marcas>: solo se puede copiar, no se prueba
    entradas: tuple[str, ...] = ()    # lo que "escribe el usuario" si el programa usa consultar


@dataclass(frozen=True)
class Termino:
    nombre: str
    descripcion: str
    uso: str = ""        # plantilla con <marcas>
    ejemplo: str = ""    # fragmento real (las pruebas comprueban que se puede parsear)


@dataclass(frozen=True)
class Ficha:
    nombre: str
    declaracion: str
    uso: str
    operaciones: str
    restricciones: str


@dataclass(frozen=True)
class Seccion:
    id: str
    titulo: str
    resumen: str
    bloques: tuple


# --------------------------------------------------------------------------- #
# 1. Palabras reservadas
# --------------------------------------------------------------------------- #

PALABRAS = Seccion(
    id="palabras",
    titulo="Palabras reservadas",
    resumen="Las palabras con significado fijo del lenguaje.",
    bloques=(
        Parrafo("Estas palabras tienen un significado fijo en Enigma: no se pueden usar como nombre de una pista (variable) ni de una función."),

        Subtitulo("Declaraciones"),
        Termino("pista", "Declara una variable. Su valor puede cambiar.",
                "pista <nombre> = <tipo>(valor: x)!", "pista sospechoso1 = entero(valor: 15)!"),
        Termino("hecho", "Declara una constante. Intentar cambiarla es un error de compilación.",
                "hecho <nombre> = <tipo>(valor: x)!", "hecho maximo = entero(valor: 10)!"),
        Termino("valor", "Va dentro del tipo e indica el valor inicial.",
                "<tipo>(valor: x)", "pista nombre = expresion(valor: 'Alex')!"),

        Subtitulo("Programa principal"),
        Termino("caso", "El programa principal (equivale a main). Se abre con «abierto» y se cierra con «cerrado!».",
                "caso <Nombre> abierto ... caso <Nombre> cerrado!",
                "caso HolaDetective abierto\n    revelar('Hola')!\ncaso HolaDetective cerrado!"),
        Termino("abierto / cerrado", "Marcan el comienzo y el final del caso. El nombre debe ser el mismo en ambos."),

        Subtitulo("Entrada y salida"),
        Termino("revelar", "Muestra algo en la salida. Acepta varios valores separados por coma.",
                "revelar(<valor>, <valor>, ...)!", "revelar('El sospechoso es:', sospechoso1)!"),
        Termino("consultar", "Pide un dato al usuario y lo guarda en una pista ya declarada.",
                "consultar(<variable>)!", "consultar(valorPremisa)!"),

        Subtitulo("Condicionales"),
        Termino("evaluar si", "Condicional simple: ejecuta el bloque si la condición es verdadera.",
                "evaluar si (<condicion>) inicio ... fin!",
                "evaluar si (pista1 > pista2) inicio\n    revelar('Mayor')!\nfin!"),
        Termino("sino evaluar", "Otra condición, si la anterior no se cumplió.",
                "sino evaluar (<condicion>) inicio ... fin!",
                "evaluar si (a < 1) inicio\n    revelar('a')!\nfin!\nsino evaluar (a < 2) inicio\n    revelar('b')!\nfin!"),
        Termino("sino", "Alternativa final, si ninguna condición se cumplió.",
                "sino inicio ... fin!",
                "evaluar si (a < 1) inicio\n    revelar('a')!\nfin!\nsino inicio\n    revelar('otra')!\nfin!"),
        Termino("suceso", "Condición múltiple: varios casos numerados con su propia condición.",
                "suceso (<variable>) inicio\n    1 (<condicion>): <instruccion>\n    ...\nfin!",
                "suceso (edad) inicio\n    1 (edad < 18): revelar('menor')!\n    2 (edad > 18): revelar('mayor')!\nfin!"),

        Subtitulo("Bloques"),
        Termino("inicio / fin", "Abren y cierran un bloque (condicionales, ciclos y funciones). El «fin» siempre lleva «!»."),

        Subtitulo("Ciclos"),
        Termino("rastrear", "Ciclo de repetición controlada (como for). El contador sube de 1 en 1, desde el primer valor hasta el último, inclusive.",
                "rastrear <contador> desde <x> hasta <y> inicio ... fin!",
                "rastrear paso desde 1 hasta 10 inicio\n    revelar(paso)!\nfin!"),
        Termino("desde / hasta", "Marcan el valor inicial y el final de «rastrear»."),
        Termino("seguir mientras", "Ciclo que se repite mientras la condición sea verdadera (como while).",
                "seguir mientras (<condicion>) inicio ... fin!",
                "seguir mientras (n > 0) inicio\n    n = descartar(n, 1)!\nfin!"),

        Subtitulo("Funciones"),
        Termino("escena", "Define una función que devuelve un valor.",
                "escena <Nombre>(<p>: <tipo>)::<tipo> inicio ... fin!",
                "escena Doble(x: entero)::entero inicio\n    concluir intensificar(x, 2)!\nfin!"),
        Termino("proceso", "Define una función que no devuelve nada.",
                "proceso <Nombre>(<p>: <tipo>) inicio ... fin!",
                "proceso Saludar(nombre: expresion) inicio\n    revelar('Hola', nombre)!\nfin!"),
        Termino("resolver", "Llama a una escena o a un proceso.",
                "resolver <Nombre>(<argumentos>)!", "resolver Saludar('Ana')!"),
        Termino("concluir", "Devuelve el valor de una escena y termina la función.",
                "concluir <expresion>!", "concluir resultado!"),

        Subtitulo("Aritmética"),
        Termino("conectar", "Suma. Acepta dos o más valores.", "conectar(p1, p2, ...)", "pista s = conectar(a, b, c)!"),
        Termino("descartar", "Resta.", "descartar(p1, p2)", "pista r = descartar(a, b)!"),
        Termino("intensificar", "Multiplicación.", "intensificar(p1, p2)", "pista m = intensificar(a, b)!"),
        Termino("repartir", "División.", "repartir(p1, p2)", "pista d = repartir(a, b)!"),

        Subtitulo("Lógica"),
        Termino("y", "AND lógico: verdadero si ambas condiciones lo son.",
                "(<condicion>) y (<condicion>)",
                "evaluar si ((a > 1) y (a < 10)) inicio\n    revelar('en rango')!\nfin!"),
        Termino("o", "OR lógico: verdadero si al menos una condición lo es.",
                "(<condicion>) o (<condicion>)",
                "evaluar si ((a == 1) o (a == 2)) inicio\n    revelar('uno o dos')!\nfin!"),
        Termino("no", "NOT: invierte una condición.",
                "no (<condicion>)",
                "evaluar si (no (a == 1)) inicio\n    revelar('no es uno')!\nfin!"),

        Subtitulo("Tipos"),
        Termino("entero", "Números sin decimales.", "entero(valor: 15)", "pista a = entero(valor: 15)!"),
        Termino("decimal", "Números con decimales.", "decimal(valor: 15.5)", "pista a = decimal(valor: 15.5)!"),
        Termino("expresion", "Texto (cadena entre comillas simples).", "expresion(valor: 'texto')", "pista a = expresion(valor: 'Estaba en el baño.')!"),
        Termino("declaracion", "Booleano: culpable o NoCulpable.", "declaracion(valor: culpable)", "pista a = declaracion(valor: NoCulpable)!"),
        Termino("pistas", "Lista de elementos del mismo tipo.", "pistas <tipo>[a, b, c]", "pista archivos = pistas entero[2, 4, 6]!"),
        Termino("tablero", "Matriz de filas y columnas.", "tablero <tipo>[filas][columnas]", "pista celdas = tablero entero[4][4]!"),

        Subtitulo("Valores especiales"),
        Termino("culpable", "Verdadero."),
        Termino("NoCulpable", "Falso."),
        Termino("sin_pista", "Nulo: la ausencia de valor.", "<tipo>(valor: sin_pista)", "pista nota = entero(valor: sin_pista)!"),

        Subtitulo("Símbolos"),
        Termino("!", "Terminador: cierra cada instrucción y cada bloque (fin!, caso … cerrado!)."),
        Termino("{ }", "Comentario: todo lo que esté entre llaves se ignora.", "{ <comentario> }", "{ esto no se ejecuta }"),
        Termino("#expediente", "Importa las funciones de otro archivo del proyecto.",
                "#expediente <archivo.eng>", "#expediente <pistas.eng>"),
    ),
)


# --------------------------------------------------------------------------- #
# 2. Sintaxis
# --------------------------------------------------------------------------- #

SINTAXIS = Seccion(
    id="sintaxis",
    titulo="Sintaxis",
    resumen="Cómo se escribe cada instrucción.",
    bloques=(
        Parrafo("Reglas generales: cada instrucción termina con «!», los bloques se abren con «inicio» y se cierran con «fin!», y los comentarios van entre llaves { }. Las mayúsculas importan."),

        Subtitulo("Instrucciones"),
        Parrafo("Declaración de una variable (pista) o de una constante (hecho):"),
        Codigo("pista sospechoso1 = entero(valor: 15)!\nhecho limite = entero(valor: 10)!", "Declaración"),
        Parrafo("Asignación: se escribe el nombre y un nuevo valor del mismo tipo."),
        Codigo("pista edad = entero(valor: 15)!\nedad = entero(valor: 16)!\nedad = conectar(edad, 1)!", "Asignación"),
        Parrafo("Entrada de datos: lee lo que escribe el usuario."),
        Codigo("pista edad = entero(valor: 0)!\nconsultar(edad)!", "Entrada"),
        Parrafo("Salida de datos: muestra textos y valores."),
        Codigo("pista edad = entero(valor: 17)!\nrevelar('Tu edad es:', edad)!", "Salida"),
        Parrafo("Llamada a una función: con «resolver». Si devuelve un valor, se puede guardar o usar directamente."),
        Codigo("resolver Saludar('Ana')!\npista doble = resolver Doble(21)!\nrevelar(resolver Doble(4))!", "Llamadas"),
        Parrafo("Importación: va al inicio del archivo y no lleva «!»."),
        Codigo("#expediente <pistas.eng>", "Importación"),

        Subtitulo("Estructura de un archivo"),
        Parrafo("Primero las importaciones, luego (si las hay) variables globales y funciones, y al final el caso principal."),
        Codigo(
            "#expediente <utilidades.eng>      { 1. importaciones }\n"
            "\n"
            "hecho maximo = entero(valor: 10)!  { 2. globales (opcional) }\n"
            "\n"
            "proceso Saludar(nombre: expresion) inicio   { 3. funciones }\n"
            "    revelar('Hola', nombre)!\n"
            "fin!\n"
            "\n"
            "caso MiCaso abierto               { 4. programa principal }\n"
            "    resolver Saludar('Ana')!\n"
            "caso MiCaso cerrado!",
            "Orden de un archivo",
        ),

        Subtitulo("Comentarios"),
        Codigo("{ Un comentario de una línea }\ncaso C abierto\n    { También en medio del código }\n    revelar('hola')!\ncaso C cerrado!",
               "Comentarios", ejecutable=True),
        Nota("Un comentario sin su llave de cierre «}» es un error léxico."),
    ),
)


# --------------------------------------------------------------------------- #
# 3. Estructuras de control
# --------------------------------------------------------------------------- #

CONTROL = Seccion(
    id="control",
    titulo="Estructuras de control",
    resumen="Condicionales y ciclos.",
    bloques=(
        Subtitulo("Condicional simple"),
        Parrafo("Ejecuta el bloque solo si la condición es verdadera."),
        Codigo(
            "caso Simple abierto\n"
            "    pista edad = entero(valor: 20)!\n"
            "    evaluar si (edad >= 18) inicio\n"
            "        revelar('Es mayor de edad')!\n"
            "    fin!\n"
            "caso Simple cerrado!",
            "evaluar si", ejecutable=True,
        ),

        Subtitulo("Condicional con alternativa"),
        Parrafo("«sino» se ejecuta cuando la condición no se cumple."),
        Codigo(
            "caso Alternativa abierto\n"
            "    pista coartada = expresion(valor: 'biblioteca')!\n"
            "    evaluar si (coartada == 'biblioteca') inicio\n"
            "        revelar('La coartada coincide.')!\n"
            "    fin!\n"
            "    sino inicio\n"
            "        revelar('Indicio fallido: revisa la coartada.')!\n"
            "    fin!\n"
            "caso Alternativa cerrado!",
            "evaluar si … sino", ejecutable=True,
        ),

        Subtitulo("Condicional múltiple"),
        Parrafo("Hay dos formas. La primera encadena condiciones con «sino evaluar»:"),
        Codigo(
            "caso Veredicto abierto\n"
            "    pista edad = entero(valor: 17)!\n"
            "    evaluar si (edad < 18) inicio\n"
            "        revelar('Menor de edad')!\n"
            "    fin!\n"
            "    sino evaluar (edad == 18) inicio\n"
            "        revelar('Justo 18')!\n"
            "    fin!\n"
            "    sino inicio\n"
            "        revelar('Mayor de edad')!\n"
            "    fin!\n"
            "caso Veredicto cerrado!",
            "sino evaluar", ejecutable=True,
        ),
        Parrafo("La segunda es «suceso»: una lista de casos numerados, cada uno con su condición."),
        Codigo(
            "caso Casos abierto\n"
            "    pista edad = entero(valor: 18)!\n"
            "    suceso (edad) inicio\n"
            "        1 (edad < 18): revelar('Menor')!\n"
            "        2 (edad > 18): revelar('Mayor')!\n"
            "        3 (edad == 18): revelar('Justo 18')!\n"
            "    fin!\n"
            "caso Casos cerrado!",
            "suceso", ejecutable=True,
        ),

        Subtitulo("Ciclo con contador: rastrear"),
        Parrafo("El contador se crea solo, sube de 1 en 1 y existe únicamente dentro del ciclo. Incluye el valor final."),
        Codigo(
            "caso Contar abierto\n"
            "    pista total = entero(valor: 0)!\n"
            "    rastrear paso desde 1 hasta 4 inicio\n"
            "        total = conectar(total, paso)!\n"
            "    fin!\n"
            "    revelar('La suma de 1 a 4 es', total)!\n"
            "caso Contar cerrado!",
            "rastrear", ejecutable=True,
        ),
        Nota("El contador de «rastrear» debe ser entero: un decimal no sirve como contador."),

        Subtitulo("Ciclo con condición: seguir mientras"),
        Parrafo("Repite el bloque mientras la condición sea verdadera. Dentro del bloque hay que cambiar algo, o el ciclo no termina nunca."),
        Codigo(
            "caso Cuenta abierto\n"
            "    pista n = entero(valor: 3)!\n"
            "    seguir mientras (n > 0) inicio\n"
            "        revelar('Faltan', n)!\n"
            "        n = descartar(n, 1)!\n"
            "    fin!\n"
            "caso Cuenta cerrado!",
            "seguir mientras", ejecutable=True,
        ),
    ),
)


# --------------------------------------------------------------------------- #
# 4. Funciones
# --------------------------------------------------------------------------- #

FUNCIONES = Seccion(
    id="funciones",
    titulo="Funciones",
    resumen="Escenas, procesos, parámetros y retorno.",
    bloques=(
        Parrafo("Hay dos clases de funciones: la «escena» devuelve un valor y el «proceso» no. Se declaran antes del caso principal, y los parámetros llevan su tipo: nombre: tipo."),

        Subtitulo("Función con retorno: escena"),
        Parrafo("Después de los parámetros se escribe «::» y el tipo que devuelve. Debe terminar con «concluir»."),
        Codigo(
            "escena Promedio(a: entero, b: entero)::decimal inicio\n"
            "    concluir repartir(conectar(a, b), 2)!\n"
            "fin!\n"
            "\n"
            "caso Notas abierto\n"
            "    pista p = resolver Promedio(15, 18)!\n"
            "    revelar('El promedio es', p)!\n"
            "caso Notas cerrado!",
            "escena", ejecutable=True,
        ),

        Subtitulo("Función sin retorno: proceso"),
        Parrafo("Ejecuta sus instrucciones y termina al llegar a «fin!». No puede usar «concluir»."),
        Codigo(
            "proceso Saludar(nombre: expresion) inicio\n"
            "    revelar('Hola', nombre)!\n"
            "fin!\n"
            "\n"
            "caso Saludo abierto\n"
            "    resolver Saludar('Ana')!\n"
            "caso Saludo cerrado!",
            "proceso", ejecutable=True,
        ),

        Subtitulo("Parámetros y argumentos"),
        Lista((
            "Los parámetros son los nombres que recibe la función: nombre: tipo.",
            "Los argumentos son los valores con que la llamas.",
            "La cantidad y el tipo de los argumentos se validan al compilar.",
            "Un entero se puede pasar donde se espera un decimal.",
        )),

        Subtitulo("Punto de entrada"),
        Parrafo("El programa empieza siempre en el bloque «caso … abierto». Dentro del caso se llama a las demás funciones con «resolver»."),
        Nota("Si una función está en otro archivo, impórtala con #expediente (mira la sección Importaciones)."),
    ),
)


# --------------------------------------------------------------------------- #
# 5. Operaciones
# --------------------------------------------------------------------------- #

OPERACIONES = Seccion(
    id="operaciones",
    titulo="Operaciones",
    resumen="Aritméticas, lógicas y relacionales.",
    bloques=(
        Subtitulo("Aritméticas"),
        Parrafo("Se escriben como funciones y se evalúan respetando el orden de los argumentos. Solo aceptan entero y decimal."),
        Lista((
            "conectar(a, b, ...)  suma (acepta dos o más valores)",
            "descartar(a, b)  resta",
            "intensificar(a, b)  multiplicación",
            "repartir(a, b)  división (dividir entre cero es un error de ejecución)",
        )),
        Codigo(
            "caso Aritmetica abierto\n"
            "    pista a = entero(valor: 12)!\n"
            "    pista b = entero(valor: 5)!\n"
            "    revelar('Suma:', conectar(a, b))!\n"
            "    revelar('Resta:', descartar(a, b))!\n"
            "    revelar('Multiplicación:', intensificar(a, b))!\n"
            "    revelar('División:', repartir(a, b))!\n"
            "    revelar('Anidadas:', repartir(conectar(a, b), 2))!\n"
            "caso Aritmetica cerrado!",
            "Aritmética", ejecutable=True,
        ),

        Subtitulo("Relacionales"),
        Lista((
            "==  igual",
            "<>  diferente",
            ">  mayor",
            "<  menor",
            ">=  mayor o igual",
            "<=  menor o igual",
        )),
        Parrafo("Comparan dos valores del mismo tipo y dan una declaración (culpable o NoCulpable). Los textos solo se comparan con == y <>."),
        Codigo(
            "caso Comparar abierto\n"
            "    pista sospechoso = expresion(valor: 'Alex')!\n"
            "    evaluar si (sospechoso == 'Alex') inicio\n"
            "        revelar('Es Alex')!\n"
            "    fin!\n"
            "    evaluar si (sospechoso <> 'Luis') inicio\n"
            "        revelar('No es Luis')!\n"
            "    fin!\n"
            "caso Comparar cerrado!",
            "Relacionales", ejecutable=True,
        ),

        Subtitulo("Lógicas"),
        Lista((
            "y  AND: ambas condiciones deben ser verdaderas",
            "o  OR: al menos una debe ser verdadera",
            "no  NOT: invierte la condición",
        )),
        Parrafo("Escribe cada condición entre paréntesis. Se evalúan de izquierda a derecha."),
        Codigo(
            "caso Logicas abierto\n"
            "    pista a = entero(valor: 5)!\n"
            "    evaluar si ((a > 1) y (a < 10)) inicio\n"
            "        revelar('a está entre 1 y 10')!\n"
            "    fin!\n"
            "    evaluar si ((a == 1) o (a == 5)) inicio\n"
            "        revelar('a es 1 o 5')!\n"
            "    fin!\n"
            "    evaluar si (no (a == 3)) inicio\n"
            "        revelar('a no es 3')!\n"
            "    fin!\n"
            "caso Logicas cerrado!",
            "Lógicas", ejecutable=True,
        ),
    ),
)


# --------------------------------------------------------------------------- #
# 6. Semántica
# --------------------------------------------------------------------------- #

SEMANTICA = Seccion(
    id="semantica",
    titulo="Semántica",
    resumen="Cómo se comporta un programa al compilar y ejecutar.",
    bloques=(
        Subtitulo("Cómo inicia un programa"),
        Parrafo("La ejecución empieza en el bloque «caso Nombre abierto … caso Nombre cerrado!» del archivo principal. Todo archivo lleva su propio caso, pero solo se ejecuta el del archivo marcado como principal."),

        Subtitulo("Bloques e indentación"),
        Parrafo("Los bloques se delimitan con «inicio» y «fin!». La indentación NO es obligatoria; el editor la recomienda para que el código se lea como una narración."),

        Subtitulo("Variables"),
        Parrafo("Las variables tienen tipo fijo: se declaran con «pista» indicando el tipo y el valor inicial. Para cambiarlas basta con asignarles un valor compatible. Con «hecho» se declaran constantes que no pueden cambiar."),
        Nota("Una pista declarada con sin_pista (por ejemplo entero(valor: sin_pista)) no se puede usar en operaciones hasta que reciba un valor."),

        Subtitulo("Alcance"),
        Lista((
            "Global: lo declarado fuera de funciones y del caso se ve en todo el archivo.",
            "Local: lo declarado dentro de una escena, un proceso, un evaluar si, un rastrear o un seguir mientras solo existe dentro de su bloque (de «inicio» a «fin!»).",
        )),

        Subtitulo("Cómo se evalúan las expresiones"),
        Parrafo("Las operaciones aritméticas respetan el orden de sus argumentos y se pueden anidar. Las condiciones relacionales y lógicas se evalúan de izquierda a derecha."),

        Subtitulo("Condiciones y ciclos"),
        Parrafo("Una condición debe dar culpable o NoCulpable. «evaluar si» y «sino evaluar» ejecutan su bloque solo si se cumple; «seguir mientras» lo repite mientras se cumpla; «rastrear» avanza un contador de 1 en 1."),

        Subtitulo("Funciones y retorno"),
        Parrafo("Se llaman con «resolver». Una escena debe devolver, con «concluir», un valor compatible con su tipo. Un proceso termina en «fin!» y no puede usar «concluir»."),

        Subtitulo("Importaciones"),
        Parrafo("«#expediente <archivo.eng>» trae al archivo las funciones de otro. Se resuelven antes de compilar el código principal (mira la sección Importaciones)."),

        Subtitulo("Manejo de errores"),
        Parrafo("Enigma no lanza excepciones genéricas: cada fallo es una «Indicio Fallido de Razonamiento» con el tipo de error, el archivo, la línea, la descripción y una posible causa."),
        Nota("Para entrenar el razonamiento, el IDE primero da un indicio para que busques el error por tu cuenta. Si vuelves a cometer el mismo error, muestra la explicación completa."),
        Lista((
            "Errores léxicos y sintácticos: un símbolo desconocido, un «!» olvidado, un bloque sin cerrar.",
            "Errores semánticos: variable no declarada, tipos incompatibles, reasignar un hecho, llamar con argumentos de más o de menos.",
            "Errores de importación: archivo inexistente, función duplicada, importación circular.",
            "Errores de ejecución: dividir entre cero, índice fuera del rango, dato que no corresponde al tipo.",
        )),
    ),
)


# --------------------------------------------------------------------------- #
# 7. Tipos de datos
# --------------------------------------------------------------------------- #

TIPOS = Seccion(
    id="tipos",
    titulo="Tipos de datos",
    resumen="Cinco tipos simples y dos compuestos.",
    bloques=(
        Subtitulo("Tipos simples"),
        Ficha(
            "entero",
            "pista edad = entero(valor: 15)!",
            "Números sin decimales, positivos o negativos, para conteos.",
            "Aritméticas (conectar, descartar, intensificar, repartir) y relacionales.",
            "No acepta decimales. Es el único tipo válido como contador de «rastrear».",
        ),
        Ficha(
            "decimal",
            "pista precio = decimal(valor: 15.5)!",
            "Cantidades continuas o medidas con decimales.",
            "Aritméticas y relacionales. Un entero se acepta donde se espera un decimal.",
            "No puede usarse como contador de «rastrear».",
        ),
        Ficha(
            "expresion",
            "pista frase = expresion(valor: 'Estaba en el baño.')!",
            "Texto entre comillas simples.",
            "Salida (revelar), lectura (consultar) y comparación con == y <>.",
            "No se puede cambiar una sola letra: para modificarlo se reemplaza el texto completo. No admite operaciones aritméticas.",
        ),
        Ficha(
            "declaracion",
            "pista culpa = declaracion(valor: culpable)!",
            "Verdad lógica: culpable (verdadero) o NoCulpable (falso).",
            "Lógicas (y, o, no) e igualdad o diferencia.",
            "Solo puede tomar los valores culpable o NoCulpable.",
        ),
        Ficha(
            "sin_pista (nulo)",
            "pista nota = entero(valor: sin_pista)!",
            "La ausencia de valor, o una premisa todavía sin resolver.",
            "Comparar con == sin_pista o <> sin_pista para saber si ya tiene valor.",
            "No se puede operar aritméticamente ni usar en una condición hasta asignarle un valor válido.",
        ),

        Subtitulo("Tipos compuestos"),
        Ficha(
            "pistas (lista)",
            "pista nums = pistas entero[2, 4, 6]!",
            "Colección ordenada de elementos del mismo tipo. Se accede por posición, empezando en 0: nums[0].",
            "Leer un elemento (nums[1]), cambiarlo (nums[1] = 40!), pasarla como parámetro a funciones.",
            "No se pueden mezclar tipos. Un índice fuera del rango es un error.",
        ),
        Ficha(
            "tablero (matriz)",
            "pista celdas = tablero entero[4][4]!",
            "Datos en filas y columnas, como una cuadrícula. Se accede con dos índices: celdas[fila][columna].",
            "Leer y cambiar celdas, y recorrerlo con ciclos «rastrear» anidados.",
            "Se deben indicar filas y columnas al crearlo. No se pueden mezclar tipos. Salirse de sus dimensiones es un error.",
        ),
        Codigo(
            "caso Compuestos abierto\n"
            "    pista nums = pistas entero[2, 4, 6]!\n"
            "    nums[1] = 40!\n"
            "    revelar('Segundo elemento:', nums[1])!\n"
            "\n"
            "    pista celdas = tablero entero[2][2]!\n"
            "    celdas[0][1] = 7!\n"
            "    revelar('Celda [0][1]:', celdas[0][1])!\n"
            "caso Compuestos cerrado!",
            "Listas y tableros", ejecutable=True,
        ),
    ),
)


# --------------------------------------------------------------------------- #
# 8. Importaciones
# --------------------------------------------------------------------------- #

IMPORTACIONES = Seccion(
    id="importaciones",
    titulo="Importaciones",
    resumen="Usar funciones de otros archivos del proyecto.",
    bloques=(
        Parrafo("Un proyecto puede tener varios archivos. Con «#expediente» un archivo usa las funciones (escenas y procesos) de otro."),
        Codigo("#expediente <archivo.eng>", "Sintaxis", plantilla=True),

        Subtitulo("Cómo funciona"),
        Lista((
            "Va al inicio del archivo, antes de todo lo demás, y no lleva «!».",
            "El archivo se busca junto al archivo que escribe la importación. También sirven rutas como <carpeta/otro.eng> o <../lib/util.eng>.",
            "Solo se importan funciones, no las variables globales.",
            "Las importaciones se resuelven antes de compilar, y los archivos importados también se revisan.",
            "Todo archivo lleva su bloque «caso», pero solo se ejecuta el del archivo principal.",
        )),

        Subtitulo("Ejemplo con dos archivos"),
        Parrafo("Archivo pistas.eng:"),
        Codigo(
            "escena EsSospechoso(nombre: expresion)::declaracion inicio\n"
            "    evaluar si (nombre == 'Alex') inicio\n"
            "        concluir culpable!\n"
            "    fin!\n"
            "    concluir NoCulpable!\n"
            "fin!\n"
            "\n"
            "caso Pistas abierto\n"
            "caso Pistas cerrado!",
            "pistas.eng",
        ),
        Parrafo("Archivo principal (caso-042.eng):"),
        Codigo(
            "#expediente <pistas.eng>\n"
            "\n"
            "caso Caso042 abierto\n"
            "    pista sospechoso = expresion(valor: 'Alex')!\n"
            "    revelar('¿Es sospechoso?', resolver EsSospechoso(sospechoso))!\n"
            "caso Caso042 cerrado!",
            "caso-042.eng",
        ),

        Subtitulo("Qué se valida"),
        Lista((
            "Que el archivo importado exista.",
            "Que la función exista y se llame con la cantidad y el tipo de argumentos correctos.",
            "Que no haya funciones duplicadas entre archivos.",
            "Que no haya importaciones circulares (A importa B y B importa A).",
            "Que los archivos importados no tengan errores. Si los tienen, el error indica el archivo donde ocurren.",
        )),
    ),
)


# --------------------------------------------------------------------------- #
# 9. Ejemplos
# --------------------------------------------------------------------------- #

EJEMPLOS = Seccion(
    id="ejemplos",
    titulo="Ejemplos",
    resumen="Programas completos para insertar y probar.",
    bloques=(
        Parrafo("Pulsa «Insertar en el editor» para copiar un ejemplo en el archivo abierto, y ejecútalo con Ctrl+Enter."),
        Parrafo("También puedes abrir los acertijos completos desde la carpeta «ejemplos» del proyecto."),

        Codigo(
            "caso HolaDetective abierto\n"
            "    revelar('Hola, detective.')!\n"
            "caso HolaDetective cerrado!",
            "Hola, detective", ejecutable=True,
        ),
        Codigo(
            "caso Caso042 abierto\n"
            "    pista sospechoso = expresion(valor: 'Alex')!\n"
            "    pista coartada = expresion(valor: 'biblioteca')!\n"
            "\n"
            "    evaluar si (coartada == 'biblioteca') inicio\n"
            "        revelar('La coartada coincide.')!\n"
            "    fin!\n"
            "    sino inicio\n"
            "        revelar('Indicio fallido: revisa la coartada.')!\n"
            "    fin!\n"
            "caso Caso042 cerrado!",
            "La coartada", ejecutable=True,
        ),
        Codigo(
            "caso Edad abierto\n"
            "    pista edad = entero(valor: 0)!\n"
            "    revelar('Escribe tu edad:')!\n"
            "    consultar(edad)!\n"
            "\n"
            "    evaluar si (edad < 18) inicio\n"
            "        revelar('Eres menor de edad.')!\n"
            "    fin!\n"
            "    sino inicio\n"
            "        revelar('Eres mayor de edad.')!\n"
            "    fin!\n"
            "caso Edad cerrado!",
            "Preguntar un dato", ejecutable=True, entradas=("25",),
        ),
        Codigo(
            "escena CalcularPromedio(a: entero, b: entero)::decimal inicio\n"
            "    concluir repartir(conectar(a, b), 2)!\n"
            "fin!\n"
            "\n"
            "caso Promedio abierto\n"
            "    pista nota1 = entero(valor: 15)!\n"
            "    pista nota2 = entero(valor: 18)!\n"
            "    revelar('El promedio es', resolver CalcularPromedio(nota1, nota2))!\n"
            "caso Promedio cerrado!",
            "Promedio de notas", ejecutable=True,
        ),
        Codigo(
            "caso Tabla abierto\n"
            "    rastrear fila desde 1 hasta 3 inicio\n"
            "        rastrear columna desde 1 hasta 3 inicio\n"
            "            revelar(fila, 'x', columna, '=', intensificar(fila, columna))!\n"
            "        fin!\n"
            "    fin!\n"
            "caso Tabla cerrado!",
            "Ciclos anidados", ejecutable=True,
        ),
        Codigo(
            "caso Sospechosos abierto\n"
            "    pista lista = pistas expresion['Alex', 'Bea', 'Carlos']!\n"
            "    rastrear i desde 0 hasta 2 inicio\n"
            "        revelar('Sospechoso', conectar(i, 1), ':', lista[i])!\n"
            "    fin!\n"
            "caso Sospechosos cerrado!",
            "Recorrer una lista", ejecutable=True,
        ),
        Codigo(
            "caso Descartes abierto\n"
            "    pista culpable1 = declaracion(valor: culpable)!\n"
            "    pista huellas = entero(valor: 3)!\n"
            "\n"
            "    evaluar si ((huellas >= 3) y (culpable1 == culpable)) inicio\n"
            "        revelar('Caso resuelto: hay pruebas suficientes.')!\n"
            "    fin!\n"
            "    sino inicio\n"
            "        revelar('Faltan pistas.')!\n"
            "    fin!\n"
            "caso Descartes cerrado!",
            "Deducción con lógica", ejecutable=True,
        ),
        Codigo(
            "escena CalcularCodigo(digitouno: entero, digitodos: entero)::entero inicio\n"
            "    concluir conectar(intensificar(digitouno, 10), digitodos)!\n"
            "fin!\n"
            "\n"
            "caso CajaFuerte abierto\n"
            "    revelar('La caja fuerte solo acepta un codigo de dos cifras.')!\n"
            "    revelar('Primera pista: el doble de 3.')!\n"
            "    revelar('Segunda pista: las 12 campanadas menos 8.')!\n"
            "    pista digitouno = entero(valor: 0)!\n"
            "    pista digitodos = entero(valor: 0)!\n"
            "    digitouno = intensificar(3, 2)!\n"
            "    digitodos = descartar(12, 8)!\n"
            "    pista codigo = resolver CalcularCodigo(digitouno, digitodos)!\n"
            "\n"
            "    revelar('Codigo calculado:', codigo)!\n"
            "    evaluar si (codigo == 64) inicio\n"
            "        revelar('La caja se abre. ¡La torre conserva su secreto!')!\n"
            "    fin!\n"
            "    sino inicio\n"
            "        revelar('La caja permanece cerrada. Revisa las pistas.')!\n"
            "    fin!\n"
            "caso CajaFuerte cerrado!",
            "Acertijo: la caja fuerte de la torre del reloj", ejecutable=True,
        ),
        Codigo(
            "escena EsCulpable(coartada: declaracion, huella: declaracion)::declaracion inicio\n"
            "    concluir coartada y huella!\n"
            "fin!\n"
            "\n"
            "caso GaleriaDelMuseo abierto\n"
            "    revelar('Una obra desaparecio de la galeria del museo.')!\n"
            "    pista tieneCoartada = declaracion(valor: culpable)!\n"
            "    pista huellaCoincide = declaracion(valor: NoCulpable)!\n"
            "    pista esSospechoso = resolver EsCulpable(no(tieneCoartada), huellaCoincide)!\n"
            "\n"
            "    evaluar si (esSospechoso == culpable) inicio\n"
            "        revelar('El sospechoso A pudo cometer el robo.')!\n"
            "    fin!\n"
            "    sino inicio\n"
            "        revelar('El sospechoso A queda descartado.')!\n"
            "    fin!\n"
            "\n"
            "    tieneCoartada = NoCulpable!\n"
            "    huellaCoincide = culpable!\n"
            "    esSospechoso = resolver EsCulpable(no(tieneCoartada), huellaCoincide)!\n"
            "\n"
            "    evaluar si (esSospechoso == culpable) inicio\n"
            "        revelar('El sospechoso B es el culpable. ¡El caso esta resuelto!')!\n"
            "    fin!\n"
            "caso GaleriaDelMuseo cerrado!",
            "Acertijo: el sospechoso de la galería", ejecutable=True,
        ),
    ),
)


PRACTICA = Seccion(
    id="practica",
    titulo="Casos de práctica",
    resumen="Recibe un caso y escribe tú mismo la solución.",
    bloques=(
        Parrafo("Estos apartados presentan el desafío, pero no incluyen la solución completa. Pulsa «Insertar en el editor», cambia el código de inicio y compila con Ctrl+Enter."),
        Subtitulo("Caso 1: La caja de la torre"),
        Lista((
            "Una caja fuerte tiene un código de dos cifras.",
            "El primer dígito es el doble de 3.",
            "El segundo dígito son las 12 campanadas menos 8.",
            "Calcula el código y revela si es igual a 64.",
        )),
        Nota("Objetivo: usar operaciones aritméticas, una decisión evaluar si / sino y revelar."),
        Codigo(
            "caso CajaDePractica abierto\n"
            "    { Calcula el primer digito a partir de 3. }\n"
            "    pista primero = entero(valor: 0)!\n"
            "\n"
            "    { Calcula el segundo digito a partir de 12. }\n"
            "    pista segundo = entero(valor: 0)!\n"
            "\n"
            "    { Usa los dos digitos para formar el codigo. }\n"
            "    pista codigo = entero(valor: 0)!\n"
            "\n"
            "    revelar('Tu codigo es:', codigo)!\n"
            "caso CajaDePractica cerrado!",
            "Reto: abre la caja fuerte", ejecutable=False,
        ),
        Subtitulo("Caso 2: El sospechoso de la galería"),
        Lista((
            "Investiga los sospechosos A y B.",
            "Un sospechoso es culpable solo si no tiene coartada y su huella coincide.",
            "El sospechoso A sí tiene coartada y su huella no coincide.",
            "El sospechoso B no tiene coartada y su huella sí coincide.",
        )),
        Nota("Objetivo: usar declaracion, los operadores no / y, una decisión y revelar el sospechoso correcto."),
        Codigo(
            "caso SospechosoDePractica abierto\n"
            "    pista sospechosoA_coartada = declaracion(valor: culpable)!\n"
            "    pista sospechosoA_huella = declaracion(valor: NoCulpable)!\n"
            "\n"
            "    pista sospechosoB_coartada = declaracion(valor: NoCulpable)!\n"
            "    pista sospechosoB_huella = declaracion(valor: culpable)!\n"
            "\n"
            "    { Evalua cada sospechoso con: no(tieneCoartada) y huellaCoincide. }\n"
            "    revelar('Investiga al sospechoso A y despues al sospechoso B.')!\n"
            "caso SospechosoDePractica cerrado!",
            "Reto: encuentra al culpable", ejecutable=False,
        ),
        Subtitulo("Caso 3: La suma del cofre"),
        Lista((
            "El cofre se abrirá con la suma de los números secretos del 1 al 6.",
            "Recorre esas cifras con un ciclo rastrear.",
            "Acumula cada cifra en una pista llamada total.",
            "El cofre se abre únicamente si el total es 21.",
        )),
        Nota("Objetivo: combinar ciclo, acumulación y condición. Este reto exige mantener el estado entre varias repeticiones."),
        Codigo(
            "caso CofreDePractica abierto\n"
            "    pista total = entero(valor: 0)!\n"
            "\n"
            "    { Recorre los numeros secretos del 1 al 6 y acumula cada uno. }\n"
            "    rastrear numero desde 1 hasta 6 inicio\n"
            "        { Asigna aqui la operacion necesaria para actualizar total. }\n"
            "    fin!\n"
            "\n"
            "    revelar('Suma encontrada:', total)!\n"
            "caso CofreDePractica cerrado!",
            "Reto: suma del cofre", ejecutable=False,
        ),
        Subtitulo("Caso 4: El camino del tablero sellado"),
        Lista((
            "Un mapa contiene filas de pistas representadas por una matriz.",
            "Coloca los valores 2, 5, 4, 8, 3 y 1 según las instrucciones del tablero.",
            "Recorre cada casilla con ciclos anidados.",
            "Solo se abre el camino cuya suma de las seis casillas sea 23.",
        )),
        Nota("Objetivo: recorrer una matriz, modificar varias casillas y comprobar el resultado con ciclos anidados."),
        Codigo(
            "caso TableroDePractica abierto\n"
            "    pista mapa = tablero entero[2][3]!\n"
            "\n"
            "    { Asigna a las seis casillas los valores indicados por el acertijo. }\n"
            "    pista suma = entero(valor: 0)!\n"
            "\n"
            "    rastrear fila desde 0 hasta 1 inicio\n"
            "        rastrear columna desde 0 hasta 2 inicio\n"
            "            { Suma aqui mapa[fila][columna] al total. }\n"
            "        fin!\n"
            "    fin!\n"
            "\n"
            "    revelar('Suma del camino:', suma)!\n"
            "caso TableroDePractica cerrado!",
            "Reto: abre el tablero sellado", ejecutable=False,
        ),
    ),
)


# --------------------------------------------------------------------------- #
# 10. Atajos y colores
# --------------------------------------------------------------------------- #

ATAJOS = Seccion(
    id="atajos",
    titulo="Atajos y colores",
    resumen="Teclas del IDE y significado de los colores.",
    bloques=(
        Subtitulo("Atajos de teclado"),
        Lista((
            "Ctrl+Enter  compilar y ejecutar",
            "Ctrl+S  guardar el archivo",
            "Ctrl+F  buscar en el archivo (Enter siguiente, Mayús+Enter anterior, Esc cierra)",
            "Ctrl+W  cerrar la pestaña",
            "Ctrl+O  abrir una carpeta",
            "F1  mostrar u ocultar esta guía",
            "Clic central sobre una pestaña  cerrarla",
        )),
        Subtitulo("Colores del editor"),
        Lista((
            "Morado: palabras clave (pista, caso, evaluar…)",
            "Amarillo: tipos (entero, expresion…)",
            "Naranja claro: texto y rutas de importación",
            "Verde: nombres de pistas y funciones",
            "Naranja: números",
            "Gris cursiva: comentarios",
        )),
        Nota("Si un error aparece en el panel de salida, la primera vez verás solo una pista. Corrige y vuelve a intentar: si repites el mismo error, verás la explicación completa."),
    ),
)


SECCIONES: tuple[Seccion, ...] = (
    PALABRAS, SINTAXIS, CONTROL, FUNCIONES, OPERACIONES,
    SEMANTICA, TIPOS, IMPORTACIONES, EJEMPLOS, PRACTICA, ATAJOS,
)

POR_ID = {s.id: s for s in SECCIONES}
