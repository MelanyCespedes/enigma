from __future__ import annotations

import builtins
import contextlib
import os
import random
import tkinter as tk
from tkinter import simpledialog, ttk

from core.errors import PistaFallidaDeRazonamiento
from core.interpreter import ejecutar
from core.lexer import tokenizar
from core.module_resolver import resolver_importaciones
from core.parser import parsear
from core.semantic import analizar


_PISTAS_GENERICAS = {
    "ErrorLexico": [
        "Hay un simbolo en tu codigo que Enigma no reconoce.",
        "Puede que haya un simbolo de mas, o que te falte alguno.",
    ],
    "ErrorSintactico": [
        "Puede que te falte un '!' al final de alguna instruccion.",
        "Revisa que cada bloque que abriste tambien lo hayas cerrado.",
        "Algo en el orden de tu codigo no es el que Enigma espera.",
    ],
    "ErrorSemantico": [
        "Quizas olvidaste declarar algo en tu codigo.",
        "Puede que estes mezclando tipos de datos que no combinan.",
        "Revisa si intentaste cambiar algo que debia quedar fijo.",
        "Puede que una de tus funciones no reciba lo que esperaba.",
    ],
    "ErrorDeImportacion": [
        "Puede que un archivo que esperabas usar no este donde lo buscaste.",
        "Revisa los nombres de los archivos que estas importando.",
    ],
    "ErrorDeEjecucion": [
        "Algo durante la ejecucion no salio como lo planeaste.",
        "Revisa los valores que le estas dando a tus operaciones.",
    ],
}
_PISTA_POR_DEFECTO = "Hay algo que no cuadra en tu codigo. Revisalo con calma."


class _EscritorTk:

    def __init__(self, panel: "PanelSalida"):
        self._panel = panel

    def write(self, texto: str) -> None:
        if texto:
            self._panel._agregar_texto(texto)

    def flush(self) -> None:
        pass


class PanelSalida(ttk.Frame):

    def __init__(self, master, obtener_proyecto, guardar_archivos_abiertos=None, **kwargs):
        super().__init__(master, **kwargs)
        self.obtener_proyecto = obtener_proyecto
        self.guardar_archivos_abiertos = guardar_archivos_abiertos
        self.programa_compilado = None
        self._ultima_firma_error = None
        self._construir_widgets()

    def _construir_widgets(self) -> None:
        barra = ttk.Frame(self)
        barra.pack(fill="x")

        self.boton_compilar = ttk.Button(barra, text="Compilar", command=self.compilar)
        self.boton_compilar.pack(side="left", padx=2, pady=2)

        self.boton_ejecutar = ttk.Button(
            barra, text="Ejecutar", command=self.ejecutar_programa, state="disabled"
        )
        self.boton_ejecutar.pack(side="left", padx=2, pady=2)

        self.etiqueta_estado = ttk.Label(barra, text="Sin compilar", anchor="w")
        self.etiqueta_estado.pack(side="left", padx=10)

        contenedor_texto = ttk.Frame(self)
        contenedor_texto.pack(fill="both", expand=True)

        self.texto = tk.Text(contenedor_texto, height=12, state="disabled", wrap="word")
        barra_desplazamiento = ttk.Scrollbar(
            contenedor_texto, orient="vertical", command=self.texto.yview
        )
        self.texto.configure(yscrollcommand=barra_desplazamiento.set)
        self.texto.pack(side="left", fill="both", expand=True)
        barra_desplazamiento.pack(side="right", fill="y")

        self.texto.tag_configure("error", foreground="#b00020")
        self.texto.tag_configure("ok", foreground="#1b7f3b")
        self.texto.tag_configure("pista", foreground="#b06000")


    def limpiar(self) -> None:
        self.texto.config(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.config(state="disabled")

    def _agregar_texto(self, texto: str, tag: str | None = None) -> None:
        self.texto.config(state="normal")
        self.texto.insert("end", texto, tag)
        self.texto.see("end")
        self.texto.config(state="disabled")

    def _firma_error(self, error: PistaFallidaDeRazonamiento) -> tuple:
        """Identifica un error de forma unica: mismo tipo, archivo, linea y
        descripcion => se considera 'el mismo problema' entre intentos."""
        return (type(error).__name__, error.archivo, error.linea, error.descripcion)

    def _pista_generica(self, error: PistaFallidaDeRazonamiento) -> str:
        opciones = _PISTAS_GENERICAS.get(type(error).__name__, [_PISTA_POR_DEFECTO])
        return random.choice(opciones)

    def _mostrar_error(self, error: PistaFallidaDeRazonamiento) -> None:
        firma = self._firma_error(error)

        if firma == self._ultima_firma_error:
            # Segundo intento con exactamente el mismo error.
            self._agregar_texto(
                "Volviste a encontrar el mismo problema. Aqui esta la explicacion completa:\n",
                "pista",
            )
            self._agregar_texto(error.mostrar_completo() + "\n", "error")
        else:
            # Primer intento: solo una pista generica.
            self._agregar_texto(
                self._pista_generica(error) + "\n"
                "Corrige lo que creas necesario y vuelve a intentarlo.\n",
                "pista",
            )

        self._ultima_firma_error = firma

    # ---------- compilar ----------

    def compilar(self) -> bool:
        """Lexer -> parser -> module_resolver -> semantico.
        Devuelve True si compilo sin errores."""
        if self.guardar_archivos_abiertos:
            self.guardar_archivos_abiertos()

        self.limpiar()
        self.programa_compilado = None
        self.boton_ejecutar.config(state="disabled")

        ruta_principal, directorio_proyecto = self.obtener_proyecto()
        if not ruta_principal:
            self._agregar_texto("No hay un archivo principal marcado en el proyecto.\n", "error")
            self.etiqueta_estado.config(text="Sin compilar")
            return False

        nombre_archivo = os.path.basename(ruta_principal)

        try:
            with open(ruta_principal, encoding="utf-8") as f:
                codigo = f.read()

            tokens = tokenizar(codigo, nombre_archivo)
            programa = parsear(tokens, nombre_archivo)
            resolver_importaciones(programa, directorio_proyecto)
            analizar(programa)
        except PistaFallidaDeRazonamiento as error:
            self._mostrar_error(error)
            self.etiqueta_estado.config(text="Compilacion fallida")
            return False

        self._ultima_firma_error = None  # se resolvio: reinicia el seguimiento
        self.programa_compilado = programa
        self.boton_ejecutar.config(state="normal")
        self.etiqueta_estado.config(text="Compilacion exitosa")
        self._agregar_texto("Compilacion exitosa.\n", "ok")
        return True

    # ---------- ejecutar ----------

    def ejecutar_programa(self) -> None:
        if self.programa_compilado is None:
            if not self.compilar():
                return

        self._agregar_texto("--- Ejecucion ---\n")

        def entrada_grafica(mensaje: str = "") -> str:
            respuesta = simpledialog.askstring("Entrada de datos", mensaje or "Consultar:")
            return respuesta or ""

        entrada_original = builtins.input
        builtins.input = entrada_grafica
        try:
            with contextlib.redirect_stdout(_EscritorTk(self)):
                ejecutar(self.programa_compilado)
        except PistaFallidaDeRazonamiento as error:
            self._mostrar_error(error)
            self.etiqueta_estado.config(text="Ejecucion con errores")
            return
        finally:
            builtins.input = entrada_original

        self._ultima_firma_error = None
        self.etiqueta_estado.config(text="Ejecucion finalizada")
        self._agregar_texto("--- Fin de la ejecucion ---\n", "ok")


if __name__ == "__main__":
    import sys

    directorio = sys.argv[1] if len(sys.argv) > 1 else "."
    archivo_principal = os.path.join(directorio, "principal.eng")

    raiz = tk.Tk()
    raiz.title("Panel de salida - prueba")
    raiz.geometry("500x300")
    panel = PanelSalida(raiz, obtener_proyecto=lambda: (archivo_principal, directorio))
    panel.pack(fill="both", expand=True)
    raiz.mainloop()