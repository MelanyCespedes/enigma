"""Panel "Guia del detective": consulta del lenguaje (PDF, seccion 10).

El contenido vive en guia_contenido.py; aqui solo se dibuja.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from gui import resaltado, tema
from gui.barra_pestanas import BotonPlano
from gui.guia_contenido import (
    SECCIONES,
    POR_ID,
    Codigo,
    Ficha,
    Lista,
    Nota,
    Parrafo,
    Subtitulo,
    Termino,
)
from gui.pestana_editor import COLORES_RESALTADO

FAMILIA = "Segoe UI"
COLOR_CODIGO = tema.SUPERFICIE
COLOR_NOTA = "#2a2145"
COLOR_TEXTO_CUERPO = "#c9ccd6"


class GuiaDetective(tk.Frame):
    """Panel lateral con las secciones de la guia.

    al_insertar(texto) -> bool  inserta codigo en el editor (True si se pudo)
    al_cerrar()                 oculta el panel
    """

    def __init__(self, master, al_insertar, al_cerrar):
        super().__init__(master, bg=tema.FONDO)
        self._al_insertar = al_insertar
        self._seccion = SECCIONES[0]

        self._construir_cabecera(al_cerrar)
        self._construir_cuerpo()
        self.abrir_seccion(self._seccion.id)

    # ---------- construccion ----------

    def _construir_cabecera(self, al_cerrar) -> None:
        barra = tk.Frame(self, bg=tema.FONDO)
        barra.pack(side="top", fill="x")
        tk.Frame(self, height=1, bg=tema.BORDE).pack(side="top", fill="x")

        self._anterior = BotonPlano(barra, "‹", lambda: self._mover(-1), font=(FAMILIA, 12))
        self._anterior.pack(side="left")

        self._selector = tk.Menubutton(
            barra, bg=tema.FONDO, fg=tema.TEXTO, activebackground=tema.SELECCION_SUAVE,
            activeforeground=tema.TEXTO, relief="flat", borderwidth=0, padx=8, pady=6,
            font=(FAMILIA, 10, "bold"), anchor="w",
        )
        menu = tk.Menu(self._selector, tearoff=0, borderwidth=1)
        for seccion in SECCIONES:
            menu.add_command(label=seccion.titulo, command=lambda s=seccion.id: self.abrir_seccion(s))
        self._selector.config(menu=menu)
        self._selector.pack(side="left", fill="x", expand=True)

        self._siguiente = BotonPlano(barra, "›", lambda: self._mover(1), font=(FAMILIA, 12))
        self._siguiente.pack(side="left")
        BotonPlano(barra, "×", al_cerrar, font=(FAMILIA, 12)).pack(side="left")

    def _construir_cuerpo(self) -> None:
        contenedor = tk.Frame(self, bg=tema.FONDO)
        contenedor.pack(side="top", fill="both", expand=True)

        self._texto = tk.Text(
            contenedor, wrap="word", state="disabled", cursor="arrow",
            bg=tema.FONDO, fg=COLOR_TEXTO_CUERPO, font=(FAMILIA, 10), padx=14, pady=10,
            relief="flat", borderwidth=0, highlightthickness=0, selectbackground=tema.SELECCION,
            spacing1=1, spacing3=3, width=1, height=1,
        )
        barra = ttk.Scrollbar(contenedor, orient="vertical", command=self._texto.yview)
        self._texto.configure(yscrollcommand=barra.set)
        self._texto.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        t = self._texto
        t.tag_configure("titulo", font=(FAMILIA, 15, "bold"), foreground=tema.ACENTO, spacing3=2)
        t.tag_configure("resumen", foreground=tema.TEXTO_SUAVE, spacing3=8)
        t.tag_configure("sub", font=(FAMILIA, 11, "bold"), foreground=tema.TEXTO, spacing1=14, spacing3=4)
        t.tag_configure("p", spacing3=6)
        t.tag_configure("item", lmargin1=8, lmargin2=22, spacing3=3)
        t.tag_configure(
            "nota", background=COLOR_NOTA, foreground="#e0d4ff", lmargin1=8, lmargin2=8,
            rmargin=8, spacing1=6, spacing3=6,
        )
        t.tag_configure("nota_etq", font=(FAMILIA, 10, "bold"), foreground="#c9a7ff")
        t.tag_configure("etq_codigo", foreground=tema.TEXTO_SUAVE, font=(FAMILIA, 8, "bold"), spacing1=8)
        t.tag_configure(
            "codigo", font=tema.FUENTE_CODIGO[:1] + (10,), background=COLOR_CODIGO, foreground=tema.TEXTO,
            lmargin1=10, lmargin2=10, rmargin=10, spacing1=0, spacing2=0, spacing3=0, wrap="char",
        )
        t.tag_configure("plantilla", foreground="#a9b1c6")
        t.tag_configure("termino", font=tema.FUENTE_CODIGO[:1] + (10, "bold"), foreground=COLORES_RESALTADO[resaltado.PALABRA_CLAVE], spacing1=10)
        t.tag_configure("etq", foreground=tema.TEXTO_SUAVE, font=(FAMILIA, 8, "bold"), lmargin1=8, lmargin2=8)
        t.tag_configure("def", lmargin1=8, lmargin2=8)
        t.tag_configure("ficha", font=tema.FUENTE_CODIGO[:1] + (11, "bold"), foreground=tema.ACENTO, spacing1=14)
        t.tag_configure("ficha_etq", font=(FAMILIA, 9, "bold"), foreground=tema.TEXTO_SUAVE, lmargin1=8, lmargin2=8, spacing1=4)
        t.tag_configure("ficha_txt", lmargin1=8, lmargin2=8)
        for etiqueta, color in COLORES_RESALTADO.items():
            t.tag_configure("r_" + etiqueta, foreground=color)
        t.tag_raise("sel")

    # ---------- navegacion ----------

    def abrir_seccion(self, id_seccion: str) -> None:
        seccion = POR_ID.get(id_seccion)
        if seccion is None:
            return
        self._seccion = seccion
        self._selector.config(text=f"{seccion.titulo}   ▾")
        indice = SECCIONES.index(seccion)
        self._anterior.config(fg=tema.BORDE if indice == 0 else tema.TEXTO_SUAVE)
        self._siguiente.config(fg=tema.BORDE if indice == len(SECCIONES) - 1 else tema.TEXTO_SUAVE)
        self._dibujar(seccion)
        self._texto.yview_moveto(0)

    def seccion_actual(self) -> str:
        return self._seccion.id

    def _mover(self, paso: int) -> None:
        indice = SECCIONES.index(self._seccion) + paso
        if 0 <= indice < len(SECCIONES):
            self.abrir_seccion(SECCIONES[indice].id)

    # ---------- dibujo ----------

    def _dibujar(self, seccion) -> None:
        t = self._texto
        t.config(state="normal")
        t.delete("1.0", "end")
        t.insert("end", seccion.titulo + "\n", "titulo")
        t.insert("end", seccion.resumen + "\n", "resumen")

        for bloque in seccion.bloques:
            if isinstance(bloque, Parrafo):
                t.insert("end", bloque.texto + "\n", "p")
            elif isinstance(bloque, Subtitulo):
                t.insert("end", bloque.texto + "\n", "sub")
            elif isinstance(bloque, Nota):
                t.insert("end", "Nota  ", ("nota", "nota_etq"))
                t.insert("end", bloque.texto + "\n", "nota")
            elif isinstance(bloque, Lista):
                for item in bloque.items:
                    t.insert("end", "•  " + item + "\n", "item")
            elif isinstance(bloque, Codigo):
                self._dibujar_codigo(bloque)
            elif isinstance(bloque, Termino):
                self._dibujar_termino(bloque)
            elif isinstance(bloque, Ficha):
                self._dibujar_ficha(bloque)

        t.insert("end", "\n")
        t.config(state="disabled")

    def _insertar_codigo(self, codigo: str, plantilla: bool = False) -> None:
        """Escribe codigo con el mismo coloreado del editor."""
        t = self._texto
        inicio = t.index("end-1c")
        t.insert("end", codigo, ("codigo", "plantilla") if plantilla else "codigo")
        if plantilla:
            return
        for etiqueta, desde, hasta in resaltado.calcular_resaltado(codigo):
            t.tag_add("r_" + etiqueta, f"{inicio}+{desde}c", f"{inicio}+{hasta}c")

    def _dibujar_codigo(self, bloque: Codigo) -> None:
        t = self._texto
        if bloque.titulo:
            t.insert("end", bloque.titulo.upper() + "\n", "etq_codigo")
        # Margen superior e inferior del recuadro: lineas vacias con el mismo fondo.
        t.insert("end", " \n", "codigo")
        self._insertar_codigo(bloque.texto, bloque.plantilla)
        t.insert("end", "\n \n", "codigo")

        fila = tk.Frame(t, bg=tema.FONDO)
        if not bloque.plantilla:
            self._boton(fila, "Insertar en el editor", lambda boton, b=bloque: self._insertar(b.texto, boton), True)
        self._boton(fila, "Copiar", lambda boton, b=bloque: self._copiar(b.texto, boton), False)
        t.window_create("end", window=fila, pady=4)
        t.insert("end", "\n")

    def _dibujar_termino(self, termino: Termino) -> None:
        t = self._texto
        t.insert("end", termino.nombre + "\n", "termino")
        t.insert("end", termino.descripcion + "\n", "def")
        if termino.uso:
            t.insert("end", "USO\n", "etq")
            self._insertar_codigo(termino.uso, plantilla=True)
            t.insert("end", "\n")
        if termino.ejemplo:
            t.insert("end", "EJEMPLO\n", "etq")
            self._insertar_codigo(termino.ejemplo)
            t.insert("end", "\n")

    def _dibujar_ficha(self, ficha: Ficha) -> None:
        t = self._texto
        t.insert("end", ficha.nombre + "\n", "ficha")
        for etiqueta, texto in (("DECLARACIÓN", None), ("USO", ficha.uso),
                                ("OPERACIONES PERMITIDAS", ficha.operaciones),
                                ("RESTRICCIONES", ficha.restricciones)):
            t.insert("end", etiqueta + "\n", "ficha_etq")
            if texto is None:
                self._insertar_codigo(ficha.declaracion)
                t.insert("end", "\n")
            else:
                t.insert("end", texto + "\n", "ficha_txt")

    # ---------- botones de los bloques de codigo ----------

    def _boton(self, padre, texto: str, comando, principal: bool) -> tk.Label:
        fondo = tema.ACENTO if principal else tema.SUPERFICIE
        color = "#1b1c25" if principal else tema.TEXTO
        boton = tk.Label(
            padre, text=texto, bg=fondo, fg=color, padx=10, pady=3, cursor="hand2",
            font=(FAMILIA, 9, "bold" if principal else "normal"),
        )
        boton.pack(side="left", padx=(0, 6))
        boton.bind("<Button-1>", lambda e: comando(boton))
        return boton

    def _insertar(self, texto: str, boton: tk.Label) -> None:
        codigo_bloque = next(
            (
                bloque for bloque in self._seccion.bloques
                if isinstance(bloque, Codigo) and bloque.texto == texto
            ),
            None,
        )
        nombre = codigo_bloque.titulo if codigo_bloque is not None else "codigo_enigma"
        if self._al_insertar(texto, nombre):
            self._avisar(boton, "¡Insertado!")

    def _copiar(self, texto: str, boton: tk.Label) -> None:
        self.clipboard_clear()
        self.clipboard_append(texto)
        self._avisar(boton, "¡Copiado!")

    def _avisar(self, boton: tk.Label, mensaje: str) -> None:
        """Cambia el texto del boton un instante para confirmar la accion."""
        original = boton.cget("text")
        boton.config(text=mensaje)
        self.after(1300, lambda: boton.winfo_exists() and boton.config(text=original))
