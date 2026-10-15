"""Cuadros de dialogo con el tema oscuro de Enigma (reemplazan a
tkinter.messagebox / tkinter.simpledialog, que usan el estilo del sistema)."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from gui import tema

TITULO = "Enigma"


class _Dialogo(tk.Toplevel):
    def __init__(
        self,
        padre,
        titulo: str,
        mensaje: str,
        botones: list[tuple[str, object]],
        valor_cancelar: object,
        entrada: bool = False,
        valor_inicial: str = "",
    ):
        ventana = padre.winfo_toplevel()
        super().__init__(ventana)
        self.title(titulo)
        self.configure(bg=tema.FONDO, padx=20, pady=16)
        self.resizable(False, False)
        self.transient(ventana)

        self.resultado = valor_cancelar
        self._valor_cancelar = valor_cancelar
        self._entrada = None

        ttk.Label(
            self, text=mensaje, wraplength=380, justify="left", foreground=tema.TEXTO
        ).pack(anchor="w")

        if entrada:
            self._entrada = tk.Entry(
                self, width=44, bg=tema.EDITOR, fg=tema.TEXTO, insertbackground=tema.ACENTO,
                selectbackground=tema.SELECCION, relief="flat", font=tema.FUENTE_CODIGO,
                highlightthickness=1, highlightbackground=tema.BORDE, highlightcolor=tema.ACENTO,
            )
            self._entrada.pack(fill="x", pady=(10, 0), ipady=4)
            self._entrada.insert(0, valor_inicial)
            self._entrada.select_range(0, "end")

        barra = ttk.Frame(self)
        barra.pack(fill="x", pady=(16, 0))

        self._valor_por_defecto = botones[0][1]
        for texto, valor in reversed(botones):
            es_principal = valor == self._valor_por_defecto
            ttk.Button(
                barra, text=texto, command=lambda v=valor: self._terminar(v),
                style="Acento.TButton" if es_principal else "TButton",
            ).pack(side="right", padx=(8, 0))

        self.bind("<Return>", lambda e: self._terminar(self._valor_por_defecto))
        self.bind("<Escape>", lambda e: self._terminar(self._valor_cancelar))
        self.protocol("WM_DELETE_WINDOW", lambda: self._terminar(self._valor_cancelar))

        self._centrar(ventana)
        tema.oscurecer_barra_titulo(self)
        self.grab_set()
        (self._entrada or self).focus_set()

    def _centrar(self, ventana) -> None:
        self.update_idletasks()
        ancho, alto = self.winfo_reqwidth(), self.winfo_reqheight()
        x = ventana.winfo_rootx() + (ventana.winfo_width() - ancho) // 2
        y = ventana.winfo_rooty() + (ventana.winfo_height() - alto) // 3
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _terminar(self, valor) -> None:
        if self._entrada is not None and valor == self._valor_por_defecto:
            self.resultado = self._entrada.get()
        else:
            self.resultado = valor
        self.destroy()

    def mostrar(self):
        self.wait_window(self)
        return self.resultado


def preguntar_texto(padre, titulo: str, mensaje: str, valor_inicial: str = "") -> str | None:
    return _Dialogo(
        padre, titulo, mensaje, [("Aceptar", "ok"), ("Cancelar", None)], None,
        entrada=True, valor_inicial=valor_inicial,
    ).mostrar()


def mostrar_info(padre, mensaje: str, titulo: str = TITULO) -> None:
    _Dialogo(padre, titulo, mensaje, [("Aceptar", "ok")], "ok").mostrar()


mostrar_aviso = mostrar_info


def mostrar_error(padre, mensaje: str, titulo: str = TITULO) -> None:
    _Dialogo(padre, titulo, mensaje, [("Aceptar", "ok")], "ok").mostrar()


def confirmar(padre, mensaje: str, si: str = "Sí", no: str = "No", titulo: str = TITULO) -> bool:
    return _Dialogo(padre, titulo, mensaje, [(si, True), (no, False)], False).mostrar()


def confirmar_o_cancelar(
    padre, mensaje: str, si: str = "Sí", no: str = "No", titulo: str = TITULO
) -> bool | None:
    return _Dialogo(
        padre, titulo, mensaje, [(si, True), (no, False), ("Cancelar", None)], None
    ).mostrar()
