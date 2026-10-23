from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from gui import resaltado, tema
from gui.botones import autoocultar

FUENTE = tema.FUENTE_CODIGO
COLOR_NUMEROS_FONDO = tema.EDITOR
COLOR_NUMEROS_TEXTO = "#525767"
ESPACIADO = 3  # px extra arriba y abajo de cada linea (el diseno es mas "aireado")
COLOR_SELECCION = "#3b3f5c"

COLORES_RESALTADO = {
    resaltado.PALABRA_CLAVE: "#c07ee0",
    resaltado.TIPO: "#ffd400",
    resaltado.TEXTO: "#d9a85b",
    resaltado.VARIABLE: "#9fd7bb",
    resaltado.NUMERO: "#d19a66",
    resaltado.COMENTARIO: "#6f7384",
}

ESPACIOS_POR_TAB = 4

ETIQUETA_BUSQUEDA = "busqueda"
ETIQUETA_BUSQUEDA_ACTUAL = "busqueda_actual"
COLOR_BUSQUEDA = "#4b4f73"
MAX_COINCIDENCIAS = 5000


class PestanaEditor(ttk.Frame):
    """Un archivo abierto: numeracion de lineas + area de texto con resaltado.

    No sabe nada de archivos en disco ni de otras pestañas; avisa de los
    cambios mediante callbacks (al_modificar, al_guardar, al_ejecutar).
    """

    def __init__(self, master, ruta: str | None, al_modificar, al_guardar, al_ejecutar, tam_fuente: int = FUENTE[1]):
        super().__init__(master)
        self.ruta = ruta
        self.modificado = False
        self._fin_de_linea = "\n"
        self._cargando = False
        self._resaltado_pendiente = None
        self._al_modificar = al_modificar
        self._fuente = (FUENTE[0], tam_fuente)

        # Busqueda (Ctrl+F): el editor la controla desde fuera.
        self.al_actualizar_busqueda = None  # callback(actual, total)
        self._consulta = ""
        self._coincidencias: list[tuple[str, str]] = []
        self._indice: int | None = None

        self.numeros = tk.Text(
            self, width=5, padx=10, pady=8, font=self._fuente, wrap="none", state="disabled",
            spacing1=ESPACIADO, spacing3=ESPACIADO,
            bg=COLOR_NUMEROS_FONDO, fg=COLOR_NUMEROS_TEXTO, relief="flat", borderwidth=0,
            highlightthickness=0, cursor="arrow", takefocus=0,
        )
        self.numeros.tag_configure("derecha", justify="right")

        self.texto = tk.Text(
            self, padx=14, pady=8, font=self._fuente, wrap="none", undo=True, maxundo=-1,
            spacing1=ESPACIADO, spacing3=ESPACIADO,
            bg=tema.EDITOR, fg=tema.TEXTO, insertbackground=tema.ACENTO,
            selectbackground=COLOR_SELECCION, relief="flat", borderwidth=0,
            highlightthickness=0, tabs=("1c",),
        )
        for etiqueta, color in COLORES_RESALTADO.items():
            self.texto.tag_configure(etiqueta, foreground=color)
        self.texto.tag_configure(resaltado.COMENTARIO, font=self._fuente + ("italic",))
        self.texto.tag_configure(resaltado.TIPO, font=self._fuente + ("bold",))
        self.texto.tag_configure(ETIQUETA_BUSQUEDA, background=COLOR_BUSQUEDA)
        self.texto.tag_configure(
            ETIQUETA_BUSQUEDA_ACTUAL, background=tema.ACENTO, foreground="#1b1c25"
        )
        self.texto.tag_raise("sel")

        self.barra_v = ttk.Scrollbar(self, orient="vertical", command=self._desplazar)
        self.barra_h = ttk.Scrollbar(self, orient="horizontal", command=self.texto.xview)
        self._poner_barra_v = autoocultar(
            self.barra_v, lambda: self.barra_v.grid(), lambda: self.barra_v.grid_remove()
        )
        self.texto.configure(
            yscrollcommand=self._al_desplazar,
            xscrollcommand=autoocultar(self.barra_h, lambda: self.barra_h.grid(), lambda: self.barra_h.grid_remove()),
        )

        self._separador = tk.Frame(self, width=1, bg=tema.BORDE)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.numeros.grid(row=0, column=0, sticky="ns")
        self._separador.grid(row=0, column=1, sticky="ns")
        self.texto.grid(row=0, column=2, sticky="nsew")
        self.barra_v.grid(row=0, column=3, sticky="ns")
        self.barra_h.grid(row=1, column=2, sticky="ew")

        self.texto.bind("<<Modified>>", self._cuando_cambia_el_texto)
        self.texto.bind("<Tab>", self._insertar_espacios)
        self.texto.bind("<Control-s>", self._como_atajo(al_guardar))
        self.texto.bind("<Control-Return>", self._como_atajo(al_ejecutar))
        self.numeros.bind("<MouseWheel>", lambda e: "break")

        self._actualizar_numeros()

    def cambiar_fuente(self, tam_fuente: int) -> None:
        """Cambia el tamaño de letra (preferencias)."""
        self._fuente = (FUENTE[0], tam_fuente)
        self.texto.config(font=self._fuente)
        self.numeros.config(font=self._fuente)
        self.texto.tag_configure(resaltado.COMENTARIO, font=self._fuente + ("italic",))
        self.texto.tag_configure(resaltado.TIPO, font=self._fuente + ("bold",))

    @staticmethod
    def _como_atajo(accion):
        """Envuelve 'accion' como manejador de teclado que evita la accion por
        defecto del Text (p. ej. que Ctrl+Enter inserte un salto de linea)."""
        def manejador(_evento):
            accion()
            return "break"
        return manejador

    # ---------- desplazamiento ----------

    def _desplazar(self, *args) -> None:
        self.texto.yview(*args)
        self.numeros.yview(*args)

    def _al_desplazar(self, primero, ultimo) -> None:
        self._poner_barra_v(primero, ultimo)
        self.numeros.yview_moveto(primero)

    # ---------- contenido ----------

    def cargar(self, contenido: str, fin_de_linea: str = "\n") -> None:
        self._cargando = True
        self._fin_de_linea = fin_de_linea
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", contenido)
        self.texto.edit_reset()
        self.texto.edit_modified(False)
        self._cargando = False
        self._establecer_modificado(False)
        self._actualizar_numeros()
        self._resaltar()

    def obtener_contenido(self) -> str:
        return self.texto.get("1.0", "end-1c")

    def fin_de_linea(self) -> str:
        return self._fin_de_linea

    def marcar_guardado(self) -> None:
        self._establecer_modificado(False)

    def _establecer_modificado(self, valor: bool) -> None:
        if self.modificado != valor:
            self.modificado = valor
            self._al_modificar(self)

    def _cuando_cambia_el_texto(self, _evento=None) -> None:
        if not self.texto.edit_modified():
            return
        self.texto.edit_modified(False)
        if self._cargando:
            return
        self._establecer_modificado(True)
        self._actualizar_numeros()
        if self._resaltado_pendiente is not None:
            self.after_cancel(self._resaltado_pendiente)
        self._resaltado_pendiente = self.after(80, self._resaltar)

    def _insertar_espacios(self, _evento) -> str:
        self.texto.insert("insert", " " * ESPACIOS_POR_TAB)
        return "break"

    # ---------- numeracion y resaltado ----------

    def _actualizar_numeros(self) -> None:
        total = int(self.texto.index("end-1c").split(".")[0])
        self.numeros.config(state="normal")
        self.numeros.delete("1.0", "end")
        self.numeros.insert("1.0", "\n".join(str(n) for n in range(1, total + 1)), "derecha")
        self.numeros.config(state="disabled")
        self.numeros.yview_moveto(self.texto.yview()[0])

    def _resaltar(self) -> None:
        self._resaltado_pendiente = None
        for etiqueta in resaltado.ETIQUETAS:
            self.texto.tag_remove(etiqueta, "1.0", "end")
        codigo = self.obtener_contenido()
        for etiqueta, inicio, fin in resaltado.calcular_resaltado(codigo):
            self.texto.tag_add(etiqueta, f"1.0+{inicio}c", f"1.0+{fin}c")
        if self._consulta:
            self._marcar_coincidencias()
            self._indice = None
            self._avisar_busqueda()

    # ---------- busqueda ----------

    def buscar(self, consulta: str) -> int:
        """Marca todas las coincidencias (sin distinguir mayusculas) y devuelve
        cuantas hay. Una consulta vacia limpia la busqueda."""
        self._consulta = consulta
        self._indice = None
        self._marcar_coincidencias()
        return len(self._coincidencias)

    def _marcar_coincidencias(self) -> None:
        for etiqueta in (ETIQUETA_BUSQUEDA, ETIQUETA_BUSQUEDA_ACTUAL):
            self.texto.tag_remove(etiqueta, "1.0", "end")
        self._coincidencias = []
        if not self._consulta:
            return

        cuenta = tk.IntVar(self)
        posicion = "1.0"
        while len(self._coincidencias) < MAX_COINCIDENCIAS:
            inicio = self.texto.search(
                self._consulta, posicion, stopindex="end", nocase=True, count=cuenta
            )
            if not inicio or cuenta.get() == 0:
                break
            fin = self.texto.index(f"{inicio}+{cuenta.get()}c")
            self.texto.tag_add(ETIQUETA_BUSQUEDA, inicio, fin)
            self._coincidencias.append((inicio, fin))
            posicion = fin

    def mover_coincidencia(self, direccion: int) -> tuple[int, int]:
        """Salta a la coincidencia siguiente (+1) o anterior (-1).
        Devuelve (numero de la actual, total); (0, 0) si no hay ninguna."""
        total = len(self._coincidencias)
        if total == 0:
            return (0, 0)

        if self._indice is None:
            cursor = self.texto.index("insert")
            if direccion > 0:
                despues = [i for i, (a, _) in enumerate(self._coincidencias) if self.texto.compare(a, ">=", cursor)]
                self._indice = despues[0] if despues else 0
            else:
                antes = [i for i, (a, _) in enumerate(self._coincidencias) if self.texto.compare(a, "<", cursor)]
                self._indice = antes[-1] if antes else total - 1
        else:
            self._indice = (self._indice + direccion) % total

        inicio, fin = self._coincidencias[self._indice]
        self.texto.tag_remove(ETIQUETA_BUSQUEDA_ACTUAL, "1.0", "end")
        self.texto.tag_add(ETIQUETA_BUSQUEDA_ACTUAL, inicio, fin)
        self.texto.mark_set("insert", inicio)
        self.texto.see(inicio)
        return (self._indice + 1, total)

    def texto_seleccionado(self) -> str:
        try:
            return self.texto.get("sel.first", "sel.last")
        except tk.TclError:
            return ""

    def _avisar_busqueda(self) -> None:
        if self.al_actualizar_busqueda:
            self.al_actualizar_busqueda(0, len(self._coincidencias))
