"""Panel del Constructor de bloques (columna derecha): arma codigo con formularios y lo inserta en el editor."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from gui import constructor_codigo as cc
from gui import resaltado, tema
from gui.botones import BotonPlano
from gui.pestana_editor import COLORES_RESALTADO

FAMILIA = "Segoe UI"


class ConstructorBloques(tk.Frame):
    """Selector de bloques arriba, formulario apilado en medio y vista previa abajo.

    al_insertar(texto, nombre) -> bool  escribe el codigo en el archivo abierto o, si no hay ninguno, crea
                                        un proyecto y un archivo nuevos como la Guia (True si se pudo)
    al_cerrar()                         vuelve a la guia rapida
    """

    def __init__(self, master, al_insertar, al_cerrar):
        super().__init__(master, bg=tema.FONDO)
        self._al_insertar = al_insertar
        self._variables: dict[str, tk.Variable] = {}
        self._textos: dict[str, tk.Text] = {}
        self._bloque: cc.Bloque = cc.BLOQUES[0]
        self._valido = True

        self._construir_cabecera(al_cerrar)
        self._construir_pie()
        self._construir_cuerpo()
        self._elegir(cc.BLOQUES[0].id)

    # ---------- construccion ----------

    def _construir_cabecera(self, al_cerrar) -> None:
        barra = tk.Frame(self, bg=tema.FONDO)
        barra.pack(side="top", fill="x")
        tk.Frame(self, height=1, bg=tema.BORDE).pack(side="top", fill="x")

        BotonPlano(barra, "‹", lambda: self._mover(-1), font=(FAMILIA, 12)).pack(side="left")
        self._selector = tk.Menubutton(
            barra, bg=tema.FONDO, fg=tema.TEXTO, activebackground=tema.SELECCION_SUAVE,
            activeforeground=tema.TEXTO, relief="flat", borderwidth=0, padx=8, pady=6,
            font=(FAMILIA, 10, "bold"), anchor="w",
        )
        menu = tk.Menu(self._selector, tearoff=0, borderwidth=1)
        for bloque in cc.BLOQUES:
            menu.add_command(label=bloque.titulo, command=lambda b=bloque.id: self._elegir(b))
        self._selector.config(menu=menu)
        self._selector.pack(side="left", fill="x", expand=True)
        BotonPlano(barra, "›", lambda: self._mover(1), font=(FAMILIA, 12)).pack(side="left")
        BotonPlano(barra, "×", al_cerrar, font=(FAMILIA, 12)).pack(side="left")

    def _construir_pie(self) -> None:
        """Estado y botones van abajo del todo para que nunca queden fuera de vista."""
        pie = tk.Frame(self, bg=tema.FONDO)
        pie.pack(side="bottom", fill="x", padx=16, pady=(6, 14))

        botones = tk.Frame(pie, bg=tema.FONDO)
        botones.pack(side="bottom", fill="x")
        self._boton_insertar = tk.Label(
            botones, text="Insertar en el editor", bg=tema.ACENTO, fg="#1b1c25", font=(FAMILIA, 9, "bold"),
            padx=14, pady=7, cursor="hand2",
        )
        self._boton_insertar.pack(side="left")
        self._boton_insertar.bind("<Button-1>", lambda e: self._insertar())
        BotonPlano(botones, "Copiar", self._copiar, color=tema.TEXTO).pack(side="left", padx=(8, 0))

        self._estado = tk.Label(pie, bg=tema.FONDO, font=(FAMILIA, 9), anchor="w", justify="left", wraplength=280)
        self._estado.pack(side="bottom", fill="x", pady=(0, 10))
        self._estado.bind("<Configure>", lambda e: self._estado.config(wraplength=max(120, e.width - 4)))

    def _construir_cuerpo(self) -> None:
        cuerpo = tk.Frame(self, bg=tema.FONDO)
        cuerpo.pack(side="top", fill="both", expand=True, padx=16, pady=(14, 0))

        self._titulo = tk.Label(cuerpo, bg=tema.FONDO, fg=tema.TEXTO_FUERTE, font=(FAMILIA, 12, "bold"), anchor="w")
        self._titulo.pack(side="top", fill="x")
        self._descripcion = tk.Label(
            cuerpo, bg=tema.FONDO, fg=tema.TEXTO_APAGADO, font=(FAMILIA, 9), anchor="w", justify="left", wraplength=280
        )
        self._descripcion.pack(side="top", fill="x", pady=(2, 10))
        self._descripcion.bind("<Configure>", lambda e: self._descripcion.config(wraplength=max(120, e.width - 4)))

        self._formulario = tk.Frame(cuerpo, bg=tema.FONDO)
        self._formulario.pack(side="top", fill="x")

        tk.Label(
            cuerpo, text="VISTA PREVIA", bg=tema.FONDO, fg=tema.TEXTO_SUAVE, font=(FAMILIA, 8, "bold"), anchor="w"
        ).pack(side="top", fill="x", pady=(12, 6))
        marco = tk.Frame(cuerpo, bg=tema.EDITOR, highlightthickness=1, highlightbackground=tema.BORDE)
        marco.pack(side="top", fill="both", expand=True)
        self._vista = tk.Text(
            marco, height=4, width=1, state="disabled", wrap="char", bg=tema.EDITOR, fg=tema.TEXTO,
            font=tema.FUENTE_CODIGO[:1] + (10,), relief="flat", borderwidth=0, highlightthickness=0,
            padx=10, pady=8, spacing1=1, spacing3=1, selectbackground=tema.SELECCION,
        )
        self._vista.pack(fill="both", expand=True)
        for etiqueta, color in COLORES_RESALTADO.items():
            self._vista.tag_configure("r_" + etiqueta, foreground=color)

    # ---------- formulario ----------

    def _mover(self, paso: int) -> None:
        ids = [b.id for b in cc.BLOQUES]
        self._elegir(ids[(ids.index(self._bloque.id) + paso) % len(ids)])

    def _elegir(self, id_bloque: str) -> None:
        self._bloque = cc.POR_ID[id_bloque]
        self._selector.config(text=f"{self._bloque.titulo}  ▾")  # la flecha indica que se despliega
        self._titulo.config(text=self._bloque.titulo)
        self._descripcion.config(text=self._bloque.descripcion)

        for hijo in self._formulario.winfo_children():
            hijo.destroy()
        self._variables.clear()
        self._textos.clear()

        for campo in self._bloque.campos:
            variable = None
            if campo.tipo == "casilla":
                variable = tk.BooleanVar(value=bool(campo.por_defecto))
                ttk.Checkbutton(self._formulario, text=campo.etiqueta, variable=variable).pack(
                    side="top", anchor="w", pady=(6, 2)
                )
            else:
                tk.Label(
                    self._formulario, text=campo.etiqueta, bg=tema.FONDO, fg=tema.TEXTO, font=(FAMILIA, 9), anchor="w"
                ).pack(side="top", fill="x", pady=(6, 2))
                if campo.tipo == "opciones":
                    variable = tk.StringVar(value=str(campo.por_defecto))
                    ttk.Combobox(self._formulario, textvariable=variable, values=campo.opciones, state="readonly").pack(
                        side="top", fill="x"
                    )
                elif campo.multilinea:
                    self._textos[campo.clave] = self._crear_texto_multilinea(campo)
                else:
                    variable = tk.StringVar(value=str(campo.por_defecto))
                    ttk.Entry(self._formulario, textvariable=variable).pack(side="top", fill="x")

            if variable is not None:
                self._variables[campo.clave] = variable
                variable.trace_add("write", lambda *_: self._actualizar())
            if campo.ayuda:
                ayuda = tk.Label(
                    self._formulario, text=campo.ayuda, bg=tema.FONDO, fg=tema.TEXTO_APAGADO, font=(FAMILIA, 8),
                    anchor="w", justify="left", wraplength=280,
                )
                ayuda.pack(side="top", fill="x", pady=(2, 0))
                ayuda.bind("<Configure>", lambda e, a=ayuda: a.config(wraplength=max(120, e.width - 4)))

        self._actualizar()

    def _crear_texto_multilinea(self, campo: cc.Campo) -> tk.Text:
        texto = tk.Text(
            self._formulario, height=2, width=1, bg=tema.EDITOR, fg=tema.TEXTO, insertbackground=tema.ACENTO,
            font=tema.FUENTE_CODIGO[:1] + (10,), relief="flat", highlightthickness=1,
            highlightbackground=tema.BORDE, highlightcolor=tema.ACENTO, padx=8, pady=6, wrap="none",
            selectbackground=tema.SELECCION,
        )
        texto.insert("1.0", str(campo.por_defecto))
        texto.pack(side="top", fill="x")
        texto.bind("<KeyRelease>", lambda e: self._actualizar())
        return texto

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
            self._estado.config(
                text="●  Corrige el formulario antes de insertar: " + self._estado.cget("text")[3:], fg=tema.ERROR
            )
            return
        if self._al_insertar(self.codigo(), self._bloque.titulo):
            self._parpadear(self._boton_insertar, "¡Insertado!")

    def _copiar(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(self.codigo())
        self._parpadear(self._estado, "●  Copiado al portapapeles", tema.EXITO)

    def _parpadear(self, widget: tk.Label, mensaje: str, color: str | None = None) -> None:
        original = (widget.cget("text"), widget.cget("fg"))
        widget.config(text=mensaje, **({"fg": color} if color else {}))
        self.after(1300, lambda: widget.winfo_exists() and widget.config(text=original[0], fg=original[1]))
