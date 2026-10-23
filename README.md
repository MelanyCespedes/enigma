<p align="center">
  <img src="docs/logo_enigma.png" alt="Logo de Enigma" width="220">
</p>

# Enigma

Lenguaje de programación temático (detectives y casos) para entrenar el razonamiento
lógico y matemático. Incluye su propio compilador/intérprete y un IDE gráfico.
Proyecto del curso Paradigmas de Programación (Universidad Nacional, Sede Regional Brunca).

> *"Todo dato es una pista. Toda operación es un paso más. Todo programa es un caso que se resuelve con lógica."*

Los archivos de Enigma usan la extensión **`.eng`**.

**Integrantes:** Melany Céspedes Sánchez y Alisson Cordero Fonseca.

## Cómo arrancar

Requiere **Python 3.10 o superior**. El IDE usa `tkinter`, que ya viene incluido con Python
(en Linux puede hacer falta `sudo apt install python3-tk`).

```bash
pip install -r requirements.txt     # solo pytest, para las pruebas
python main.py                      # abre el IDE
python main.py ejemplo_gui          # abre el IDE con una carpeta como proyecto
```

## Un programa de ejemplo

```
{ Los comentarios van entre llaves }
escena CalcularPromedio(a: entero, b: entero)::decimal inicio
    concluir repartir(conectar(a, b), 2)!
fin!

caso CasoPromedio abierto
    pista nota1 = entero(valor: 15)!
    hecho notaMinima = entero(valor: 10)!

    evaluar si (nota1 < notaMinima) inicio
        revelar('El sospechoso reprobó.')!
    fin!
    sino inicio
        revelar('El sospechoso aprobó.')!
    fin!

    rastrear intento desde 1 hasta 3 inicio
        revelar('Intento número:', intento)!
    fin!
caso CasoPromedio cerrado!
```

Resumen de la sintaxis

| Concepto | Palabras reservadas |
|---|---|
| Variables y constantes | `pista`, `hecho` |
| Tipos | `entero`, `decimal`, `expresion` (texto), `declaracion` (booleano), `pistas` (lista), `tablero` (matriz) |
| Valores especiales | `culpable`, `NoCulpable`, `sin_pista` |
| Programa principal | `caso Nombre abierto … caso Nombre cerrado!` |
| Entrada y salida | `consultar`, `revelar` |
| Condicionales | `evaluar si`, `sino evaluar`, `sino`, `suceso` |
| Ciclos | `rastrear … desde … hasta`, `seguir mientras` |
| Funciones | `escena` (devuelve valor), `proceso`, `resolver` (llamar), `concluir` (retornar) |
| Aritmética | `conectar`, `descartar`, `intensificar`, `repartir` |
| Lógica y comparación | `y`, `o`, `no`, `==`, `<>`, `>`, `<`, `>=`, `<=` |
| Importar | `#expediente <archivo.eng>` |

Reglas básicas: toda sentencia y todo cierre de bloque (`fin!`) termina en `!`;
los comentarios se escriben `{ así }`; el texto va entre comillas simples.

## El IDE

Diseño de referencia: `docs/diseno_ide.png`. El detalle de uso va en el manual de usuario.

- **Proyectos con varios archivos**: árbol de archivos con carpetas, renombrar, eliminar y
  marcar el **archivo principal** (★).
- **Editor** con pestañas, números de línea, resaltado de sintaxis y búsqueda (`Ctrl+F`).
- **Compilar** y **Ejecutar caso**, con el resultado en el panel inferior (Salida y Terminal).
  `consultar` pide el dato escribiendo en el mismo panel.
- **Guía del detective** (`F1`): consulta del lenguaje con ejemplos que se insertan en el editor.
- **Constructor de pistas**: arma código con formularios y lo valida con el compilador.
- **Innovación, errores en dos pasos**: ante un error el IDE primero da una *pista* que orienta
  sin decir dónde está; si repites el mismo error, muestra la explicación completa con
  archivo, línea y causa posible.

| Atajo | Acción |
|---|---|
| `Ctrl+Enter` | Compilar y ejecutar |
| `Ctrl+S` | Guardar |
| `Ctrl+F` | Buscar |
| `Ctrl+W` | Cerrar pestaña |
| `Ctrl+O` | Abrir carpeta |
| `F1` | Mostrar u ocultar la Guía del detective |

### Importaciones

`#expediente <archivo.eng>` busca el archivo **junto al archivo que lo escribe**
(también sirven rutas como `<utilidades/pistas.eng>` o `<../lib/util.eng>`).
Se detectan archivos inexistentes, funciones duplicadas e importaciones circulares, y los
errores se reportan con el nombre del archivo donde realmente ocurren.

## Cómo funciona por dentro

Intérprete de árbol clásico en cinco etapas:

```
texto .eng → lexer → parser → resolución de #expediente → semántico → intérprete
```

```
enigma/
├── main.py            Punto de entrada del IDE
├── core/              El lenguaje (sin dependencias externas)
│   ├── tokens.py          Tipos de token y palabras reservadas
│   ├── lexer.py           Texto → tokens
│   ├── ast_nodes.py       Nodos del árbol de sintaxis
│   ├── parser*.py         Tokens → AST (descenso recursivo, dividido por tema)
│   ├── module_resolver.py Resuelve #expediente y detecta ciclos
│   ├── symbols.py         Tabla de símbolos y alcances
│   ├── semantic.py        Valida tipos, alcances, constantes, llamadas…
│   ├── interpreter.py     Ejecuta el AST
│   └── errors.py          Jerarquía de errores (Pista Fallida de Razonamiento)
├── gui/               El IDE en tkinter (ventana, editor, árbol, panel de salida, guías)
│   ├── pistas.py          Pistas de error de la innovación
│   └── assets/            Logo e iconos (los genera herramientas/)
├── herramientas/      Scripts que generan el logo y los iconos
├── tests/             Pruebas con pytest
├── ejemplos/          Programas .eng de ejemplo
├── ejemplo_gui/       Proyecto de ejemplo para abrir en el IDE
└── docs/              Documentación del proyecto
```

## Pruebas

```bash
pytest tests/ -v
```
