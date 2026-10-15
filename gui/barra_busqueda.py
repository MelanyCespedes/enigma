from __future__ import annotations

import tkinter as tk

from gui import tema
from gui.barra_pestanas import BotonPlano


class BarraBusqueda(tk.Frame):
    def __init__(self, master, al_buscar, al_siguiente, al_anterior, al_cerrar):
        super().__init__(master, bg=tema.FONDO, padx=8, pady=6)
        self.visible = False
        self._al_buscar = al_buscar

        tk.Frame(self, height=1, bg=tema.BORDE).pack(side="bottom", fill="x", pady=(6, 0))

        self._var = tk.StringVar()
        self._entrada = tk.Entry(
            self, textvariable=self._var, width=32, bg=tema.EDITOR, fg=tema.TEXTO,
            insertbackground=tema.ACENTO, selectbackground=tema.SELECCION, relief="flat",
            highlightthickness=1, highlightbackground=tema.BORDE, highlightcolor=tema.ACENTO,
        )
        self._entrada.pack(side="left", ipady=3)

        self._contador = tk.Label(self, text="", bg=tema.FONDO, fg=tema.TEXTO_SUAVE, width=14)
        self._contador.pack(side="left", padx=6)

        BotonPlano(self, "▲", al_anterior).pack(side="left")
        BotonPlano(self, "▼", al_siguiente).pack(side="left")
        BotonPlano(self, "×", al_cerrar).pack(side="right")

        self._var.trace_add("write", lambda *_: al_buscar(self._var.get()))
        self._entrada.bind("<Return>", lambda e: (al_siguiente(), "break")[1])
        self._entrada.bind("<Shift-Return>", lambda e: (al_anterior(), "break")[1])
        self._entrada.bind("<Escape>", lambda e: (al_cerrar(), "break")[1])

    def consulta(self) -> str:
        return self._var.get()

    def mostrar(self, texto_inicial: str = "") -> None:
        self.visible = True
        if texto_inicial:
            self._var.set(texto_inicial)
        self._entrada.focus_set()
        self._entrada.select_range(0, "end")
        self._entrada.icursor("end")

    def ocultar(self) -> None:
        self.visible = False

    def poner_contador(self, actual: int, total: int) -> None:
        if not self._var.get():
            texto = ""
        elif total == 0:
            texto = "Sin resultados"
        elif actual:
            texto = f"{actual} de {total}"
        else:
            texto = f"{total} resultados"
        self._contador.config(text=texto)
