"""Los 20 programas de prueba del enunciado (seccion 18), con su objetivo y resultado esperado.

El resultado esperado se dedujo a mano a partir de las reglas del lenguaje, no de lo que el
compilador devuelve. Los lee `tests/test_programas_prueba.py` y `herramientas/informe_pruebas.py`.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Caso:
    id: str
    categoria: str
    objetivo: str
    principal: str                      # ruta respecto a tests/programas_prueba
    entradas: tuple[str, ...] = ()      # lo que se escribe cuando el programa usa consultar
    # Si el programa es valido: las lineas exactas que debe imprimir.
    salida: tuple[str, ...] = ()
    # Si debe fallar: clase del error, archivo, linea y un fragmento de la descripcion.
    error: str = ""
    archivo: str = ""
    linea: int = 0
    fragmento: str = ""

    @property
    def es_valido(self) -> bool:
        return not self.error


VALIDOS = "Programa válido"
SINTACTICO = "Error sintáctico"
SEMANTICO = "Error semántico"
IMPORTACION = "Importación"
COMPLETA = "Prueba completa"

CASOS: tuple[Caso, ...] = (
    # ---------------------------------------------------------------- válidos
    Caso("V1", VALIDOS, "Declarar variables y constantes, usar las cuatro operaciones aritméticas y leer un dato con consultar.",
         "validos/V1_aritmetica.eng", entradas=("4",),
         salida=("Suma: 16", "Resta: 8", "Producto: 48", "Division: 3.0", "Detective: Holmes")),
    Caso("V2", VALIDOS, "Ejecutar un condicional simple, uno con alternativas (sino evaluar, sino) y uno múltiple (suceso).",
         "validos/V2_condicionales.eng",
         salida=("Puede entrar", "Justo 18", "Opcion 3")),
    Caso("V3", VALIDOS, "Ejecutar un ciclo rastrear (for) y un ciclo seguir mientras (while).",
         "validos/V3_ciclos.eng",
         salida=("Suma de 1 a 5: 15", "Cuenta regresiva 3", "Cuenta regresiva 2", "Cuenta regresiva 1")),
    Caso("V4", VALIDOS, "Definir y llamar una escena (con retorno) y un proceso (sin retorno) con parámetros.",
         "validos/V4_funciones.eng",
         salida=("Cuadrado de 7: 49", "Detective Watson listo")),
    Caso("V5", VALIDOS, "Usar una lista, un tablero, los operadores lógicos y el valor nulo sin_pista.",
         "validos/V5_compuestos_y_logica.eng",
         salida=("Lista: 2 40 6", "Tablero: 7 9", "b es falso", "Al menos uno es verdadero",
                 "No son ambos verdaderos", "Aun sin pista")),
    # ------------------------------------------------------------ sintácticos
    Caso("S1", SINTACTICO, "Detectar una sentencia sin el terminador ! y señalar la línea donde falta.",
         "sintacticos/S1_falta_terminador.eng",
         error="ErrorSintactico", archivo="S1_falta_terminador.eng", linea=3, fragmento="SELLO"),
    Caso("S2", SINTACTICO, "Detectar un bloque inicio al que le falta su fin!.",
         "sintacticos/S2_bloque_sin_fin.eng",
         error="ErrorSintactico", archivo="S2_bloque_sin_fin.eng", linea=6, fragmento="No se esperaba"),
    Caso("S3", SINTACTICO, "Detectar un paréntesis que no se cierra.",
         "sintacticos/S3_parentesis_sin_cerrar.eng",
         error="ErrorSintactico", archivo="S3_parentesis_sin_cerrar.eng", linea=3, fragmento="PARENTESIS_DER"),
    Caso("S4", SINTACTICO, "Detectar un condicional mal escrito (evaluar sin la palabra si).",
         "sintacticos/S4_evaluar_sin_si.eng",
         error="ErrorSintactico", archivo="S4_evaluar_sin_si.eng", linea=4, fragmento="SI"),
    Caso("S5", SINTACTICO, "Detectar un caso principal que se abre y nunca se cierra.",
         "sintacticos/S5_caso_sin_cierre.eng",
         error="ErrorSintactico", archivo="S5_caso_sin_cierre.eng", linea=3, fragmento="FIN_DE_ARCHIVO"),
    # ------------------------------------------------------------- semánticos
    Caso("M1", SEMANTICO, "Detectar el uso de una variable que no fue declarada.",
         "semanticos/M1_variable_no_declarada.eng",
         error="ErrorSemantico", archivo="M1_variable_no_declarada.eng", linea=3, fragmento="sospechoso"),
    Caso("M2", SEMANTICO, "Detectar la reasignación de una constante declarada con hecho.",
         "semanticos/M2_reasignar_hecho.eng",
         error="ErrorSemantico", archivo="M2_reasignar_hecho.eng", linea=4, fragmento="hecho"),
    Caso("M3", SEMANTICO, "Detectar la asignación de un texto a una pista de tipo entero.",
         "semanticos/M3_tipos_incompatibles.eng",
         error="ErrorSemantico", archivo="M3_tipos_incompatibles.eng", linea=4, fragmento="entero"),
    Caso("M4", SEMANTICO, "Detectar una pista declarada dos veces en el mismo alcance.",
         "semanticos/M4_declaracion_duplicada.eng",
         error="ErrorSemantico", archivo="M4_declaracion_duplicada.eng", linea=4, fragmento="ya fue declarada"),
    Caso("M5", SEMANTICO, "Detectar una operación aritmética sobre un valor sin_pista.",
         "semanticos/M5_operar_sin_pista.eng",
         error="ErrorSemantico", archivo="M5_operar_sin_pista.eng", linea=4, fragmento="aritm"),
    # ----------------------------------------------------------- importaciones
    Caso("I1", IMPORTACION, "Detectar la importación de un archivo que no existe.",
         "importacion/I1_archivo_inexistente/principal.eng",
         error="ErrorDeImportacion", archivo="principal.eng", linea=2, fragmento="herramientas.eng"),
    Caso("I2", IMPORTACION, "Detectar una llamada a una función importada con la cantidad de argumentos incorrecta.",
         "importacion/I2_argumentos_incorrectos/principal.eng",
         error="ErrorSemantico", archivo="principal.eng", linea=5, fragmento="3 argumento"),
    Caso("I3", IMPORTACION, "Detectar un error dentro de un archivo importado e indicar el archivo donde ocurre.",
         "importacion/I3_error_en_importado/principal.eng",
         error="ErrorSemantico", archivo="calculos.eng", linea=2, fragmento="factor"),
    Caso("C1", IMPORTACION, "Detectar una importación circular (a.eng importa b.eng y b.eng importa a.eng).",
         "importacion/C1_circular/principal.eng",
         error="ErrorDeImportacion", archivo="b.eng", linea=1, fragmento="vuelve a un archivo ya en proceso"),
    # --------------------------------------------------------- prueba completa
    Caso("P1", COMPLETA, "Resolver un caso de deducción con varios archivos: importación, tablero, ciclo, funciones, "
                         "lógica, valor nulo y lectura de la respuesta del estudiante.",
         "completa/P1_caso_museo/principal.eng", entradas=("1",),
         salida=("Una obra desaparecio del museo. Hay tres sospechosos.",
                 "Sospechoso 0 : descartado", "Sospechoso 1 : culpable", "Sospechoso 2 : descartado",
                 "Culpables encontrados: 1",
                 "Quien crees que es el culpable?", "Correcto: has resuelto el caso.")),
)

POR_ID = {caso.id: caso for caso in CASOS}
