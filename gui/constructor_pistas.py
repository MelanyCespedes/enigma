"""Ventana del Constructor de pistas: arma codigo con formularios y lo inserta en el editor."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from gui import constructor_codigo as cc
from gui import resaltado, tema
from gui.botones import BotonPlano
from gui.pestana_editor import COLORES_RESALTADO

FAMILIA = "Segoe UI"


class _ItemBloque(tk.Frame):
    def __init__(self, master, bloque: cc.Bloque, comando):
        super().__init__(master, bg=tema.FONDO, cursor="hand2")
        self.bloque = bloque
        self._borde = tk.Frame(self, width=3, bg=tema.FONDO)
        self._borde.pack(side="left", fill="y")
        self._texto = tk.Label(
            self, text=bloque.titulo, bg=tema.FONDO, fg=tema.TEXTO, font=(FAMILIA, 9), anchor="w", padx=12, pady=8
        )
        self._texto.pack(side="left", fill="x", expand=True)
        self._seleccionado = False
        for widget in (self, self._texto, self._borde):
            widget.bind("<Button-1>", lambda e: comando(bloque.id))
            widget.bind("<Enter>", lambda e: self._pintar(True))
            widget.bind("<Leave>", lambda e: self._pintar(False))

    def marcar(self, seleccionado: bool) -> None:
        self._seleccionado = seleccionado
        self._pintar(False)

    def _pintar(self, sobre: bool) -> None:
        fondo = tema.SELECCION if self._seleccionado else (tema.SELECCION_SUAVE if sobre else tema.FONDO)
        self.config(bg=fondo)
        self._texto.config(bg=fondo, fg=tema.TEXTO_FUERTE if self._seleccionado else tema.TEXTO)
        self._borde.config(bg=tema.ACENTO if self._seleccionado else fondo)


class ConstructorPistas(tk.Toplevel):
    """Ventana (no modal) con los bloques a la izquierda, el formulario y la vista previa."""

    def __init__(self, master, al_insertar):
        super().__init__(master)
        self._al_insertar = al_insertar
        self.title("Constructor de pistas")
        self.configure(bg=tema.FONDO)
        self.geometry("820x580")
        self.minsize(720, 520)
        self.transient(master.winfo_toplevel())

        self._variables: dict[str, tk.Variable] = {}
        self._textos: dict[str, tk.Text] = {}
        self._bloque: cc.Bloque = cc.BLOQUES[0]
        self._items: dict[str, _ItemBloque] = {}

        self._construir()
        self._elegir(cc.BLOQUES[0].id)
        tema.oscurecer_barra_titulo(self)
        self.bind("<Escape>", lambda e: self.destroy())

    # ---------- construccion ----------

    def _construir(self) -> None:
        lateral = tk.Frame(self, bg=tema.FONDO, width=240)
        lateral.pack(side="left", fill="y")
        lateral.pack_propagate(False)
        tk.Label(
            lateral, text="BLOQUES", bg=tema.FONDO, fg=tema.TEXTO_SUAVE, font=(FAMILIA, 8, "bold"),
            anchor="w", padx=18, pady=16,
        ).pack(side="top", fill="x")
        for bloque in cc.BLOQUES:
            item = _ItemBloque(lateral, bloque, self._elegir)
            item.pack(side="top", fill="x", padx=(10, 10))
            self._items[bloque.id] = item
        tk.Frame(self, width=1, bg=tema.BORDE).pack(side="left", fill="y")

        derecha = tk.Frame(self, bg=tema.FONDO)
        derecha.pack(side="left", fill="both", expand=True, padx=24, pady=18)
        self._titulo = tk.Label(derecha, bg=tema.FONDO, fg=tema.TEXTO_FUERTE, font=(FAMILIA, 13, "bold"), anchor="w")
        self._titulo.pack(side="top", fill="x")
        self._descripcion = tk.Label(derecha, bg=tema.FONDO, fg=tema.TEXTO_APAGADO, font=(FAMILIA, 9), anchor="w")
        self._descripcion.pack(side="top", fill="x", pady=(2, 14))

        self._formulario = tk.Frame(derecha, bg=tema.FONDO)
        self._formulario.pack(side="top", fill="x")

        tk.Label(
            derecha, text="VISTA PREVIA", bg=tema.FONDO, fg=tema.TEXTO_SUAVE, font=(FAMILIA, 8, "bold"), anchor="w"
        ).pack(side="top", fill="x", pady=(16, 6))
        marco = tk.Frame(derecha, bg=tema.EDITOR, highlightthickness=1, highlightbackground=tema.BORDE)
        marco.pack(side="top", fill="both", expand=True)
        self._vista = tk.Text(
            marco, height=7, state="disabled", wrap="none", bg=tema.EDITOR, fg=tema.TEXTO, font=tema.FUENTE_CODIGO[:1] + (10,),
            relief="flat", borderwidth=0, highlightthickness=0, padx=12, pady=10, spacing1=1, spacing3=1,
            selectbackground=tema.SELECCION,
        )
        self._vista.pack(fill="both", expand=True)
        for etiqueta, color in COLORES_RESALTADO.items():
            self._vista.tag_configure("r_" + etiqueta, foreground=color)

        self._estado = tk.Label(derecha, bg=tema.FONDO, font=(FAMILIA, 9), anchor="w", justify="left", wraplength=480)
        self._estado.pack(side="top", fill="x", pady=(8, 0))

        botones = tk.Frame(derecha, bg=tema.FONDO)
        botones.pack(side="top", fill="x", pady=(12, 0))
        self._boton_insertar = tk.Label(
            botones, text="Insertar en el editor", bg=tema.ACENTO, fg="#1b1c25", font=(FAMILIA, 9, "bold"),
            padx=14, pady=7, cursor="hand2",
        )
        self._boton_insertar.pack(side="left")
        self._boton_insertar.bind("<Button-1>", lambda e: self._insertar())
        BotonPlano(botones, "Copiar", self._copiar, color=tema.TEXTO).pack(side="left", padx=(8, 0))
        BotonPlano(botones, "Cerrar", self.destroy, color=tema.TEXTO_APAGADO).pack(side="right")

    # ---------- formulario ----------

    def _elegir(self, id_bloque: str) -> None:
        self._bloque = cc.POR_ID[id_bloque]
        for k, item in self._items.items():
            item.marcar(k == id_bloque)
        self._titulo.config(text=self._bloque.titulo)
        self._descripcion.config(text=self._bloque.descripcion)

        for hijo in self._formulario.winfo_children():
            hijo.destroy()
        self._variables.clear()
        self._textos.clear()
        self._formulario.grid_columnconfigure(1, weight=1)

        for fila, campo in enumerate(self._bloque.campos):
            if campo.tipo != "casilla":
                tk.Label(
                    self._formulario, text=campo.etiqueta, bg=tema.FONDO, fg=tema.TEXTO, font=(FAMILIA, 9), anchor="w"
                ).grid(row=fila, column=0, sticky="nw", padx=(0, 14), pady=5)

            if campo.tipo == "opciones":
                variable = tk.StringVar(value=str(campo.por_defecto))
                ttk.Combobox(self._formulario, textvariable=variable, values=campo.opciones, state="readonly",
                             width=24).grid(row=fila, column=1, sticky="w", pady=5)
            elif campo.tipo == "casilla":
                variable = tk.BooleanVar(value=bool(campo.por_defecto))
                ttk.Checkbutton(self._formulario, text=campo.etiqueta, variable=variable).grid(
                    row=fila, column=0, columnspan=2, sticky="w", pady=5
                )
            elif campo.multilinea:
                variable = None
                texto = tk.Text(
                    self._formulario, height=3, width=40, bg=tema.EDITOR, fg=tema.TEXTO, insertbackground=tema.ACENTO,
                    font=tema.FUENTE_CODIGO[:1] + (10,), relief="flat", highlightthickness=1,
                    highlightbackground=tema.BORDE, highlightcolor=tema.ACENTO, padx=8, pady=6, wrap="none",
                    selectbackground=tema.SELECCION,
                )
                texto.insert("1.0", str(campo.por_defecto))
                texto.grid(row=fila, column=1, sticky="ew", pady=5)
                texto.bind("<KeyRelease>", lambda e: self._actualizar())
                self._textos[campo.clave] = texto
            else:
                variable = tk.StringVar(value=str(campo.por_defecto))
                ttk.Entry(self._formulario, textvariable=variable).grid(row=fila, column=1, sticky="ew", pady=5)

            if variable is not None:
                self._variables[campo.clave] = variable
                variable.trace_add("write", lambda *_: self._actualizar())
            if campo.ayuda:
                tk.Label(
                    self._formulario, text=campo.ayuda, bg=tema.FONDO, fg=tema.TEXTO_APAGADO, font=(FAMILIA, 8),
                    anchor="w",
                ).grid(row=fila, column=2, sticky="w", padx=(10, 0))

        self._actualizar()

    def _valores(self) -> dict:
        valores = {clave: var.get() for clave, var in self._variables.items()}
        for clave, texto in self._textos.items():
            valores[clave] = texto.get("1.0", "end-1c")
        return valores

    # ---------- vista previa ----------

    def codigo(self) -> str:
        return cc.generar(self._bloque.id, self._valores())

    def _actualizar(self) -> None:
        codigo = self.codigo()
        self._vista.config(state="normal")
        self._vista.delete("1.0", "end")
        self._vista.insert("1.0", codigo)
        for etiqueta, desde, hasta in resaltado.calcular_resaltado(codigo):
            self._vista.tag_add("r_" + etiqueta, f"1.0+{desde}c", f"1.0+{hasta}c")
        self._vista.config(state="disabled")

        problema = cc.validar(codigo)
        if problema is None:
            self._estado.config(text="●  El código es válido", fg=tema.EXITO)
        else:
            self._estado.config(text="●  " + problema, fg=tema.ERROR)
        self._valido = problema is None

    # ---------- acciones ----------

    def _insertar(self) -> None:
        if not self._valido:
            self._estado.config(text="●  Corrige el formulario antes de insertar: " + self._estado.cget("text")[3:], fg=tema.ERROR)
            return
        if self._al_insertar(self.codigo()):
            self._parpadear(self._boton_insertar, "¡Insertado!")

    def _copiar(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.codigo())
        self._parpadear(self._estado, "●  Copiado al portapapeles", tema.EXITO)

    def _parpadear(self, widget: tk.Label, mensaje: str, color: str | None = None) -> None:
        original = (widget.cget("text"), widget.cget("fg"))
        widget.config(text=mensaje, **({"fg": color} if color else {}))
        self.after(1300, lambda: widget.winfo_exists() and widget.config(text=original[0], fg=original[1]))


def abrir(master, al_insertar) -> ConstructorPistas:
    """Abre el constructor (o trae al frente el que ya estaba abierto)."""
    existente = getattr(master, "_constructor_pistas", None)
    if existente is not None and existente.winfo_exists():
        existente.deiconify()
        existente.lift()
        existente.focus_set()
        return existente
    ventana = ConstructorPistas(master, al_insertar)
    master._constructor_pistas = ventana
    return ventana
