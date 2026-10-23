"""Columna derecha del IDE: la Guia rapida (por defecto) o la Guia del detective."""
from __future__ import annotations

import tkinter as tk

from gui import tema
from gui.guia_detective import GuiaDetective
from gui.guia_rapida import GuiaRapida

RAPIDA = "rapida"
DETECTIVE = "detective"


class PanelDerecho(tk.Frame):
    """Alterna entre las dos guias. 'al_cambiar_vista(vista)' permite ajustar el ancho."""

    def __init__(self, master, al_insertar, al_ocultar, al_constructor, al_cambiar_vista=None):
        super().__init__(master, bg=tema.FONDO)
        self._al_cambiar_vista = al_cambiar_vista
        tk.Frame(self, width=1, bg=tema.BORDE).pack(side="left", fill="y")

        self.rapida = GuiaRapida(self, al_ocultar=al_ocultar, al_constructor=al_constructor)
        self.detective = GuiaDetective(self, al_insertar=al_insertar, al_cerrar=self.mostrar_rapida)
        self.vista = RAPIDA
        self.rapida.pack(side="left", fill="both", expand=True)

    def mostrar_rapida(self) -> None:
        self.detective.pack_forget()
        self.rapida.pack(side="left", fill="both", expand=True)
        self._cambiar(RAPIDA)

    def mostrar_detective(self, seccion: str | None = None) -> None:
        if seccion:
            self.detective.abrir_seccion(seccion)
        self.rapida.pack_forget()
        self.detective.pack(side="left", fill="both", expand=True)
        self._cambiar(DETECTIVE)

    def _cambiar(self, vista: str) -> None:
        self.vista = vista
        if self._al_cambiar_vista:
            self._al_cambiar_vista(vista)
