"""Botones planos del IDE (de texto y de icono), tooltips y barras de desplazamiento que se ocultan."""
from __future__ import annotations

import tkinter as tk

from gui import tema


class Tooltip:
    """Globito de ayuda que aparece al dejar el mouse sobre un widget."""

    RETARDO_MS = 600

    def __init__(self, widget, texto: str):
        self.widget = widget
        self.texto = texto
        self._ventana = None
        self._pendiente = None
        widget.bind("<Enter>", self._programar, add="+")
        widget.bind("<Leave>", self._ocultar, add="+")
        widget.bind("<ButtonPress>", self._ocultar, add="+")

    def _programar(self, _evento=None) -> None:
        self._cancelar()
        self._pendiente = self.widget.after(self.RETARDO_MS, self._mostrar)

    def _cancelar(self) -> None:
        if self._pendiente is not None:
            self.widget.after_cancel(self._pendiente)
            self._pendiente = None

    def _mostrar(self) -> None:
        self._pendiente = None
        if self._ventana is not None or not self.widget.winfo_exists():
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self._ventana = tk.Toplevel(self.widget)
        self._ventana.wm_overrideredirect(True)
        tk.Label(
            self._ventana, text=self.texto, bg=tema.SUPERFICIE, fg=tema.TEXTO_FUERTE,
            padx=8, pady=3, borderwidth=1, relief="solid", font=("Segoe UI", 9),
        ).pack()
        self._ventana.update_idletasks()
        self._ventana.wm_geometry(f"+{x - self._ventana.winfo_width() // 2}+{y}")

    def _ocultar(self, _evento=None) -> None:
        self._cancelar()
        if self._ventana is not None:
            self._ventana.destroy()
            self._ventana = None


class BotonPlano(tk.Label):
    """Boton de texto sin borde que se ilumina al pasar el mouse."""

    def __init__(self, master, texto: str, comando, color: str = tema.TEXTO_SUAVE, fondo: str = tema.FONDO, **kwargs):
        super().__init__(
            master, text=texto, bg=fondo, fg=color, padx=10, pady=5, cursor="hand2", **kwargs
        )
        self._color = color
        self._fondo = fondo
        self.bind("<Button-1>", lambda e: comando())
        self.bind("<Enter>", lambda e: self.config(bg=tema.SELECCION_SUAVE, fg=tema.TEXTO_FUERTE))
        self.bind("<Leave>", lambda e: self.config(bg=self._fondo, fg=self._color))


class BotonIcono(tk.Label):
    """Boton con un icono (y, opcionalmente, un texto a su derecha)."""

    def __init__(
        self, master, imagen, comando, texto: str = "", ayuda: str = "", fondo: str = tema.FONDO,
        color: str = tema.TEXTO, **kwargs,
    ):
        super().__init__(
            master, image=imagen, text=texto, compound="left" if texto else "none", bg=fondo, fg=color,
            padx=8, pady=6, cursor="hand2", **kwargs,
        )
        self._fondo = fondo
        self._color = color
        self.bind("<Button-1>", lambda e: comando())
        self.bind("<Enter>", lambda e: self.config(bg=tema.SELECCION_SUAVE, fg=tema.TEXTO_FUERTE))
        self.bind("<Leave>", lambda e: self.config(bg=self._fondo, fg=self._color))
        if ayuda:
            Tooltip(self, ayuda)

    def cambiar_icono(self, imagen) -> None:
        self.config(image=imagen)

def autoocultar(barra, mostrar, ocultar):
    """Devuelve la funcion para 'yscrollcommand'/'xscrollcommand': actualiza la barra
    y la oculta mientras todo el contenido esta a la vista."""
    visible = {"si": True}

    def establecer(primero, ultimo):
        barra.set(primero, ultimo)
        cabe = float(primero) <= 0.0 and float(ultimo) >= 1.0
        if cabe and visible["si"]:
            ocultar()
            visible["si"] = False
        elif not cabe and not visible["si"]:
            mostrar()
            visible["si"] = True

    return establecer
