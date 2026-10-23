"""Seccion "Herramientas" (abajo a la izquierda, bajo el arbol de archivos)."""
from __future__ import annotations

import tkinter as tk

from gui import recursos, tema

FAMILIA = "Segoe UI"


class _Entrada(tk.Frame):
    def __init__(self, master, icono: str, texto: str, comando):
        super().__init__(master, bg=tema.FONDO, cursor="hand2")
        self._activa = False
        self._icono = tk.Label(self, image=recursos.icono(icono, master=master), bg=tema.FONDO)
        self._icono.pack(side="left", padx=(16, 9), pady=7)
        self._texto = tk.Label(self, text=texto, bg=tema.FONDO, fg=tema.TEXTO, font=(FAMILIA, 9), anchor="w")
        self._texto.pack(side="left", fill="x", expand=True)
        for widget in (self, self._icono, self._texto):
            widget.bind("<Button-1>", lambda e: comando())
            widget.bind("<Enter>", lambda e: self._pintar(True))
            widget.bind("<Leave>", lambda e: self._pintar(False))

    def marcar(self, activa: bool) -> None:
        self._activa = activa
        self._pintar(False)

    def _pintar(self, sobre: bool) -> None:
        fondo = tema.SELECCION_SUAVE if (sobre or self._activa) else tema.FONDO
        color = tema.ACENTO if self._activa else tema.TEXTO
        for widget in (self, self._icono, self._texto):
            widget.config(bg=fondo)
        self._texto.config(fg=color)


class PanelHerramientas(tk.Frame):
    """Lista de accesos directos. 'entradas' es una lista de (clave, icono, texto, comando)."""

    def __init__(self, master, entradas):
        super().__init__(master, bg=tema.FONDO)
        tk.Frame(self, height=1, bg=tema.BORDE).pack(side="top", fill="x", padx=16)
        tk.Label(
            self, text="HERRAMIENTAS", anchor="w", bg=tema.FONDO, fg=tema.TEXTO_SUAVE,
            font=(FAMILIA, 8, "bold"), padx=16, pady=10,
        ).pack(side="top", fill="x")

        self._entradas: dict[str, _Entrada] = {}
        for clave, icono, texto, comando in entradas:
            entrada = _Entrada(self, icono, texto, comando)
            entrada.pack(side="top", fill="x")
            self._entradas[clave] = entrada
        tk.Frame(self, height=10, bg=tema.FONDO).pack(side="top")

    def marcar(self, clave: str, activa: bool) -> None:
        """Resalta una entrada (p. ej. la guia mientras esta abierta)."""
        if clave in self._entradas:
            self._entradas[clave].marcar(activa)
