from __future__ import annotations

import sys
import tkinter as tk
from tkinter import filedialog, ttk

from gui import ajustes, constructor_pistas, dialogos, recursos, tema
from gui.cabecera import Cabecera
from gui.editor_widget import EditorCodigo
from gui.file_tree import ArbolArchivos
from gui.guia_contenido import SECCIONES
from gui.herramientas import PanelHerramientas
from gui.output_panel import PanelSalida
from gui.panel_derecho import DETECTIVE, PanelDerecho
from gui.tema import CABECERA, SELECCION_SUAVE, TEXTO, aplicar_tema, oscurecer_barra_titulo

ANCHO_IZQUIERDA = 222
ANCHO_RAPIDA = 260
ANCHO_DETECTIVE = 420


class VentanaPrincipal(tk.Tk):
    """Une la cabecera, el arbol de archivos, el editor, el panel de salida y las guias."""

    def __init__(self, carpeta_inicial: str | None = None):
        super().__init__()
        self.title("Enigma - Laboratorio de razonamiento")
        self.geometry("1300x760")
        self.minsize(960, 560)

        aplicar_tema(self)
        recursos.poner_icono(self)
        self._config = ajustes.cargar()
        self._derecha_visible = True
        self._construir_widgets()
        self._construir_menu()
        self._conectar_atajos()
        self.protocol("WM_DELETE_WINDOW", self._cerrar_ventana)

        oscurecer_barra_titulo(self)
        self.after(50, self._ajustar_columnas)

        if carpeta_inicial:
            self.arbol.cargar_proyecto(carpeta_inicial)

    # ---------- construccion ----------

    def _construir_widgets(self) -> None:
        self.cabecera = Cabecera(
            self, al_campana=self._abrir_historial, al_ajustes=self._abrir_preferencias,
        )
        self.cabecera.pack(side="top", fill="x")

        horizontal = ttk.PanedWindow(self, orient="horizontal")
        horizontal.pack(side="top", fill="both", expand=True)
        self._contenedor = horizontal

        # Cada widget debe crearse como hijo del panel que lo contiene; si no,
        # queda tapado por su "hermano" y no se ve.
        izquierda = tk.Frame(horizontal, bg=tema.FONDO, width=ANCHO_IZQUIERDA, height=100)
        izquierda.pack_propagate(False)
        centro = ttk.PanedWindow(horizontal, orient="vertical")

        self.editor = EditorCodigo(
            centro,
            on_ejecutar=self.compilar_y_ejecutar,
            on_compilar=self.compilar,
            on_nuevo=lambda: self.arbol.nuevo_archivo(),
            on_estado=self._actualizar_cabecera,
            tam_fuente=ajustes.limitar_fuente(self._config.get("tam_fuente")),
        )

        self.herramientas = PanelHerramientas(
            izquierda,
            [
                ("guia", "libro", "Guía del detective", self.alternar_guia),
                ("atajos", "ayuda", "Atajos de teclado", lambda: self.mostrar_guia("atajos")),
            ],
        )
        self.herramientas.pack(side="bottom", fill="x")
        self.arbol = ArbolArchivos(
            izquierda,
            on_abrir_archivo=self.editor.abrir,
            on_renombrado=self.editor.actualizar_ruta,
            on_eliminado=self.editor.descartar,
            on_proyecto_cargado=self._proyecto_cargado,
        )
        self.arbol.pack(side="top", fill="both", expand=True)

        self.panel = PanelSalida(
            centro,
            obtener_proyecto=lambda: (
                self.arbol.obtener_archivo_principal(),
                self.arbol.obtener_directorio_proyecto(),
            ),
            guardar_archivos_abiertos=self.editor.guardar_todos,
            on_pista=lambda texto: self.derecha.rapida.mostrar_pista(texto),
            on_evento=self._evento_panel,
        )
        centro.add(self.editor, weight=4)
        centro.add(self.panel, weight=1)

        self.derecha = PanelDerecho(
            horizontal,
            al_insertar=self.editor.insertar_texto,
            al_ocultar=self.ocultar_derecha,
            al_constructor=self.abrir_constructor,
            al_cambiar_vista=self._vista_cambiada,
        )
        self.derecha.configure(width=ANCHO_RAPIDA, height=100)
        self.derecha.pack_propagate(False)

        horizontal.add(izquierda, weight=0)
        horizontal.add(centro, weight=1)
        horizontal.add(self.derecha, weight=0)

    def _construir_menu(self) -> None:
        """Menus propios (la barra nativa de Windows no se puede pintar), dentro de la cabecera."""
        barra = self.cabecera.menus

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
        editar.add_separator()
        editar.add_command(label="Preferencias…", command=self._abrir_preferencias)

        ejecutar = self._crear_menu(barra, "Ejecutar")
        ejecutar.add_command(label="Compilar", command=self.compilar)
        ejecutar.add_command(
            label="Ejecutar caso", accelerator="Ctrl+Enter", command=self.compilar_y_ejecutar
        )

        ayuda = self._crear_menu(barra, "Ayuda")
        ayuda.add_command(label="Guía rápida", command=self.mostrar_rapida)
        ayuda.add_command(label="Guía del detective", accelerator="F1", command=self.alternar_guia)
        ayuda.add_command(label="Constructor de pistas", command=self.abrir_constructor)
        ayuda.add_separator()
        for seccion in SECCIONES:
            ayuda.add_command(
                label=seccion.titulo, command=lambda s=seccion.id: self.mostrar_guia(s)
            )
        ayuda.add_separator()
        ayuda.add_command(label="Acerca de Enigma", command=self._acerca_de)

    def _crear_menu(self, barra: tk.Frame, texto: str) -> tk.Menu:
        boton = tk.Menubutton(
            barra, text=texto, bg=CABECERA, fg=TEXTO, activebackground=SELECCION_SUAVE,
            activeforeground=TEXTO, relief="flat", borderwidth=0, padx=12, pady=5,
        )
        boton.pack(side="left")
        menu = tk.Menu(boton, tearoff=0, borderwidth=1)
        boton.config(menu=menu)
        return menu

    def _conectar_atajos(self) -> None:
        self.bind("<Control-o>", lambda e: self.abrir_carpeta())
        self.bind("<Control-Return>", lambda e: self.compilar_y_ejecutar())
        self.bind("<F1>", lambda e: self.alternar_guia())

    # ---------- columnas ----------

    def _ajustar_columnas(self) -> None:
        """Fija el ancho de la columna izquierda y de la derecha (Tk las reparte al azar al inicio)."""
        total = self._contenedor.winfo_width()
        if total < 700:
            self.after(50, self._ajustar_columnas)
            return
        try:
            self._contenedor.sashpos(0, ANCHO_IZQUIERDA)
            if self._derecha_visible:
                ancho = ANCHO_DETECTIVE if self.derecha.vista == DETECTIVE else ANCHO_RAPIDA
                self._contenedor.sashpos(1, total - ancho)
        except tk.TclError:
            pass

    def _vista_cambiada(self, vista: str) -> None:
        self.herramientas.marcar("guia", vista == DETECTIVE and self._derecha_visible)
        if self._derecha_visible:
            self.after_idle(self._ajustar_columnas)

    def mostrar_derecha(self) -> None:
        if not self._derecha_visible:
            self._contenedor.add(self.derecha, weight=0)
            self._derecha_visible = True
            self.update_idletasks()
        self._ajustar_columnas()

    def ocultar_derecha(self) -> None:
        if self._derecha_visible:
            self._contenedor.forget(self.derecha)
            self._derecha_visible = False
            self.herramientas.marcar("guia", False)

    # ---------- guias ----------

    def mostrar_guia(self, seccion: str | None = None) -> None:
        """Muestra la Guia del detective (a la derecha), opcionalmente en una seccion."""
        self.mostrar_derecha()
        self.derecha.mostrar_detective(seccion)

    def mostrar_rapida(self) -> None:
        self.mostrar_derecha()
        self.derecha.mostrar_rapida()

    def alternar_guia(self) -> None:
        if self._derecha_visible and self.derecha.vista == DETECTIVE:
            self.derecha.mostrar_rapida()
        else:
            self.mostrar_guia()

    def abrir_constructor(self) -> None:
        constructor_pistas.abrir(self, self.editor.insertar_texto)

    # ---------- estado ----------

    def _proyecto_cargado(self, _ruta: str) -> None:
        self._actualizar_cabecera(self.editor.obtener_ruta_activa(), self.editor.hay_cambios_sin_guardar())
        self.panel.actualizar_proyecto()

    def _actualizar_cabecera(self, ruta_activa: str | None, modificado: bool) -> None:
        self.cabecera.actualizar(self.arbol.obtener_directorio_proyecto(), ruta_activa, modificado)
        titulo = "Enigma - Laboratorio de razonamiento"
        if ruta_activa:
            nombre = ruta_activa.replace(chr(92), "/").rsplit("/", 1)[-1]
            titulo = f"{nombre}{' ●' if modificado else ''} - Enigma"
        self.title(titulo)

    def _evento_panel(self, tipo: str) -> None:
        """Compilar o ejecutar termino: si fallo, la campana avisa."""
        if tipo == "error" and self.panel._solapa_actual != "terminal":
            self.cabecera.marcar_aviso(True)

    # ---------- ventanas auxiliares ----------

    def _abrir_historial(self) -> None:
        self.panel.mostrar_solapa("terminal")
        self.cabecera.marcar_aviso(False)

    def _abrir_preferencias(self) -> None:
        ajustes.abrir_preferencias(
            self, ajustes.limitar_fuente(self._config.get("tam_fuente")), self._aplicar_preferencias
        )

    def _aplicar_preferencias(self, tam_fuente: int) -> None:
        self._config["tam_fuente"] = tam_fuente
        ajustes.guardar(self._config)
        self.editor.cambiar_tamano_fuente(tam_fuente)

    def _acerca_de(self) -> None:
        dialogos.mostrar_info(
            self,
            "Enigma — Laboratorio de razonamiento\n\n"
            "Un lenguaje de programación temático (detectives y casos) para entrenar el "
            "razonamiento lógico y matemático.\n\n"
            "Proyecto del curso Paradigmas de Programación.\n"
            "Universidad Nacional, Sede Regional Brunca.",
            titulo="Acerca de Enigma",
        )

    # ---------- acciones ----------

    def abrir_carpeta(self) -> None:
        ruta = filedialog.askdirectory(title="Selecciona la carpeta del proyecto")
        if ruta:
            self.arbol.cargar_proyecto(ruta)

    def compilar(self) -> bool:
        return self.panel.compilar()

    def compilar_y_ejecutar(self) -> None:
        if self.panel.esta_ocupado():
            return
        if self.panel.compilar():
            self.panel.ejecutar_programa()

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
