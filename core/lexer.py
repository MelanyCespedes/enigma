from core.tokens import Token, TipoToken, PALABRAS_RESERVADAS
from core.errors import ErrorLexico

SIMBOLOS_UN_CARACTER = {
    ",": TipoToken.COMA,
    ":": TipoToken.DOS_PUNTOS,
    "(": TipoToken.PARENTESIS_IZQ,
    ")": TipoToken.PARENTESIS_DER,
    "[": TipoToken.CORCHETE_IZQ,
    "]": TipoToken.CORCHETE_DER,
}

def tokenizar(codigo_fuente: str, nombre_archivo: str)-> list[Token]:
    tokens: list[Token] = []
    posicion = 0
    linea = 1
    columna = 1

    while posicion < len(codigo_fuente):
        caracter = codigo_fuente[posicion]

        if  caracter == "\n":
            linea += 1
            columna = 1
            posicion += 1
            continue

        if caracter.isspace():
            posicion += 1
            columna += 1
            continue

        if caracter == "{":
            linea_apertura = linea
            columna_apertura = columna
            posicion += 1
            columna += 1

            while posicion < len(codigo_fuente) and codigo_fuente[posicion] != "}":
                if codigo_fuente[posicion] == "\n":
                    linea += 1
                    columna = 1
                else:
                    columna += 1
                posicion += 1

            if posicion >= len(codigo_fuente):
                raise ErrorLexico(
                    tipo="Comentario sin cerrar",
                    archivo=nombre_archivo,
                    linea=linea_apertura,
                    indicio="Hay un comentario que nunca se cierra.",
                    descripcion=(
                        f"El comentario abierto con '{{' en la linea {linea_apertura}, "
                        f"columna {columna_apertura} no tiene su '}}' de cierre."
                    ),
                    causa_posible="Revisa si te falto una llave de cierre '}'.",
                )

            posicion += 1
            columna += 1
            continue

        if caracter == "}":
            raise ErrorLexico(
                tipo="Cierre de comentario sin apertura",
                archivo=nombre_archivo,
                linea=linea,
                indicio="Hay una llave de cierre '}' que no corresponde a ningun comentario.",
                descripcion="Se encontro '}' sin un '{' que abra un comentario antes.",
                causa_posible="Revisa si te falto la llave de apertura '{' o si sobra esta '}'.",
            )

        if caracter == "!":
            tokens.append(Token(TipoToken.SELLO, "!",None, linea, columna))
            posicion += 1
            columna +=1
            continue

        if caracter == "=":
            if posicion + 1 < len(codigo_fuente) and codigo_fuente[posicion + 1] == "=":
                tokens.append(Token(TipoToken.IGUAL_IGUAL, "==", None, linea, columna))
                posicion += 2
                columna += 2
            else:
                tokens.append(Token(TipoToken.IGUAL, "=", None, linea, columna))
                posicion += 1
                columna += 1
            continue

        if caracter == "<" and posicion + 1 < len(codigo_fuente) and codigo_fuente[posicion + 1]  == ">":
            tokens.append(Token(TipoToken.DIFERENTE, "<>", None, linea, columna))
            posicion += 2
            columna +=2
            continue

        if caracter == ">" and posicion + 1 < len(codigo_fuente) and codigo_fuente[posicion + 1]  == "=":
            tokens.append(Token(TipoToken.MAYOR_IGUAL, ">=", None, linea, columna))
            posicion += 2
            columna +=2
            continue

        if caracter == "<" and posicion + 1 < len(codigo_fuente) and codigo_fuente[posicion + 1]  == "=":
            tokens.append(Token(TipoToken.MENOR_IGUAL, "<=", None, linea, columna))
            posicion += 2
            columna +=2
            continue

        if caracter == ">":
            tokens.append(Token(TipoToken.MAYOR, ">",None, linea, columna))
            posicion += 1
            columna +=1
            continue

        if caracter == "<":
            tokens.append(Token(TipoToken.MENOR, "<",None, linea, columna))
            posicion += 1
            columna +=1
            continue

        if caracter in SIMBOLOS_UN_CARACTER:
            tokens.append(Token(SIMBOLOS_UN_CARACTER[caracter], caracter, None, linea, columna))
            posicion += 1
            columna += 1
            continue

        if caracter.isalpha() or caracter == "_":
            inicio = posicion
            while posicion < len(codigo_fuente) and (codigo_fuente[posicion].isalnum() or codigo_fuente[posicion] == "_"):
                posicion += 1
            lexema = codigo_fuente[inicio:posicion]
            columna_inicial = columna
            columna += len(lexema)

            tipo = PALABRAS_RESERVADAS.get(lexema, TipoToken.IDENTIFICADOR)
            tokens.append(Token(tipo, lexema, None, linea, columna_inicial))
            continue

        if caracter.isdigit():
            inicio = posicion
            columna_inicial = columna
            es_decimal = False
            while posicion < len(codigo_fuente) and (
                codigo_fuente[posicion].isdigit() or codigo_fuente[posicion] == "."
            ):
                if codigo_fuente[posicion] == ".":
                    es_decimal =True
                posicion += 1
            lexema = codigo_fuente[inicio:posicion]
            columna += len(lexema)

            if es_decimal:
                tokens.append(Token(TipoToken.NUMERO_DECIMAL, lexema, float(lexema), linea, columna_inicial))
            else:
                tokens.append(Token(TipoToken.NUMERO_ENTERO, lexema, int(lexema), linea, columna_inicial))
            continue

        if caracter == "'":
                    columna_inicial = columna
                    posicion += 1
                    columna += 1
                    inicio = posicion

                    while posicion < len(codigo_fuente) and codigo_fuente[posicion] != "'":
                        if codigo_fuente[posicion] == "\n":
                            linea += 1
                            columna = 1
                        else:
                            columna += 1
                        posicion += 1

                    if posicion >= len(codigo_fuente):
                        raise ErrorLexico(
                            tipo="Cadena de texto sin cerrar",
                            archivo=nombre_archivo,
                            linea=linea,
                            indicio="Hay una cadena de texto que nunca se cierra.",
                            descripcion="Se esperaba una comilla simple ' para cerrar la cadena de texto y no se encontro antes del final del archivo.",
                            causa_posible="Revisa si te falto una comilla simple de cierre.",
                        )

                    lexema = codigo_fuente[inicio:posicion]
                    tokens.append(Token(TipoToken.CADENA_TEXTO, lexema, lexema, linea, columna_inicial))
                    posicion += 1
                    columna += 1
                    continue

        if caracter == "#":
            tokens.append(Token(TipoToken.NUMERAL, "#", None, linea, columna))
            posicion += 1
            columna += 1

            while posicion < len(codigo_fuente) and codigo_fuente[posicion].isspace() and codigo_fuente[posicion] != "\n":
                posicion += 1
                columna += 1

            inicio_palabra = posicion
            columna_palabra = columna
            while posicion < len(codigo_fuente) and codigo_fuente[posicion].isalpha():
                posicion += 1
                columna += 1
            palabra = codigo_fuente[inicio_palabra:posicion]

            if palabra != "expediente":
                raise ErrorLexico(
                    tipo="Importacion mal formada.",
                    archivo=nombre_archivo,
                    linea=linea,
                    indicio="Despues de '#' se esperaba la palabra 'expediente'.",
                    descripcion=f"Se encontró '{palabra}' en lugar de 'expediente' despues de '#'.",
                    causa_posible="Revisa que la directiva de importacion tenga la forma #expediente <archivo.eng>.",
                )

            tokens.append(Token(TipoToken.EXPEDIENTE, "expediente", None, linea, columna_palabra))

            while posicion < len(codigo_fuente) and codigo_fuente[posicion].isspace() and codigo_fuente[posicion] != "\n":
                posicion += 1
                columna += 1

            if posicion >= len(codigo_fuente) or codigo_fuente[posicion] != "<":
                raise ErrorLexico(
                    tipo="Importacion mal formada.",
                    archivo=nombre_archivo,
                    linea=linea,
                    indicio="Se esperaba '<' despues de 'expediente'.",
                    descripcion="La directiva de importación debe tener forma #expediente <archivo.eng>.",
                    causa_posible="Revisa que no te falte el '<' antes del nombre del archivo.",
                )

            posicion += 1
            columna += 1
            columna_inicial_ruta = columna
            inicio_ruta = posicion

            while posicion < len(codigo_fuente) and codigo_fuente[posicion] != ">":
                posicion += 1
                columna += 1

            if posicion >= len(codigo_fuente):
                raise ErrorLexico(
                    tipo="Importacion mal formada",
                    archivo=nombre_archivo,
                    linea=linea,
                    indicio="La ruta del archivo importado nunca se cierra.",
                    descripcion="Se esperaba '>' para cerrar la ruta del archivo importado.",
                    causa_posible="Revisa si faltó  el '>' de cierre",
                )

            ruta = codigo_fuente[inicio_ruta:posicion]
            tokens.append(Token(TipoToken.RUTA_ARCHIVO, ruta, ruta, linea, columna_inicial_ruta))
            posicion += 1
            columna += 1
            continue

        raise ErrorLexico(
            tipo ="Caracter no reconocido",
            archivo=nombre_archivo,
            linea=linea,
            indicio="Hay un simbolo que Enigma no reconoce en tu caso.",
            descripcion=f"El caracter '{caracter}' no es valido en Enigma.",
            causa_posible="Revisa si escribiste un simbolo que no existe en este lenguaje.",
        )

    tokens.append(Token(TipoToken.FIN_DE_ARCHIVO, "", None, linea, columna))
    return tokens