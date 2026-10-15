"""Paleta y estilos oscuros de Enigma, basados en el diseno del IDE."""
from __future__ import annotations

import sys
from tkinter import ttk

FONDO = "#1b1c25"          # ventana y barras
SUPERFICIE = "#242635"     # botones, pestañas inactivas
EDITOR = "#1e1f29"         # areas de codigo
BORDE = "#2f3144"
TEXTO = "#d7dae0"
TEXTO_SUAVE = "#8b8fa3"
ACENTO = "#ffd54a"         # amarillo del logo / cursor
SELECCION = "#5b3a8f"      # morado de la fila seleccionada
SELECCION_SUAVE = "#2d2f45"

ERROR = "#ff7b7b"
EXITO = "#7ddc9a"
AVISO = "#ffc266"

FUENTE_CODIGO = ("Consolas", 11)


def _colorref(color_hex: str) -> int:
    """'#rrggbb' -> COLORREF de Windows (0x00BBGGRR)."""
    r, g, b = (int(color_hex[i:i + 2], 16) for i in (1, 3, 5))
    return (b << 16) | (g << 8) | r


def oscurecer_barra_titulo(ventana) -> None:

    if sys.platform != "win32":
        return
    try:
        import ctypes

        ventana.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(ventana.winfo_id())

        def poner(atributo: int, valor: int) -> int:
            dato = ctypes.c_int(valor)
            return ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, atributo, ctypes.byref(dato), ctypes.sizeof(dato)
            )

        if poner(20, 1) != 0:
            poner(19, 1)
        # Win11: color exacto de la barra (35) y del texto (36).
        poner(35, _colorref(FONDO))
        poner(36, _colorref(TEXTO))
    except Exception:
        pass


def aplicar_tema(raiz) -> None:
    """Aplica el tema oscuro a toda la ventana. Debe llamarse antes de crear
    los widgets (los menus toman sus colores de la base de opciones)."""
    raiz.configure(bg=FONDO)

    for opcion, valor in {
        "background": SUPERFICIE,
        "foreground": TEXTO,
        "activeBackground": SELECCION,
        "activeForeground": "#ffffff",
        "relief": "flat",
        "borderWidth": 0,
    }.items():
        raiz.option_add(f"*Menu.{opcion}", valor)

    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")

    estilo.configure(
        ".", background=FONDO, foreground=TEXTO, fieldbackground=EDITOR,
        bordercolor=BORDE, lightcolor=FONDO, darkcolor=FONDO, troughcolor=FONDO,
        focuscolor=FONDO, insertcolor=ACENTO,
    )
    estilo.configure("TFrame", background=FONDO)
    estilo.configure("TLabel", background=FONDO, foreground=TEXTO_SUAVE)

    estilo.configure(
        "TButton", background=SUPERFICIE, foreground=TEXTO, bordercolor=BORDE,
        lightcolor=SUPERFICIE, darkcolor=SUPERFICIE, padding=(10, 4), relief="flat",
    )
    estilo.configure(
        "Acento.TButton", background=ACENTO, foreground="#1b1c25",
        lightcolor=ACENTO, darkcolor=ACENTO, bordercolor=ACENTO,
    )
    estilo.map(
        "Acento.TButton",
        background=[("pressed", "#e6bf3f"), ("active", "#ffe07a")],
        foreground=[("disabled", BORDE)],
    )
    estilo.map(
        "TButton",
        background=[("disabled", FONDO), ("pressed", SELECCION), ("active", SELECCION_SUAVE)],
        foreground=[("disabled", BORDE)],
    )

    estilo.configure(
        "Treeview", background=FONDO, fieldbackground=FONDO, foreground=TEXTO,
        bordercolor=FONDO, lightcolor=FONDO, darkcolor=FONDO, rowheight=26, borderwidth=0,
    )
    estilo.map(
        "Treeview",
        background=[("selected", SELECCION)],
        foreground=[("selected", "#ffffff")],
    )

    estilo.configure("TNotebook", background=FONDO, bordercolor=FONDO, borderwidth=0, tabmargins=(0, 0, 0, 0))
    estilo.configure(
        "TNotebook.Tab", background=FONDO, foreground=TEXTO_SUAVE, padding=(14, 7),
        bordercolor=FONDO, lightcolor=FONDO, darkcolor=FONDO,
    )
    estilo.map(
        "TNotebook.Tab",
        background=[("selected", EDITOR), ("active", SUPERFICIE)],
        foreground=[("selected", TEXTO), ("active", TEXTO)],
        lightcolor=[("selected", ACENTO)],
    )

    estilo.configure(
        "TScrollbar", background=SUPERFICIE, troughcolor=FONDO, bordercolor=FONDO,
        arrowcolor=TEXTO_SUAVE, lightcolor=SUPERFICIE, darkcolor=SUPERFICIE, relief="flat",
    )
    estilo.map("TScrollbar", background=[("active", SELECCION_SUAVE)])

    estilo.configure("TPanedwindow", background=BORDE)
    estilo.configure("Sash", sashthickness=4, background=BORDE)
