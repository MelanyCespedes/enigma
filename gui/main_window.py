from __future__ import annotations

import sys
import tkinter as tk
from tkinter import filedialog, ttk

from gui import dialogos
from gui.editor_widget import EditorCodigo
from gui.file_tree import ArbolArchivos
from gui.output_panel import PanelSalida
from gui.tema import BORDE, FONDO, SELECCION_SUAVE, TEXTO, aplicar_tema, oscurecer_barra_titulo


class VentanaPrincipal(tk.Tk):
    """Une el arbol de archivos, el editor y el panel de salida."""

    def __init__(self, carpeta_inicial: str | None = None):
        super().__init__()
        self.title("Enigma - Laboratorio de razonamiento")
        self.geometry("1200x720")
        self.minsize(800, 500)

        aplicar_tema(self)
        self._construir_widgets()
        self._construir_menu()
        self._conectar_atajos()
        self.protocol("WM_DELETE_WINDOW", self._cerrar_ventana)

        oscurecer_barra_titulo(self)

        if carpeta_inicial:
            self.arbol.cargar_proyecto(carpeta_inicial)

    # ---------- construccion ----------

    def _construir_widgets(self) -> None:
        horizontal = ttk.PanedWindow(self, orient="horizontal")
        horizontal.pack(side="bottom", fill="both", expand=True)
        self._contenedor = horizontal

        # Cada widget debe crearse como hijo del panel que lo contiene; si no,
        # queda tapado por su "hermano" y no se ve.
        vertical = ttk.PanedWindow(horizontal, orient="vertical")
        self.editor = EditorCodigo(
            vertical,
            on_ejecutar=self.compilar_y_ejecutar,
            on_nuevo=lambda: self.arbol.nuevo_archivo(),
        )
        self.arbol = ArbolArchivos(horizontal, on_abrir_archivo=self.editor.abrir)
        self.panel = PanelSalida(
            vertical,
            obtener_proyecto=lambda: (
                self.arbol.obtener_archivo_principal(),
                self.arbol.obtener_directorio_proyecto(),
            ),
            guardar_archivos_abiertos=self.editor.guardar_todos,
        )
        # El boton Ejecutar del panel reutiliza el ultimo programa compilado;
        # aqui se recompila siempre para no ejecutar una version vieja del codigo.
        self.panel.boton_ejecutar.config(command=self.compilar_y_ejecutar)
        self.panel.boton_ejecutar.config(state="normal")

        vertical.add(self.editor, weight=4)
        vertical.add(self.panel, weight=1)

        horizontal.add(self.arbol, weight=0)
        horizontal.add(vertical, weight=1)

    def _construir_menu(self) -> None:
        barra = tk.Frame(self, bg=FONDO)
        barra.pack(side="top", fill="x", before=self._contenedor)
        tk.Frame(self, bg=BORDE, height=1).pack(side="top", fill="x", before=self._contenedor)

        archivo = self._crear_menu(barra, "Archivo")
        archivo.add_command(label="Abrir carpeta...", accelerator="Ctrl+O", command=self.abrir_carpeta)
        archivo.add_separator()
        archivo.add_command(label="Guardar", accelerator="Ctrl+S", command=self.editor.guardar_activo)
        archivo.add_command(label="Guardar todo", command=self.editor.guardar_todos)
        archivo.add_command(label="Cerrar pestaña", accelerator="Ctrl+W", command=self.editor.cerrar)
        archivo.add_separator()
        archivo.add_command(label="Salir", command=self._cerrar_ventana)

        editar = self._crear_menu(barra, "Editar")
        editar.add_command(label="Buscar / cerrar búsqueda", accelerator="Ctrl+F", command=self.editor.alternar_busqueda)

        ejecutar = self._crear_menu(barra, "Ejecutar")
        ejecutar.add_command(label="Compilar", command=self.panel.compilar)
        ejecutar.add_command(
            label="Ejecutar caso", accelerator="Ctrl+Enter", command=self.compilar_y_ejecutar
        )

    def _crear_menu(self, barra: tk.Frame, texto: str) -> tk.Menu:
        boton = tk.Menubutton(
            barra, text=texto, bg=FONDO, fg=TEXTO, activebackground=SELECCION_SUAVE,
            activeforeground=TEXTO, relief="flat", borderwidth=0, padx=12, pady=5,
        )
        boton.pack(side="left")
        menu = tk.Menu(boton, tearoff=0, borderwidth=1)
        boton.config(menu=menu)
        return menu

    def _conectar_atajos(self) -> None:
        self.bind("<Control-o>", lambda e: self.abrir_carpeta())
        self.bind("<Control-Return>", lambda e: self.compilar_y_ejecutar())

    # ---------- acciones ----------

    def abrir_carpeta(self) -> None:
        ruta = filedialog.askdirectory(title="Selecciona la carpeta del proyecto")
        if ruta:
            self.arbol.cargar_proyecto(ruta)

    def compilar_y_ejecutar(self) -> None:
        try:
            if self.panel.compilar():
                self.panel.ejecutar_programa()
        finally:
            # compilar() deshabilita el boton si falla; aqui siempre se puede reintentar.
            self.panel.boton_ejecutar.config(state="normal")

    def _cerrar_ventana(self) -> None:
        if self.editor.hay_cambios_sin_guardar():
            respuesta = dialogos.confirmar_o_cancelar(
                self, "Hay archivos con cambios sin guardar.\n¿Guardarlos antes de salir?",
                si="Guardar", no="Salir sin guardar",
            )
            if respuesta is None:
                return
            if respuesta and not self.editor.guardar_todos():
                return
        self.destroy()


def main(argumentos: list[str] | None = None) -> None:
    argumentos = sys.argv[1:] if argumentos is None else argumentos
    carpeta = argumentos[0] if argumentos else None
    VentanaPrincipal(carpeta).mainloop()


if __name__ == "__main__":
    main()
