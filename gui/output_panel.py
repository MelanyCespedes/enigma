from __future__ import annotations

import builtins
import contextlib
import os
import random
import tkinter as tk
from tkinter import ttk

from core.errors import PistaFallidaDeRazonamiento
from core.interpreter import ejecutar
from core.lexer import tokenizar
from core.module_resolver import resolver_importaciones
from core.parser import parsear
from core.semantic import analizar
from gui import tema


_PISTAS_GENERICAS = {
    "ErrorLexico": [
        "Hay un símbolo en tu código que Enigma no reconoce.",
        "Puede que haya un símbolo de más, o que te falte alguno.",
    ],
    "ErrorSintactico": [
        "Puede que te falte un '!' al final de alguna instrucción.",
        "Revisa que cada bloque que abriste también lo hayas cerrado.",
        "Algo en el orden de tu código no es el que Enigma espera.",
    ],
    "ErrorSemantico": [
        "Quizás olvidaste declarar algo en tu código.",
        "Puede que estés mezclando tipos de datos que no combinan.",
        "Revisa si intentaste cambiar algo que debía quedar fijo.",
        "Puede que una de tus funciones no reciba lo que esperaba.",
    ],
    "ErrorDeImportacion": [
        "Puede que un archivo que esperabas usar no esté donde lo buscaste.",
        "Revisa los nombres de los archivos que estás importando.",
    ],
    "ErrorDeEjecucion": [
        "Algo durante la ejecución no salió como lo planeaste.",
        "Revisa los valores que le estás dando a tus operaciones.",
    ],
}
_PISTA_POR_DEFECTO = "Hay algo que no cuadra en tu código. Revísalo con calma."


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

        self.texto = tk.Text(
            contenedor_texto, height=12, state="disabled", wrap="word",
            bg=tema.EDITOR, fg=tema.TEXTO, insertbackground=tema.ACENTO,
            selectbackground=tema.SELECCION, font=tema.FUENTE_CODIGO, padx=10, pady=8,
            relief="flat", borderwidth=0, highlightthickness=0,
        )
        barra_desplazamiento = ttk.Scrollbar(
            contenedor_texto, orient="vertical", command=self.texto.yview
        )
        self.texto.configure(yscrollcommand=barra_desplazamiento.set)
        self.texto.pack(side="left", fill="both", expand=True)
        barra_desplazamiento.pack(side="right", fill="y")

        self.texto.tag_configure("error", foreground=tema.ERROR)
        self.texto.tag_configure("ok", foreground=tema.EXITO)
        self.texto.tag_configure("pista", foreground=tema.AVISO)


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
                "Volviste a encontrar el mismo problema. Aquí está la explicación completa:\n",
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

    # ---------- entrada de datos (consultar) ----------

    def _leer_en_panel(self, mensaje: str = "") -> str:
        """Pide un dato escribiendo directamente en el panel, como en una
        consola. Espera con un bucle de eventos anidado (wait_variable), asi
        la ventana sigue respondiendo mientras el interprete esta detenido."""
        if mensaje:
            self._agregar_texto(mensaje)

        texto = self.texto
        texto.config(state="normal")
        texto.mark_set("entrada_inicio", "end-1c")
        texto.mark_gravity("entrada_inicio", "left")
        texto.mark_set("insert", "end-1c")
        texto.see("end")
        texto.focus_set()

        terminado = tk.BooleanVar(master=self, value=False)
        resultado = {"valor": ""}

        def antes_de_tecla(evento):
            # Todo lo que se escriba debe quedar despues de lo ya mostrado.
            if texto.compare("insert", "<", "entrada_inicio"):
                texto.mark_set("insert", "end-1c")
            if evento.keysym in ("BackSpace", "Left") and texto.compare(
                "insert", "<=", "entrada_inicio"
            ):
                return "break"
            if evento.keysym == "Delete" and texto.compare("insert", "<", "entrada_inicio"):
                return "break"
            return None

        def enviar(_evento):
            resultado["valor"] = texto.get("entrada_inicio", "end-1c").replace("\n", "")
            texto.insert("end", "\n")
            terminado.set(True)
            return "break"

        def al_destruir(_evento):
            terminado.set(True)

        id_tecla = texto.bind("<Key>", antes_de_tecla, add="+")
        id_enviar = texto.bind("<Return>", enviar)
        id_enviar_kp = texto.bind("<KP_Enter>", enviar)
        id_destruir = self.bind("<Destroy>", al_destruir, add="+")

        self.wait_variable(terminado)

        try:
            texto.unbind("<Key>", id_tecla)
            texto.unbind("<Return>", id_enviar)
            texto.unbind("<KP_Enter>", id_enviar_kp)
            self.unbind("<Destroy>", id_destruir)
            texto.config(state="disabled")
            texto.mark_unset("entrada_inicio")
        except tk.TclError:
            pass  # la ventana se cerro mientras se esperaba la entrada

        return resultado["valor"]

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
            self.etiqueta_estado.config(text="Compilación fallida")
            return False

        self._ultima_firma_error = None  # se resolvio: reinicia el seguimiento
        self.programa_compilado = programa
        self.boton_ejecutar.config(state="normal")
        self.etiqueta_estado.config(text="Compilación exitosa")
        self._agregar_texto("Compilación exitosa.\n", "ok")
        return True

    # ---------- ejecutar ----------

    def ejecutar_programa(self) -> None:
        if self.programa_compilado is None:
            if not self.compilar():
                return

        self._agregar_texto("--- Ejecución ---\n")

        def entrada_grafica(mensaje: str = "") -> str:
            return self._leer_en_panel(mensaje)

        entrada_original = builtins.input
        builtins.input = entrada_grafica
        self.boton_compilar.config(state="disabled")
        self.boton_ejecutar.config(state="disabled")
        try:
            with contextlib.redirect_stdout(_EscritorTk(self)):
                ejecutar(self.programa_compilado)
        except PistaFallidaDeRazonamiento as error:
            self._mostrar_error(error)
            self.etiqueta_estado.config(text="Ejecución con errores")
            return
        finally:
            builtins.input = entrada_original
            self.boton_compilar.config(state="normal")
            self.boton_ejecutar.config(state="normal")

        self._ultima_firma_error = None
        self.etiqueta_estado.config(text="Ejecución finalizada")
        self._agregar_texto("--- Fin de la ejecución ---\n", "ok")


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