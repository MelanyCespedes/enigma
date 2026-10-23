"""Panel "Guia rapida" (derecha, como en el diseno): una pista, atajos, colores y el
acceso al Constructor de pistas."""
from __future__ import annotations

import tkinter as tk

from gui import recursos, tema
from gui.botones import BotonIcono
from gui.pestana_editor import COLORES_RESALTADO
from gui import resaltado

FAMILIA = "Segoe UI"
TEXTO_PISTA_INICIAL = (
    "Antes del error completo, Enigma te da una pista: te dice qué revisar, no dónde. "
    "Búscalo tú."
)

ATAJOS = (
    ("Ejecutar código", ("Ctrl", "↵")),
    ("Guardar archivo", ("Ctrl", "S")),
    ("Abrir buscador", ("Ctrl", "F")),
)
LEYENDA = (
    ("Palabra clave", resaltado.PALABRA_CLAVE),
    ("Texto", resaltado.TEXTO),
    ("Variable", resaltado.VARIABLE),
)


def _linea(padre) -> tk.Frame:
    return tk.Frame(padre, height=1, bg=tema.BORDE)


class GuiaRapida(tk.Frame):
    """al_ocultar(): contrae el panel.  al_constructor(): abre el Constructor de pistas."""

    def __init__(self, master, al_ocultar, al_constructor):
        super().__init__(master, bg=tema.FONDO)

        # Titulo y boton de contraer
        titulo = tk.Frame(self, bg=tema.FONDO)
        titulo.pack(side="top", fill="x", padx=(18, 10), pady=(18, 12))
        tk.Label(
            titulo, text="GUÍA RÁPIDA", bg=tema.FONDO, fg=tema.TEXTO_SUAVE, font=(FAMILIA, 9, "bold")
        ).pack(side="left")
        BotonIcono(
            titulo, recursos.icono("chevron_abajo", master=self), al_ocultar, ayuda="Ocultar la guía rápida"
        ).pack(side="right")

        self._construir_consejo()
        _linea(self).pack(side="top", fill="x", padx=18, pady=(18, 0))
        self._construir_atajos()
        _linea(self).pack(side="top", fill="x", padx=18, pady=(14, 0))
        self._construir_sintaxis()
        self._construir_constructor(al_constructor)

    # ---------- tarjeta de pista ----------

    def _construir_consejo(self) -> None:
        tarjeta = tk.Frame(
            self, bg=tema.SELECCION, highlightthickness=1, highlightbackground=tema.SELECCION_BORDE
        )
        tarjeta.pack(side="top", fill="x", padx=16)

        fila = tk.Frame(tarjeta, bg=tema.SELECCION)
        fila.pack(side="top", fill="x", padx=14, pady=(12, 2))
        tk.Label(fila, image=recursos.icono("bombilla", master=self), bg=tema.SELECCION).pack(side="left")
        tk.Label(
            fila, text="Primero recibe una pista", bg=tema.SELECCION, fg=tema.TEXTO_FUERTE,
            font=(FAMILIA, 10, "bold"),
        ).pack(side="left", padx=(10, 0))

        self._pista = tk.Label(
            tarjeta, text=TEXTO_PISTA_INICIAL, bg=tema.SELECCION, fg="#e6dcf2", font=(FAMILIA, 9),
            justify="left", anchor="nw", wraplength=200,
        )
        self._pista.pack(side="top", fill="x", padx=(44, 14), pady=(0, 14))
        tarjeta.bind("<Configure>", lambda e: self._pista.config(wraplength=max(120, e.width - 70)))

    def mostrar_pista(self, texto: str | None) -> None:
        """Muestra la pista del ultimo error (o el consejo inicial si ya no hay error)."""
        self._pista.config(text=texto if texto else TEXTO_PISTA_INICIAL)

    # ---------- atajos y colores ----------

    def _construir_atajos(self) -> None:
        tk.Label(
            self, text="Atajos de investigación", bg=tema.FONDO, fg=tema.TEXTO_FUERTE,
            font=(FAMILIA, 10, "bold"), anchor="w",
        ).pack(side="top", fill="x", padx=18, pady=(16, 8))
        for texto, teclas in ATAJOS:
            fila = tk.Frame(self, bg=tema.FONDO)
            fila.pack(side="top", fill="x", padx=18, pady=5)
            tk.Label(fila, text=texto, bg=tema.FONDO, fg=tema.TEXTO_APAGADO, font=(FAMILIA, 9)).pack(side="left")
            for tecla in reversed(teclas):
                tk.Label(
                    fila, text=tecla, bg=tema.SUPERFICIE, fg=tema.TEXTO, font=(FAMILIA, 8),
                    padx=7, pady=4, width=2 if len(tecla) == 1 else 4,
                ).pack(side="right", padx=(4, 0))

    def _construir_sintaxis(self) -> None:
        tk.Label(
            self, text="Sintaxis detectada", bg=tema.FONDO, fg=tema.TEXTO_FUERTE,
            font=(FAMILIA, 10, "bold"), anchor="w",
        ).pack(side="top", fill="x", padx=18, pady=(16, 8))
        fila = tk.Frame(self, bg=tema.FONDO)
        fila.pack(side="top", fill="x", padx=18)
        for texto, etiqueta in LEYENDA:
            tk.Frame(fila, width=9, height=9, bg=COLORES_RESALTADO[etiqueta]).pack(side="left", padx=(0, 4))
            tk.Label(fila, text=texto, bg=tema.FONDO, fg=tema.TEXTO_APAGADO, font=(FAMILIA, 8)).pack(
                side="left", padx=(0, 9)
            )

    # ---------- constructor de pistas ----------

    def _construir_constructor(self, al_constructor) -> None:
        tarjeta = tk.Frame(
            self, bg=tema.TARJETA, highlightthickness=1, highlightbackground="#4a3a5e", cursor="hand2"
        )
        tarjeta.pack(side="top", fill="x", padx=16, pady=(22, 0))

        icono = tk.Label(tarjeta, image=recursos.icono("varita", master=self), bg=tema.TARJETA)
        icono.pack(side="left", padx=(12, 10), pady=14)
        textos = tk.Frame(tarjeta, bg=tema.TARJETA)
        textos.pack(side="left", fill="x", expand=True)
        titulo = tk.Label(
            textos, text="Constructor de pistas", bg=tema.TARJETA, fg="#d9a8f0", font=(FAMILIA, 10, "bold"), anchor="w"
        )
        titulo.pack(fill="x")
        subtitulo = tk.Label(
            textos, text="Genera código con bloques visuales", bg=tema.TARJETA, fg=tema.TEXTO_APAGADO,
            font=(FAMILIA, 8), anchor="w", justify="left", wraplength=140,
        )
        subtitulo.pack(fill="x")
        textos.bind("<Configure>", lambda e: subtitulo.config(wraplength=max(80, e.width - 4)))
        flecha = tk.Label(tarjeta, image=recursos.icono("chevron_der_claro", master=self), bg=tema.TARJETA)
        flecha.pack(side="right", padx=(0, 8))

        for widget in (tarjeta, icono, textos, titulo, subtitulo, flecha):
            widget.bind("<Button-1>", lambda e: al_constructor())
