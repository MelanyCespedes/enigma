from __future__ import annotations

import math
import tkinter as tk

from gui import tema

CERRAR = "×"
MODIFICADO = "●"


class BotonPlano(tk.Label):

    def __init__(self, master, texto: str, comando, color: str = tema.TEXTO_SUAVE, **kwargs):
        super().__init__(
            master, text=texto, bg=tema.FONDO, fg=color, padx=10, pady=5, cursor="hand2", **kwargs
        )
        self._color = color
        self.bind("<Button-1>", lambda e: comando())
        self.bind("<Enter>", lambda e: self.config(bg=tema.SELECCION_SUAVE, fg=tema.TEXTO))
        self.bind("<Leave>", lambda e: self.config(bg=tema.FONDO, fg=self._color))


class _Pestana(tk.Frame):
    def __init__(self, master, clave: str, titulo: str, al_seleccionar, al_cerrar):
        super().__init__(master, bg=tema.FONDO)
        self.clave = clave
        self._activa = False
        self._modificada = False
        self._sobre = False

        self._subrayado = tk.Frame(self, height=2, bg=tema.FONDO)
        self._subrayado.pack(side="bottom", fill="x")
        self._nombre = tk.Label(self, text=titulo, padx=0, pady=6, cursor="hand2")
        self._nombre.pack(side="left", padx=(12, 6))
        self._cierre = tk.Label(self, text=" ", width=2, cursor="hand2")
        self._cierre.pack(side="left", padx=(0, 6))

        for widget in (self, self._nombre):
            widget.bind("<Button-1>", lambda e: al_seleccionar(clave))
        self._cierre.bind("<Button-1>", lambda e: al_cerrar(clave))
        for widget in (self, self._nombre, self._cierre, self._subrayado):
            widget.bind("<ButtonRelease-2>", lambda e: al_cerrar(clave))
            widget.bind("<Enter>", self._pidio_revisar_mouse)
            widget.bind("<Leave>", self._pidio_revisar_mouse)

        self.refrescar()

    def _pidio_revisar_mouse(self, _evento=None) -> None:
        # Entrar a un hijo dispara Leave en el padre; se revisa donde quedo el mouse.
        self.after_idle(self._revisar_mouse)

    def _revisar_mouse(self) -> None:
        try:
            x, y = self.winfo_pointerxy()
            widget = self.winfo_containing(x, y)
        except (tk.TclError, KeyError):
            return
        sobre = widget is not None and str(widget).startswith(str(self))
        if sobre != self._sobre:
            self._sobre = sobre
            self.refrescar()

    def configurar(self, titulo: str, modificada: bool) -> None:
        self._nombre.config(text=titulo)
        self._modificada = modificada
        self.refrescar()

    def activar(self, activa: bool) -> None:
        self._activa = activa
        self.refrescar()

    def refrescar(self) -> None:
        fondo = tema.EDITOR if self._activa else tema.FONDO
        if self._sobre and not self._activa:
            fondo = tema.SELECCION_SUAVE
        color_texto = tema.TEXTO if (self._activa or self._sobre) else tema.TEXTO_SUAVE

        if self._sobre or (self._activa and not self._modificada):
            simbolo = CERRAR
        elif self._modificada:
            simbolo = MODIFICADO
        else:
            simbolo = " "

        for widget in (self, self._nombre, self._cierre):
            widget.config(bg=fondo)
        self._nombre.config(fg=color_texto)
        self._cierre.config(fg=tema.ACENTO if simbolo == MODIFICADO else color_texto, text=simbolo)
        self._subrayado.config(bg=tema.ACENTO if self._activa else fondo)




class BarraPestanas(tk.Frame):

    PASO_PX = 40  # pixeles por "unidad" de desplazamiento

    def __init__(self, master, al_seleccionar, al_cerrar, al_nuevo=None):
        super().__init__(master, bg=tema.FONDO)
        self._al_seleccionar = al_seleccionar
        self._al_cerrar = al_cerrar
        self._pestanas: dict[str, _Pestana] = {}
        self._pendiente: str | None = None  # pestaña que debe quedar visible

        tk.Frame(self, height=1, bg=tema.BORDE).pack(side="bottom", fill="x")
        fila = tk.Frame(self, bg=tema.FONDO)
        fila.pack(side="top", fill="x")
        fila.grid_columnconfigure(1, weight=1)

        self._flecha_izq = BotonPlano(fila, "‹", lambda: self._desplazar(-3))
        self._flecha_der = BotonPlano(fila, "›", lambda: self._desplazar(3))
        self._flecha_izq.grid(row=0, column=0, sticky="ns")
        self._flecha_der.grid(row=0, column=2, sticky="ns")

        self._lienzo = tk.Canvas(
            fila, bg=tema.FONDO, highlightthickness=0, borderwidth=0, width=1,
            xscrollincrement=self.PASO_PX, xscrollcommand=self._al_desplazar,
        )
        self._lienzo.grid(row=0, column=1, sticky="nsew")
        self._contenedor = tk.Frame(self._lienzo, bg=tema.FONDO)
        self._lienzo.create_window((0, 0), window=self._contenedor, anchor="nw")

        self._acciones = tk.Frame(fila, bg=tema.FONDO)
        self._acciones.grid(row=0, column=3, sticky="ns")

        self._boton_nuevo = None
        if al_nuevo is not None:
            self._boton_nuevo = BotonPlano(self._contenedor, "+", al_nuevo, font=("Segoe UI", 12))
            self._boton_nuevo.pack(side="left")

        self._contenedor.bind("<Configure>", self._al_cambiar_tamano)
        self._lienzo.bind("<Configure>", self._al_cambiar_tamano)
        for widget in (self._lienzo, self._contenedor):
            self._conectar_rueda(widget)
        self._flecha_izq.grid_remove()
        self._flecha_der.grid_remove()

    # ---------- pestañas ----------

    def agregar(self, clave: str, titulo: str) -> None:
        pestana = _Pestana(self._contenedor, clave, titulo, self._al_seleccionar, self._al_cerrar)
        if self._boton_nuevo is not None:
            pestana.pack(side="left", fill="y", before=self._boton_nuevo)
        else:
            pestana.pack(side="left", fill="y")
        for widget in (pestana, *pestana.winfo_children()):
            self._conectar_rueda(widget)
        self._pestanas[clave] = pestana

    def quitar(self, clave: str) -> None:
        pestana = self._pestanas.pop(clave, None)
        if pestana is not None:
            pestana.destroy()

    def seleccionar(self, clave: str) -> None:
        for k, pestana in self._pestanas.items():
            pestana.activar(k == clave)
        if clave in self._pestanas:
            self._pendiente = clave
            self.after_idle(self._mostrar_pendiente)

    def actualizar(self, clave: str, titulo: str, modificada: bool) -> None:
        if clave in self._pestanas:
            self._pestanas[clave].configurar(titulo, modificada)

    def agregar_accion(self, texto: str, comando, destacada: bool = False) -> BotonPlano:
        boton = BotonPlano(
            self._acciones, texto, comando, color=tema.ACENTO if destacada else tema.TEXTO_SUAVE
        )
        boton.pack(side="right")
        return boton

    # ---------- desplazamiento ----------

    def _conectar_rueda(self, widget) -> None:
        widget.bind("<MouseWheel>", self._rueda, add="+")
        widget.bind("<Button-4>", lambda e: self._desplazar(-3), add="+")  # Linux
        widget.bind("<Button-5>", lambda e: self._desplazar(3), add="+")

    def _rueda(self, evento) -> None:
        self._desplazar(-3 if evento.delta > 0 else 3)

    def _desplazar(self, unidades: int) -> None:
        self._pendiente = None
        if self._hay_desborde():
            self._lienzo.xview_scroll(unidades, "units")

    def _hay_desborde(self) -> bool:
        return self._contenedor.winfo_reqwidth() > self._lienzo.winfo_width()

    def _al_cambiar_tamano(self, _evento=None) -> None:
        ancho = self._contenedor.winfo_reqwidth()
        alto = self._contenedor.winfo_reqheight()
        self._lienzo.configure(scrollregion=(0, 0, ancho, alto), height=alto)

        if self._hay_desborde():
            self._flecha_izq.grid()
            self._flecha_der.grid()
        else:
            self._flecha_izq.grid_remove()
            self._flecha_der.grid_remove()
            self._lienzo.xview_moveto(0)

        if self._pendiente:
            self.after_idle(self._mostrar_pendiente)

    def _al_desplazar(self, primero, ultimo) -> None:
        self._flecha_izq.config(fg=tema.BORDE if float(primero) <= 0.0 else tema.TEXTO_SUAVE)
        self._flecha_der.config(fg=tema.BORDE if float(ultimo) >= 1.0 else tema.TEXTO_SUAVE)

    def _mostrar_pendiente(self) -> None:
        pestana = self._pestanas.get(self._pendiente) if self._pendiente else None
        if pestana is None:
            self._pendiente = None
            return
        if not self._hay_desborde():
            return  # si luego aparece desborde, _al_cambiar_tamano reintenta
        if pestana.winfo_width() <= 1 or self._contenedor.winfo_width() < self._contenedor.winfo_reqwidth():
            return  # el reparto de espacio todavia no termino

        total = self._contenedor.winfo_reqwidth()
        visible = self._lienzo.winfo_width()
        izquierda = self._lienzo.canvasx(0)
        inicio = pestana.winfo_x()
        fin = inicio + pestana.winfo_width()
        paso = self.PASO_PX  # el lienzo solo se mueve de a 'paso' pixeles
        if inicio < izquierda:
            self._lienzo.xview_moveto((inicio // paso * paso) / total)
        elif fin > izquierda + visible:
            self._lienzo.xview_moveto((math.ceil((fin - visible) / paso) * paso) / total)