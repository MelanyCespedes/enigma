from __future__ import annotations

import json
import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, ttk

from gui import dialogos, recursos, tema
from gui.botones import BotonIcono, Tooltip

EXTENSION = ".eng"
ARCHIVO_PROYECTO = ".enigma_proyecto.json"
CARPETAS_IGNORADAS = {"__pycache__", "venv", "env", "node_modules"}
CARACTERES_INVALIDOS = re.compile(r'[<>:"/\\|?*]')


def ruta_proyecto_predeterminada() -> str:
    documentos = os.path.join(os.path.expanduser("~"), "Documents")
    onedrive_documentos = os.path.join(os.path.expanduser("~"), "OneDrive", "Documents")
    if os.path.isdir(onedrive_documentos):
        documentos = onedrive_documentos
    destino = os.path.join(documentos, "Enigma") if os.path.isdir(documentos) else os.path.join(os.path.expanduser("~"), "Enigma")
    return os.path.abspath(destino)

ARCHIVO = "archivo"
CARPETA = "carpeta"

FAMILIA = "Segoe UI"
ALTO_FILA = 30
SANGRIA = 16


class _Fila(tk.Frame):
    """Una fila del arbol: borde, sangria, chevron, icono y nombre."""

    def __init__(self, master, arbol, ruta: str, tipo: str, nivel: int, texto: str, abierta: bool,
                 raiz: bool, principal: bool, seleccionada: bool):
        super().__init__(master, bg=tema.FONDO, height=ALTO_FILA)
        self.pack_propagate(False)
        self.ruta = ruta
        self.tipo = tipo
        self._seleccionada = seleccionada

        interior = tk.Frame(self, bg=tema.FONDO)
        interior.pack(fill="both", expand=True, padx=(12, 12), pady=1)
        self._interior = interior

        self._borde = tk.Frame(interior, width=3, bg=tema.ACENTO if seleccionada else tema.FONDO)
        self._borde.pack(side="left", fill="y")
        tk.Frame(interior, width=8 + nivel * SANGRIA, bg=tema.FONDO).pack(side="left")
        self._relleno = interior.winfo_children()[-1]

        if tipo == CARPETA:
            chevron = recursos.icono("chevron_abajo" if abierta else "chevron_der", master=self)
            icono = recursos.icono("carpeta_abierta" if (abierta and raiz) else "carpeta", master=self)
        else:
            chevron = recursos.icono("chevron_der", master=self)
            icono = recursos.icono("archivo_codigo", master=self)
        if tipo == ARCHIVO:
            chevron = recursos.icono("vacio", master=self)  # hueco del chevron: alinea con las carpetas
        self._chevron = tk.Label(interior, image=chevron, bg=tema.FONDO)
        self._chevron.pack(side="left")
        self._icono = tk.Label(interior, image=icono, bg=tema.FONDO)
        self._icono.pack(side="left", padx=(4, 8))

        if raiz:
            fuente, color = (FAMILIA, 10, "bold"), tema.TEXTO_FUERTE
        elif tipo == CARPETA:
            fuente, color = (FAMILIA, 10), tema.TEXTO if abierta else tema.TEXTO_APAGADO
        else:
            fuente, color = (FAMILIA, 10), tema.TEXTO_FUERTE if seleccionada else tema.TEXTO
        self._nombre = tk.Label(interior, text=texto, bg=tema.FONDO, fg=color, font=fuente, anchor="w")
        self._nombre.pack(side="left", fill="x", expand=True)

        self._etiqueta = None
        if principal:
            self._etiqueta = tk.Label(interior, text="★", bg=tema.FONDO, fg=tema.ACENTO, font=(FAMILIA, 9), padx=4)
            self._etiqueta.pack(side="right")
            Tooltip(self._etiqueta, "Archivo principal")

        for widget in (self, interior, self._borde, self._relleno, self._chevron, self._icono, self._nombre, self._etiqueta):
            if widget is None:
                continue
            widget.bind("<Button-1>", lambda e: arbol._al_hacer_clic(self.ruta, self.tipo))
            widget.bind("<Button-3>", lambda e: arbol._abrir_menu_contextual(e, self.ruta, self.tipo))
            widget.bind("<Enter>", lambda e: self._pintar(sobre=True))
            widget.bind("<Leave>", lambda e: self._pintar(sobre=False))
            widget.bind("<MouseWheel>", arbol._rueda)

        self._pintar(sobre=False)

    def _pintar(self, sobre: bool) -> None:
        fondo = tema.SELECCION if self._seleccionada else (tema.SELECCION_SUAVE if sobre else tema.FONDO)
        for widget in (self, self._interior, self._relleno, self._chevron, self._icono, self._nombre, self._etiqueta):
            if widget is not None:
                widget.config(bg=fondo)
        self._borde.config(bg=tema.ACENTO if self._seleccionada else fondo)
        if self._etiqueta is not None:
            self._etiqueta.config(bg=fondo)


class ArbolArchivos(tk.Frame):
    """Arbol del proyecto con subcarpetas.

    Callbacks opcionales:
      on_abrir_archivo(ruta)             al abrir un archivo
      on_renombrado(ruta_vieja, nueva)   tras renombrar un archivo
      on_eliminado(ruta)                 tras eliminar un archivo
      on_proyecto_cargado(directorio)    al abrir una carpeta de proyecto
    """

    def __init__(
        self, master, on_abrir_archivo=None, on_renombrado=None, on_eliminado=None,
        on_proyecto_cargado=None, **kwargs,
    ):
        super().__init__(master, bg=tema.FONDO, **kwargs)
        self.on_abrir_archivo = on_abrir_archivo
        self.on_renombrado = on_renombrado
        self.on_eliminado = on_eliminado
        self.on_proyecto_cargado = on_proyecto_cargado

        self.directorio_proyecto: str | None = None
        self.proyectos_abiertos: list[str] = []
        # Ruta relativa al proyecto, con '/', ej. "src/caso.eng" (o "principal.eng")
        self.archivo_principal: str | None = None
        self.archivo_activo: str | None = None  # ruta absoluta
        self._seleccion: tuple[str, str] | None = None  # (ruta, tipo)
        self._abiertas: set[str] = set()  # carpetas desplegadas (rutas absolutas)

        self._construir_widgets()

    # ---------- construccion ----------

    def _construir_widgets(self) -> None:
        encabezado = tk.Frame(self, bg=tema.FONDO)
        encabezado.pack(side="top", fill="x", padx=(16, 8), pady=(16, 8))
        tk.Label(
            encabezado, text="ARCHIVOS DEL CASO", bg=tema.FONDO, fg=tema.TEXTO_SUAVE,
            font=(FAMILIA, 8, "bold"),
        ).pack(side="left")
        self._boton_mas = BotonIcono(
            encabezado, recursos.icono("mas", master=self), self._mostrar_menu_nuevo, ayuda="Nuevo…"
        )
        self._boton_mas.pack(side="right")

        zona = tk.Frame(self, bg=tema.FONDO)
        zona.pack(side="top", fill="both", expand=True)
        self._lienzo = tk.Canvas(zona, bg=tema.FONDO, highlightthickness=0, borderwidth=0, width=1)
        self._barra = ttk.Scrollbar(zona, orient="vertical", command=self._lienzo.yview)
        self._lienzo.configure(yscrollcommand=self._barra.set)
        self._lienzo.pack(side="left", fill="both", expand=True)
        self._filas = tk.Frame(self._lienzo, bg=tema.FONDO)
        self._ventana = self._lienzo.create_window((0, 0), window=self._filas, anchor="nw")
        self._lienzo.bind("<Configure>", self._ajustar)
        self._filas.bind("<Configure>", self._ajustar)
        self._lienzo.bind("<MouseWheel>", self._rueda)
        self._lienzo.bind("<Button-3>", lambda e: self._abrir_menu_contextual(e, self.directorio_proyecto, CARPETA))

        self.menu = tk.Menu(self, tearoff=0)
        self._dibujar_vacio()

    def _ajustar(self, _evento=None) -> None:
        self._lienzo.itemconfigure(self._ventana, width=self._lienzo.winfo_width())
        self._lienzo.configure(scrollregion=self._lienzo.bbox("all") or (0, 0, 0, 0))
        if self._filas.winfo_reqheight() > self._lienzo.winfo_height():
            self._barra.pack(side="right", fill="y")
        else:
            self._barra.pack_forget()
            self._lienzo.yview_moveto(0)

    def _rueda(self, evento) -> None:
        if self._filas.winfo_reqheight() > self._lienzo.winfo_height():
            self._lienzo.yview_scroll(-1 if evento.delta > 0 else 1, "units")

    def _dibujar_vacio(self) -> None:
        for hijo in self._filas.winfo_children():
            hijo.destroy()
        tk.Label(
            self._filas, text="Abre una carpeta para\nver los archivos del caso.", bg=tema.FONDO,
            fg=tema.TEXTO_APAGADO, font=(FAMILIA, 9), justify="left",
        ).pack(anchor="w", padx=18, pady=(6, 10))
        from gui.botones import BotonPlano
        BotonPlano(self._filas, "Abrir carpeta…", self._elegir_carpeta, color=tema.ACENTO).pack(anchor="w", padx=8)

    def _mostrar_menu_nuevo(self) -> None:
        self.menu.delete(0, "end")
        self.menu.add_command(label="Nuevo archivo", command=self.nuevo_archivo)
        self.menu.add_command(label="Nueva carpeta", command=self.nueva_carpeta)
        self.menu.add_separator()
        self.menu.add_command(label="Abrir carpeta…", command=self._elegir_carpeta)
        x = self._boton_mas.winfo_rootx()
        y = self._boton_mas.winfo_rooty() + self._boton_mas.winfo_height()
        self.menu.tk_popup(x, y)

    # ---------- proyecto ----------

    def cargar_proyecto(self, ruta_carpeta: str) -> None:
        ruta_carpeta = os.path.abspath(ruta_carpeta)
        if ruta_carpeta not in self.proyectos_abiertos:
            self.proyectos_abiertos.append(ruta_carpeta)
        self.directorio_proyecto = ruta_carpeta
        self._abiertas.add(ruta_carpeta)
        self._seleccion = None
        self.archivo_activo = None
        self._cargar_configuracion_proyecto()
        self._refrescar_arbol()
        if self.on_proyecto_cargado:
            self.on_proyecto_cargado(ruta_carpeta)

    def _elegir_carpeta(self) -> None:
        ruta = filedialog.askdirectory(title="Selecciona la carpeta del proyecto")
        if ruta:
            self.cargar_proyecto(ruta)

    # ---------- dibujo del arbol ----------

    def _ruta_relativa(self, ruta: str) -> str:
        proyecto = self._proyecto_de(ruta)
        return os.path.relpath(ruta, proyecto).replace(os.sep, "/") if proyecto else ruta

    def _proyecto_de(self, ruta: str) -> str | None:
        ruta = os.path.abspath(ruta)
        coincidencias = [
            proyecto for proyecto in self.proyectos_abiertos
            if ruta == proyecto or ruta.startswith(proyecto + os.sep)
        ]
        return max(coincidencias, key=len, default=None)

    def _es_principal(self, ruta: str) -> bool:
        return self.archivo_principal is not None and self._ruta_relativa(ruta) == self.archivo_principal

    def _abrir_carpetas_de(self, ruta: str | None) -> None:
        """Marca como desplegadas las carpetas que contienen 'ruta'."""
        if not ruta or not self.directorio_proyecto:
            return
        carpeta = os.path.dirname(ruta)
        raiz = os.path.abspath(self.directorio_proyecto)
        while os.path.abspath(carpeta).startswith(raiz) and os.path.abspath(carpeta) != raiz:
            self._abiertas.add(carpeta)
            carpeta = os.path.dirname(carpeta)

    def _refrescar_arbol(self, seleccionar: tuple[str, str] | None = None) -> None:
        if seleccionar is not None:
            self._seleccion = seleccionar
        for hijo in self._filas.winfo_children():
            hijo.destroy()
        if not self.proyectos_abiertos:
            self._dibujar_vacio()
            return

        for raiz in self.proyectos_abiertos:
            nombre = os.path.basename(raiz.rstrip("/\\")) or raiz
            self._agregar_fila(raiz, CARPETA, 0, nombre, raiz=True)
            if raiz in self._abiertas:
                self._insertar_contenido(raiz, 1)
        self.update_idletasks()
        self._ajustar()

    def _agregar_fila(self, ruta: str, tipo: str, nivel: int, texto: str, raiz: bool = False) -> None:
        if tipo == CARPETA:
            seleccionada = False
            principal = False
            abierta = ruta in self._abiertas
        else:
            seleccionada = ruta == self.archivo_activo or self._seleccion == (ruta, tipo)
            principal = self._es_principal(ruta)
            abierta = False
        fila = _Fila(self._filas, self, ruta, tipo, nivel, texto, abierta, raiz, principal, seleccionada)
        fila.pack(side="top", fill="x")

    def _insertar_contenido(self, carpeta: str, nivel: int) -> None:
        try:
            entradas = sorted(os.listdir(carpeta), key=str.lower)
        except OSError:
            return

        carpetas, archivos = [], []
        for nombre in entradas:
            ruta = os.path.join(carpeta, nombre)
            if nombre.startswith(".") or nombre in CARPETAS_IGNORADAS:
                continue
            if os.path.isdir(ruta):
                carpetas.append((nombre, ruta))
            elif nombre.endswith(EXTENSION):
                archivos.append((nombre, ruta))

        for nombre, ruta in carpetas:
            self._agregar_fila(ruta, CARPETA, nivel, nombre)
            if ruta in self._abiertas:
                self._insertar_contenido(ruta, nivel + 1)
        for nombre, ruta in archivos:
            self._agregar_fila(ruta, ARCHIVO, nivel, nombre)

    # ---------- configuracion del proyecto ----------

    def _ruta_configuracion(self) -> str:
        return os.path.join(self.directorio_proyecto, ARCHIVO_PROYECTO)

    def _cargar_configuracion_proyecto(self) -> None:
        self.archivo_principal = None
        ruta_config = self._ruta_configuracion()
        if os.path.isfile(ruta_config):
            try:
                with open(ruta_config, encoding="utf-8") as f:
                    datos = json.load(f)
                principal = datos.get("principal")
                self.archivo_principal = principal.replace("\\", "/") if principal else None
            except (OSError, json.JSONDecodeError, AttributeError):
                self.archivo_principal = None

    def _guardar_configuracion_proyecto(self) -> None:
        if not self.directorio_proyecto:
            return
        with open(self._ruta_configuracion(), "w", encoding="utf-8") as f:
            json.dump({"principal": self.archivo_principal}, f, ensure_ascii=False, indent=2)

    # ---------- seleccion ----------

    def _al_hacer_clic(self, ruta: str, tipo: str) -> None:
        if tipo == CARPETA:
            proyecto = self._proyecto_de(ruta)
            if proyecto and proyecto != self.directorio_proyecto:
                self.cargar_proyecto(proyecto)
                if ruta == proyecto:
                    self._abiertas.add(ruta)
                    return
            if ruta in self._abiertas:
                self._abiertas.discard(ruta)
            else:
                self._abiertas.add(ruta)
            self._seleccion = (ruta, tipo)
            self._refrescar_arbol()
        else:
            proyecto = self._proyecto_de(ruta)
            if proyecto and proyecto != self.directorio_proyecto:
                self.cargar_proyecto(proyecto)
            self._seleccion = (ruta, tipo)
            self.establecer_archivo_activo(ruta)
            if self.on_abrir_archivo:
                self.on_abrir_archivo(ruta)

    def _archivo_seleccionado(self) -> str | None:
        return self._seleccion[0] if self._seleccion and self._seleccion[1] == ARCHIVO else None

    def _carpeta_seleccionada(self) -> str | None:
        return self._seleccion[0] if self._seleccion and self._seleccion[1] == CARPETA else None

    def _carpeta_destino(self) -> str:
        """Carpeta donde crear algo nuevo: la seleccionada, la del archivo
        seleccionado o, si no hay seleccion, la raiz del proyecto."""
        if self._seleccion is None:
            return self.directorio_proyecto
        ruta, tipo = self._seleccion
        return ruta if tipo == CARPETA else os.path.dirname(ruta)

    def establecer_archivo_activo(self, ruta: str | None) -> None:
        """Marca (y resalta) el archivo que esta activo en el editor."""
        self.archivo_activo = ruta
        if ruta is not None:
            self._seleccion = (ruta, ARCHIVO)
            self._abrir_carpetas_de(ruta)
        self._refrescar_arbol()

    # ---------- crear ----------

    def _crear_proyecto_predeterminado(self) -> bool:
        nombre = dialogos.preguntar_texto(
            self,
            "Nuevo proyecto",
            "Nombre de la carpeta principal del proyecto:",
        )
        if nombre is None:
            return False

        nombre = nombre.strip()
        if not nombre or not self._nombre_valido(nombre, "una carpeta de proyecto"):
            return False

        return self._crear_proyecto_nuevo(nombre, self._elegir_ubicacion_proyecto())

    def _elegir_ubicacion_proyecto(self) -> str | None:
        carpeta_base = ruta_proyecto_predeterminada()
        os.makedirs(carpeta_base, exist_ok=True)
        return filedialog.askdirectory(
            parent=self.winfo_toplevel(),
            title="Elegir ubicación para la carpeta principal del proyecto",
            initialdir=carpeta_base,
        )

    def _crear_proyecto_nuevo(self, nombre: str, carpeta_base: str | None = None) -> bool:
        if carpeta_base is None:
            return False
        carpeta = os.path.join(carpeta_base, nombre)
        try:
            if os.path.exists(carpeta):
                dialogos.mostrar_error(
                    self,
                    f"Ya existe una carpeta llamada '{nombre}' en la ubicación predeterminada.",
                )
                return False
            os.makedirs(carpeta, exist_ok=True)
            self.cargar_proyecto(carpeta)
            return True
        except OSError as error:
            dialogos.mostrar_error(
                self,
                f"No se pudo crear el proyecto:\n{error}",
            )
            return False

    def _nombre_valido(self, nombre: str, que: str) -> bool:
        if CARACTERES_INVALIDOS.search(nombre) or nombre in (".", ".."):
            dialogos.mostrar_error(
                self, f"El nombre de {que} no puede contener / \\ : * ? \" < > |"
            )
            return False
        return True

    def nuevo_archivo(self, carpeta: str | None = None) -> None:
        if not self.directorio_proyecto:
            if not self._crear_proyecto_predeterminado():
                return

        destino = carpeta or self._carpeta_destino()
        ubicacion = self._ruta_relativa(destino) if destino != self.directorio_proyecto else ""
        mensaje = "Nombre del archivo (sin extensión):"
        if ubicacion:
            mensaje = f"Se creará en '{ubicacion}/'.\n{mensaje}"

        nombre = dialogos.preguntar_texto(self, "Nuevo archivo", mensaje)
        if not nombre:
            return
        nombre = nombre.strip()
        if not nombre or not self._nombre_valido(nombre, "un archivo"):
            return
        if not nombre.endswith(EXTENSION):
            nombre += EXTENSION

        ruta = os.path.join(destino, nombre)
        if os.path.exists(ruta):
            dialogos.mostrar_error(self, f"Ya existe un archivo llamado '{nombre}'.")
            return

        with open(ruta, "w", encoding="utf-8") as f:
            f.write("")

        self._abiertas.add(destino)
        self.establecer_archivo_activo(ruta)
        if self.on_abrir_archivo:
            self.on_abrir_archivo(ruta)

    def crear_archivo_desde_guia(self, codigo: str, nombre: str) -> str | None:
        """Crea y abre automaticamente un archivo con contenido generado por la Guia."""
        nombre_predeterminado = re.sub(r"[^\w\-]+", "_", nombre, flags=re.UNICODE).strip("_").lower()
        nombre_predeterminado = nombre_predeterminado or "caso_practica"
        nombre_proyecto = dialogos.preguntar_texto(
            self,
            "Nuevo proyecto de práctica",
            "Escribe el nombre de la carpeta principal para este caso:",
            valor_inicial=nombre_predeterminado,
        )
        if nombre_proyecto is None:
            return None
        nombre_proyecto = nombre_proyecto.strip()
        if not nombre_proyecto or not self._nombre_valido(nombre_proyecto, "una carpeta de proyecto"):
            return None
        ubicacion = self._elegir_ubicacion_proyecto()
        if ubicacion is None:
            return None
        if not self._crear_proyecto_nuevo(nombre_proyecto, ubicacion):
            return None

        nombre_seguro = re.sub(r"[^\w\-]+", "_", nombre, flags=re.UNICODE).strip("_").lower()
        nombre_seguro = nombre_seguro or "reto_enigma"
        ruta_base = os.path.join(self.directorio_proyecto, nombre_seguro)
        ruta = ruta_base + EXTENSION
        contador = 2
        while os.path.exists(ruta):
            ruta = f"{ruta_base}_{contador}{EXTENSION}"
            contador += 1

        try:
            with open(ruta, "w", encoding="utf-8") as archivo:
                archivo.write(codigo)
        except OSError as error:
            dialogos.mostrar_error(self, f"No se pudo crear el archivo:\n{error}")
            return None

        self._abiertas.add(self.directorio_proyecto)
        self._refrescar_arbol(seleccionar=(ruta, ARCHIVO))
        if self.on_abrir_archivo:
            self.on_abrir_archivo(ruta)
        self.establecer_archivo_activo(ruta)
        return ruta

    def nueva_carpeta(self, carpeta: str | None = None) -> None:
        if not self.directorio_proyecto:
            if not self._crear_proyecto_predeterminado():
                return

        destino = carpeta or self._carpeta_destino()
        nombre = dialogos.preguntar_texto(self, "Nueva carpeta", "Nombre de la carpeta:")
        if not nombre:
            return
        nombre = nombre.strip()
        if not nombre or not self._nombre_valido(nombre, "una carpeta"):
            return

        ruta = os.path.join(destino, nombre)
        if os.path.exists(ruta):
            dialogos.mostrar_error(self, f"Ya existe '{nombre}' en esa ubicación.")
            return

        os.mkdir(ruta)
        self._abiertas.add(destino)
        self._refrescar_arbol(seleccionar=(ruta, CARPETA))

    def _renombrar_carpeta_seleccionada(self) -> None:
        ruta = self._carpeta_seleccionada()
        if not ruta or ruta in self.proyectos_abiertos:
            return

        nombre = dialogos.preguntar_texto(
            self, "Renombrar carpeta", "Nuevo nombre:",
            valor_inicial=os.path.basename(ruta),
        )
        if not nombre:
            return
        nombre = nombre.strip()
        if not nombre or not self._nombre_valido(nombre, "una carpeta"):
            return

        nueva_ruta = os.path.join(os.path.dirname(ruta), nombre)
        if os.path.exists(nueva_ruta):
            dialogos.mostrar_error(self, f"Ya existe una carpeta llamada '{nombre}'.")
            return

        os.rename(ruta, nueva_ruta)
        self._abiertas = {
            nueva_ruta + carpeta[len(ruta):] if carpeta == ruta or carpeta.startswith(ruta + os.sep) else carpeta
            for carpeta in self._abiertas
        }
        if self.archivo_principal:
            principal = os.path.normpath(os.path.join(self.directorio_proyecto, self.archivo_principal))
            if principal.startswith(ruta + os.sep):
                nuevo_principal = nueva_ruta + principal[len(ruta):]
                self.archivo_principal = os.path.relpath(nuevo_principal, self.directorio_proyecto).replace(os.sep, "/")
                self._guardar_configuracion_proyecto()

        self._seleccion = None
        self._refrescar_arbol(seleccionar=(nueva_ruta, CARPETA))

    def _eliminar_carpeta_seleccionada(self) -> None:
        ruta = self._carpeta_seleccionada()
        if not ruta or ruta in self.proyectos_abiertos:
            return

        nombre = os.path.basename(ruta)
        if not dialogos.confirmar(
            self,
            f"¿Eliminar la carpeta '{nombre}' y todo su contenido? Esta acción no se puede deshacer.",
            si="Eliminar", no="Cancelar",
        ):
            return

        archivos = []
        for raiz, _, nombres in os.walk(ruta):
            archivos.extend(os.path.join(raiz, archivo) for archivo in nombres)
        shutil.rmtree(ruta)

        if self.archivo_principal:
            principal = os.path.normpath(os.path.join(self.directorio_proyecto, self.archivo_principal))
            if principal.startswith(ruta + os.sep):
                self.archivo_principal = None
                self._guardar_configuracion_proyecto()

        self._seleccion = None
        self._abiertas = {carpeta for carpeta in self._abiertas if carpeta != ruta and not carpeta.startswith(ruta + os.sep)}
        self._refrescar_arbol()
        if self.on_eliminado:
            for archivo in archivos:
                self.on_eliminado(archivo)

    # ---------- renombrar / eliminar / principal ----------

    def _renombrar_seleccionado(self) -> None:
        ruta = self._archivo_seleccionado()
        if not ruta:
            return

        nombre_actual = os.path.basename(ruta)
        nuevo_nombre = dialogos.preguntar_texto(
            self, "Renombrar archivo", "Nuevo nombre:", valor_inicial=nombre_actual
        )
        if not nuevo_nombre:
            return
        nuevo_nombre = nuevo_nombre.strip()
        if not nuevo_nombre or not self._nombre_valido(nuevo_nombre, "un archivo"):
            return
        if not nuevo_nombre.endswith(EXTENSION):
            nuevo_nombre += EXTENSION
        if nuevo_nombre == nombre_actual:
            return

        nueva_ruta = os.path.join(os.path.dirname(ruta), nuevo_nombre)
        if os.path.exists(nueva_ruta):
            dialogos.mostrar_error(self, f"Ya existe un archivo llamado '{nuevo_nombre}'.")
            return

        era_principal = self._es_principal(ruta)
        os.rename(ruta, nueva_ruta)

        if era_principal:
            self.archivo_principal = self._ruta_relativa(nueva_ruta)
            self._guardar_configuracion_proyecto()
        if self.archivo_activo == ruta:
            self.archivo_activo = nueva_ruta

        self._refrescar_arbol(seleccionar=(nueva_ruta, ARCHIVO))
        if self.on_renombrado:
            self.on_renombrado(ruta, nueva_ruta)

    def _eliminar_seleccionado(self) -> None:
        ruta = self._archivo_seleccionado()
        if not ruta:
            return

        nombre = os.path.basename(ruta)
        if not dialogos.confirmar(
            self, f"¿Eliminar '{nombre}'? Esta acción no se puede deshacer.",
            si="Eliminar", no="Cancelar",
        ):
            return

        era_principal = self._es_principal(ruta)
        os.remove(ruta)

        if era_principal:
            self.archivo_principal = None
            self._guardar_configuracion_proyecto()
        if self.archivo_activo == ruta:
            self.archivo_activo = None
        self._seleccion = None

        self._refrescar_arbol()
        if self.on_eliminado:
            self.on_eliminado(ruta)

    def _marcar_principal(self) -> None:
        ruta = self._archivo_seleccionado()
        if not ruta:
            return
        self.archivo_principal = self._ruta_relativa(ruta)
        self._guardar_configuracion_proyecto()
        self._refrescar_arbol()

    # ---------- menu contextual ----------

    def _abrir_menu_contextual(self, evento, ruta: str | None, tipo: str) -> None:
        if not self.directorio_proyecto or ruta is None:
            return
        self._seleccion = (ruta, tipo)

        self.menu.delete(0, "end")
        if tipo == ARCHIVO:
            self.menu.add_command(label="Abrir", command=lambda: self._al_hacer_clic(ruta, ARCHIVO))
            self.menu.add_command(label="Renombrar", command=self._renombrar_seleccionado)
            self.menu.add_command(label="Eliminar", command=self._eliminar_seleccionado)
            self.menu.add_separator()
            self.menu.add_command(label="Marcar como archivo principal", command=self._marcar_principal)
        else:
            self.menu.add_command(label="Nuevo archivo aquí", command=self.nuevo_archivo)
            self.menu.add_command(label="Nueva carpeta aquí", command=self.nueva_carpeta)
            self.menu.add_separator()
            self.menu.add_command(label="Renombrar", command=self._renombrar_carpeta_seleccionada)
            self.menu.add_command(label="Eliminar carpeta", command=self._eliminar_carpeta_seleccionada)
        self.menu.tk_popup(evento.x_root, evento.y_root)

    # ---------- consultas ----------

    def obtener_archivo_principal(self) -> str | None:
        """Ruta absoluta del archivo principal, o None si no se ha marcado ninguno."""
        if not self.archivo_principal or not self.directorio_proyecto:
            return None
        return os.path.normpath(os.path.join(self.directorio_proyecto, self.archivo_principal))

    def obtener_directorio_proyecto(self) -> str | None:
        return self.directorio_proyecto

    def obtener_archivo_activo(self) -> str | None:
        return self.archivo_activo


if __name__ == "__main__":
    from gui.tema import aplicar_tema

    raiz = tk.Tk()
    aplicar_tema(raiz)
    raiz.title("Arbol de archivos - prueba")
    raiz.geometry("300x400")
    arbol = ArbolArchivos(raiz, on_abrir_archivo=lambda ruta: print("Abrir:", ruta))
    arbol.pack(fill="both", expand=True)
    raiz.mainloop()
