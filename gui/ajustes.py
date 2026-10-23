"""Preferencias del IDE (tamaño de letra) y su guardado en el equipo de cada persona."""
from __future__ import annotations

import json
import os
import tkinter as tk
from tkinter import ttk

from gui import tema
from gui.botones import BotonPlano

ARCHIVO = os.path.join(os.path.expanduser("~"), ".enigma_config.json")
TAM_FUENTE_MIN, TAM_FUENTE_MAX, TAM_FUENTE_INICIAL = 9, 20, 11
FAMILIA = "Segoe UI"


def limitar_fuente(valor) -> int:
    """Convierte 'valor' en un tamaño valido (entre el minimo y el maximo)."""
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return TAM_FUENTE_INICIAL
    return max(TAM_FUENTE_MIN, min(TAM_FUENTE_MAX, numero))


def cargar(ruta: str | None = None) -> dict:
    try:
        with open(ruta or ARCHIVO, encoding="utf-8") as f:
            datos = json.load(f)
        return datos if isinstance(datos, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def guardar(datos: dict, ruta: str | None = None) -> None:
    try:
        with open(ruta or ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # sin permisos: la preferencia solo dura esta sesion


class DialogoPreferencias(tk.Toplevel):
    def __init__(self, master, tam_actual: int, al_aplicar):
        super().__init__(master)
        self.title("Preferencias")
        self.configure(bg=tema.FONDO, padx=24, pady=20)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self._al_aplicar = al_aplicar

        tk.Label(self, text="Preferencias", bg=tema.FONDO, fg=tema.TEXTO_FUERTE, font=(FAMILIA, 13, "bold")).pack(anchor="w")
        tk.Label(
            self, text="Se guardan en tu equipo y se aplican a todos los archivos abiertos.", bg=tema.FONDO,
            fg=tema.TEXTO_APAGADO, font=(FAMILIA, 9),
        ).pack(anchor="w", pady=(2, 16))

        fila = tk.Frame(self, bg=tema.FONDO)
        fila.pack(fill="x")
        tk.Label(fila, text="Tamaño de letra del editor", bg=tema.FONDO, fg=tema.TEXTO, font=(FAMILIA, 10)).pack(side="left")
        self._tam = tk.IntVar(value=limitar_fuente(tam_actual))
        ttk.Spinbox(
            fila, from_=TAM_FUENTE_MIN, to=TAM_FUENTE_MAX, textvariable=self._tam, width=4, command=self._cambio,
        ).pack(side="right")

        self._muestra = tk.Label(
            self, text="pista sospechoso = entero(valor: 15)!", bg=tema.EDITOR, fg=tema.TEXTO,
            font=tema.FUENTE_CODIGO[:1] + (self._tam.get(),), padx=14, pady=12, anchor="w",
        )
        self._muestra.pack(fill="x", pady=(16, 0))
        self._tam.trace_add("write", lambda *_: self._cambio())

        botones = tk.Frame(self, bg=tema.FONDO)
        botones.pack(fill="x", pady=(18, 0))
        aplicar = tk.Label(
            botones, text="Aplicar", bg=tema.ACENTO, fg="#1b1c25", font=(FAMILIA, 9, "bold"), padx=16, pady=7,
            cursor="hand2",
        )
        aplicar.pack(side="left")
        aplicar.bind("<Button-1>", lambda e: self._aplicar())
        BotonPlano(botones, "Cerrar", self.destroy, color=tema.TEXTO_APAGADO).pack(side="right")

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self._aplicar())
        tema.oscurecer_barra_titulo(self)

    def _valor(self) -> int:
        try:
            return limitar_fuente(self._tam.get())
        except tk.TclError:  # la caja esta vacia o con texto
            return TAM_FUENTE_INICIAL

    def _cambio(self) -> None:
        self._muestra.config(font=tema.FUENTE_CODIGO[:1] + (self._valor(),))

    def _aplicar(self) -> None:
        self._al_aplicar(self._valor())
        self.destroy()


def abrir_preferencias(master, tam_actual: int, al_aplicar) -> DialogoPreferencias:
    existente = getattr(master, "_dialogo_preferencias", None)
    if existente is not None and existente.winfo_exists():
        existente.lift()
        return existente
    ventana = DialogoPreferencias(master, tam_actual, al_aplicar)
    master._dialogo_preferencias = ventana
    return ventana
