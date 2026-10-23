from __future__ import annotations

import builtins
import contextlib
import os
import re
import tkinter as tk
from datetime import datetime
from tkinter import ttk

from core.errors import PistaFallidaDeRazonamiento
from core.interpreter import ejecutar
from core.lexer import tokenizar
from core.module_resolver import resolver_importaciones
from core.parser import parsear
from core.semantic import analizar
from gui import recursos, tema
from gui.botones import autoocultar
from gui.botones import BotonIcono
from gui.pistas import elegir_pista


FAMILIA = "Segoe UI"
COLOR_LINEA = "#393a46"


class _EscritorTk:

    def __init__(self, panel: "PanelSalida"):
        self._panel = panel

    def write(self, texto: str) -> None:
        if texto:
            self._panel._agregar_texto(texto)

    def flush(self) -> None:
        pass


class _Solapa(tk.Frame):
    """Solapa del panel inferior (Salida / Terminal): icono, texto y subrayado amarillo."""

    def __init__(self, master, icono_activo: str, icono_inactivo: str, texto: str, comando):
        super().__init__(master, bg=tema.SALIDA, cursor="hand2")
        self._img_a = recursos.icono(icono_activo, master=master)
        self._img_g = recursos.icono(icono_inactivo, master=master)
        self._icono = tk.Label(self, bg=tema.SALIDA)
        self._icono.pack(side="left", padx=(0, 7))
        self._texto = tk.Label(self, text=texto, bg=tema.SALIDA, font=(FAMILIA, 10))
        self._texto.pack(side="left")
        self._linea = tk.Frame(self, height=2, bg=tema.SALIDA)
        self._linea.place(relx=0, rely=1.0, relwidth=1.0, anchor="sw")
        for widget in (self, self._icono, self._texto):
            widget.bind("<Button-1>", lambda e: comando())
        self.activar(False)

    def activar(self, activa: bool) -> None:
        self._icono.config(image=self._img_a if activa else self._img_g)
        self._texto.config(fg=tema.ACENTO if activa else tema.TEXTO_APAGADO)
        self._linea.config(bg=tema.ACENTO if activa else tema.SALIDA)


class PanelSalida(tk.Frame):
    """Panel inferior: solapas Salida y Terminal (bitacora), estado y boton Limpiar.

    Callbacks opcionales:
      on_pista(texto | None)     una pista nueva para la tarjeta "Primero recibe una pista"
      on_evento("ok" | "error")  resultado de compilar/ejecutar (para la campana)
    """

    def __init__(self, master, obtener_proyecto, guardar_archivos_abiertos=None,
                 on_pista=None, on_evento=None, **kwargs):
        super().__init__(master, bg=tema.SALIDA, **kwargs)
        self.obtener_proyecto = obtener_proyecto
        self.guardar_archivos_abiertos = guardar_archivos_abiertos
        self.on_pista = on_pista
        self.on_evento = on_evento
        self.programa_compilado = None
        self._ultima_firma_error = None
        self._ocupado = False
        self._en_inicio = True
        self._nombre_principal = ""
        self._solapa_actual = "salida"
        self._construir_widgets()
        self.mostrar_solapa("salida")
        self._mostrar_inicio()

    # ---------- construccion ----------

    def _construir_widgets(self) -> None:
        tk.Frame(self, height=1, bg=COLOR_LINEA).pack(side="top", fill="x")
        barra = tk.Frame(self, bg=tema.SALIDA)
        barra.pack(side="top", fill="x", padx=(16, 8))

        self._solapas = {
            "salida": _Solapa(barra, "salida_a", "salida_g", "Salida", lambda: self.mostrar_solapa("salida")),
            "terminal": _Solapa(barra, "codigo_a", "codigo_g", "Terminal", lambda: self.mostrar_solapa("terminal")),
        }
        self._solapas["salida"].pack(side="left", pady=(10, 0), ipady=6)
        self._solapas["terminal"].pack(side="left", padx=(20, 0), pady=(10, 0), ipady=6)

        self._punto = tk.Label(barra, text="●", bg=tema.SALIDA, font=(FAMILIA, 8))
        self._punto.pack(side="left", padx=(22, 6), pady=(10, 0))
        self.etiqueta_estado = tk.Label(barra, bg=tema.SALIDA, font=(FAMILIA, 10))
        self.etiqueta_estado.pack(side="left", pady=(10, 0))

        BotonIcono(
            barra, recursos.icono("papelera", master=self), self.limpiar_solapa, texto="Limpiar",
            fondo=tema.SALIDA, color=tema.TEXTO_APAGADO,
        ).pack(side="right", pady=(6, 0))

        tk.Frame(self, height=1, bg=tema.BORDE).pack(side="top", fill="x")

        cuerpo = tk.Frame(self, bg=tema.SALIDA)
        cuerpo.pack(side="top", fill="both", expand=True)
        self.texto = self._crear_texto(cuerpo)       # Salida
        self.terminal = self._crear_texto(cuerpo)    # Terminal: bitacora de la sesion

        for widget in (self.texto, self.terminal):
            widget.tag_configure("error", foreground=tema.ERROR)
            widget.tag_configure("ok", foreground=tema.EXITO)
            widget.tag_configure("pista", foreground=tema.AVISO)
            widget.tag_configure("prompt", foreground=tema.PURPURA)
            widget.tag_configure("comando", foreground=tema.TEXTO)
            widget.tag_configure("hora", foreground="#525767")

        self._poner_estado("Listo", "listo")

    def _crear_texto(self, padre) -> tk.Text:
        marco = tk.Frame(padre, bg=tema.SALIDA)
        texto = tk.Text(
            marco, state="disabled", wrap="word", height=6,
            bg=tema.SALIDA, fg=tema.TEXTO_APAGADO, insertbackground=tema.ACENTO,
            selectbackground=tema.SELECCION, font=tema.FUENTE_CODIGO[:1] + (10,), padx=18, pady=12,
            relief="flat", borderwidth=0, highlightthickness=0, spacing1=2, spacing3=2,
        )
        barra = ttk.Scrollbar(marco, orient="vertical", command=texto.yview)
        marco.grid_rowconfigure(0, weight=1)
        marco.grid_columnconfigure(0, weight=1)
        texto.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")
        texto.configure(yscrollcommand=autoocultar(barra, barra.grid, barra.grid_remove))
        return texto

    # ---------- solapas y estado ----------

    def mostrar_solapa(self, clave: str) -> None:
        self._solapa_actual = clave
        for k, solapa in self._solapas.items():
            solapa.activar(k == clave)
        self.texto.master.pack_forget()
        self.terminal.master.pack_forget()
        (self.texto if clave == "salida" else self.terminal).master.pack(fill="both", expand=True)

    def limpiar_solapa(self) -> None:
        if self._ocupado:
            return
        if self._solapa_actual == "salida":
            self._mostrar_inicio()
            self._poner_estado("Listo", "listo")
        else:
            self._borrar(self.terminal)

    def _poner_estado(self, texto: str, nivel: str = "listo") -> None:
        color = {
            "listo": tema.EXITO, "trabajando": tema.ACENTO, "error": tema.ERROR, "neutro": tema.TEXTO_APAGADO,
        }[nivel]
        self._punto.config(fg=color)
        self.etiqueta_estado.config(text=texto, fg=color)
        self.update_idletasks()

    def esta_ocupado(self) -> bool:
        return self._ocupado

    # ---------- texto ----------

    def _nombre_prompt(self) -> str:
        _, directorio = self.obtener_proyecto()
        base = os.path.basename((directorio or "").rstrip("/\\")).lower().replace("_", "-")
        return re.sub(r"[^a-z0-9-]+", "-", base).strip("-") or "caso"

    def _prompt(self) -> str:
        return f"enigma@{self._nombre_prompt()}:~$ "

    def _borrar(self, widget: tk.Text) -> None:
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.config(state="disabled")

    def _mostrar_inicio(self) -> None:
        self._borrar(self.texto)
        self._en_inicio = True
        self._agregar_texto(self._prompt(), "prompt")
        self._agregar_texto("Listo para ejecutar tu investigación...\n", "comando")

    def actualizar_proyecto(self) -> None:
        """Si el panel esta en reposo, redibuja el prompt con el nombre del proyecto."""
        if self._en_inicio and not self._ocupado:
            self._mostrar_inicio()

    def limpiar(self) -> None:
        self._borrar(self.texto)

    def _agregar_texto(self, texto: str, tag: str | None = None) -> None:
        self.texto.config(state="normal")
        self.texto.insert("end", texto, tag)
        self.texto.see("end")
        self.texto.config(state="disabled")

    def _comando(self, comando: str) -> None:
        """Escribe una linea como en una terminal: prompt + comando."""
        self._agregar_texto(self._prompt(), "prompt")
        self._agregar_texto(comando + "\n", "comando")

    def _registrar(self, mensaje: str, tag: str | None = None) -> None:
        """Agrega una linea a la bitacora (solapa Terminal)."""
        self.terminal.config(state="normal")
        self.terminal.insert("end", datetime.now().strftime("%H:%M:%S") + "  ", "hora")
        self.terminal.insert("end", mensaje + "\n", tag)
        self.terminal.see("end")
        self.terminal.config(state="disabled")

    def _avisar(self, tipo: str) -> None:
        if self.on_evento:
            self.on_evento(tipo)

    # ---------- errores ----------

    def _firma_error(self, error: PistaFallidaDeRazonamiento) -> tuple:
        """Identifica un error de forma unica: mismo tipo, archivo, linea y
        descripcion => se considera 'el mismo problema' entre intentos."""
        return (type(error).__name__, error.archivo, error.linea, error.descripcion)

    def _pista_de(self, error: PistaFallidaDeRazonamiento) -> str:
        return elegir_pista(error.pista, type(error).__name__)

    def _mostrar_error(self, error: PistaFallidaDeRazonamiento) -> None:
        firma = self._firma_error(error)
        pista = self._pista_de(error)

        if firma == self._ultima_firma_error:
            # Segundo intento con exactamente el mismo error.
            self._agregar_texto(
                "Volviste a encontrar el mismo problema. Aquí está la explicación completa:\n",
                "pista",
            )
            self._agregar_texto(error.mostrar_completo() + "\n", "error")
        else:
            # Primer intento: solo una pista, sin decir donde esta el error.
            self._agregar_texto(
                f"Pista: {pista}\nCorrige lo que creas necesario y vuelve a intentarlo.\n",
                "pista",
            )

        self._ultima_firma_error = firma
        if self.on_pista:
            self.on_pista(pista)

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
        if self._ocupado:
            return False
        if self.guardar_archivos_abiertos:
            self.guardar_archivos_abiertos()

        self.mostrar_solapa("salida")
        self.limpiar()
        self._en_inicio = False
        self.programa_compilado = None

        ruta_principal, _directorio = self.obtener_proyecto()
        if not ruta_principal:
            self._comando("compilar")
            self._agregar_texto(
                "No hay un archivo principal marcado en el proyecto.\n"
                "Haz clic derecho sobre un archivo del árbol y elige «Marcar como archivo principal».\n",
                "error",
            )
            self._poner_estado("Sin archivo principal", "error")
            self._registrar("compilar → no hay archivo principal", "error")
            self._avisar("error")
            return False

        nombre_archivo = os.path.basename(ruta_principal)
        self._nombre_principal = nombre_archivo
        self._comando(f"compilar {nombre_archivo}")
        self._poner_estado("Compilando…", "trabajando")

        try:
            with open(ruta_principal, encoding="utf-8") as f:
                codigo = f.read()

            tokens = tokenizar(codigo, nombre_archivo)
            programa = parsear(tokens, nombre_archivo)
            resolver_importaciones(programa, os.path.dirname(ruta_principal))
            analizar(programa)
        except PistaFallidaDeRazonamiento as error:
            self._mostrar_error(error)
            self._poner_estado("Compilación fallida", "error")
            self._registrar(
                f"compilar {nombre_archivo} → error de {error.tipo} ({error.archivo}, línea {error.linea})", "error"
            )
            self._avisar("error")
            return False

        self._ultima_firma_error = None  # se resolvio: reinicia el seguimiento
        self.programa_compilado = programa
        self._poner_estado("Compilación exitosa", "listo")
        self._agregar_texto("Compilación exitosa.\n", "ok")
        self._registrar(f"compilar {nombre_archivo} → exitosa", "ok")
        if self.on_pista:
            self.on_pista(None)
        self._avisar("ok")
        return True

    # ---------- ejecutar ----------

    def ejecutar_programa(self) -> None:
        if self._ocupado:
            return
        if self.programa_compilado is None:
            if not self.compilar():
                return

        self._comando(f"ejecutar {self._nombre_principal}")
        self._agregar_texto("--- Ejecución ---\n", "comando")
        self._poner_estado("Ejecutando…", "trabajando")

        def entrada_grafica(mensaje: str = "") -> str:
            return self._leer_en_panel(mensaje)

        entrada_original = builtins.input
        builtins.input = entrada_grafica
        self._ocupado = True
        try:
            with contextlib.redirect_stdout(_EscritorTk(self)):
                ejecutar(self.programa_compilado)
        except PistaFallidaDeRazonamiento as error:
            self._mostrar_error(error)
            self._poner_estado("Ejecución con errores", "error")
            self._registrar(f"ejecutar {self._nombre_principal} → error de {error.tipo} (línea {error.linea})", "error")
            self._avisar("error")
            return
        finally:
            builtins.input = entrada_original
            self._ocupado = False

        self._ultima_firma_error = None
        self._poner_estado("Ejecución finalizada", "listo")
        self._agregar_texto("--- Fin de la ejecución ---\n", "ok")
        self._registrar(f"ejecutar {self._nombre_principal} → finalizada", "ok")
        self._avisar("ok")


if __name__ == "__main__":
    import sys

    from gui.tema import aplicar_tema

    directorio = sys.argv[1] if len(sys.argv) > 1 else "."
    archivo_principal = os.path.join(directorio, "principal.eng")

    raiz = tk.Tk()
    aplicar_tema(raiz)
    raiz.title("Panel de salida - prueba")
    raiz.geometry("700x300")
    panel = PanelSalida(raiz, obtener_proyecto=lambda: (archivo_principal, directorio))
    panel.pack(fill="both", expand=True)
    raiz.mainloop()
