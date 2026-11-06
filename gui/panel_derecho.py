"""Columna derecha del IDE: la Guia rapida (por defecto), la Guia del detective o el Constructor de pistas."""
from __future__ import annotations

import tkinter as tk

from gui import tema
from gui.constructor_pistas import ConstructorPistas
from gui.guia_detective import GuiaDetective
from gui.guia_rapida import GuiaRapida

RAPIDA = "rapida"
DETECTIVE = "detective"
CONSTRUCTOR = "constructor"


class PanelDerecho(tk.Frame):
    """Alterna entre las tres vistas. 'al_cambiar_vista(vista)' permite ajustar el ancho.

    al_insertar_en_editor(texto) -> bool  lo usa el Constructor para escribir en el archivo activo.
    """

    def __init__(self, master, al_insertar, al_ocultar, al_insertar_en_editor, al_cambiar_vista=None):
        super().__init__(master, bg=tema.FONDO)
        self._al_cambiar_vista = al_cambiar_vista
        tk.Frame(self, width=1, bg=tema.BORDE).pack(side="left", fill="y")

        self.rapida = GuiaRapida(self, al_ocultar=al_ocultar, al_constructor=self.mostrar_constructor)
        self.detective = GuiaDetective(self, al_insertar=al_insertar, al_cerrar=self.mostrar_rapida)
        self.constructor = ConstructorPistas(self, al_insertar=al_insertar_en_editor, al_cerrar=self.mostrar_rapida)
        self.vista = RAPIDA
        self.rapida.pack(side="left", fill="both", expand=True)

    def mostrar_rapida(self) -> None:
        self._mostrar(self.rapida, RAPIDA)

    def mostrar_detective(self, seccion: str | None = None) -> None:
        if seccion:
            self.detective.abrir_seccion(seccion)
        self._mostrar(self.detective, DETECTIVE)

    def mostrar_constructor(self) -> None:
        self._mostrar(self.constructor, CONSTRUCTOR)

    def _mostrar(self, panel: tk.Frame, vista: str) -> None:
        for otro in (self.rapida, self.detective, self.constructor):
            if otro is not panel:
                otro.pack_forget()
        panel.pack(side="left", fill="both", expand=True)
        self._cambiar(vista)

    def _cambiar(self, vista: str) -> None:
        self.vista = vista
        if self._al_cambiar_vista:
            self._al_cambiar_vista(vista)
