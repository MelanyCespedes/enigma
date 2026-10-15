from __future__ import annotations

import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

EXTENSION = ".eng"
ARCHIVO_PROYECTO = ".enigma_proyecto.json"


class ArbolArchivos(ttk.Frame):

    def __init__(self, master, on_abrir_archivo=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_abrir_archivo = on_abrir_archivo  # callback(ruta_absoluta)

        self.directorio_proyecto: str | None = None
        self.archivo_principal: str | None = None  # nombre, ej. "principal.eng"
        self.archivo_activo: str | None = None  # ruta absoluta

        self._construir_widgets()


    def _construir_widgets(self) -> None:
        barra = ttk.Frame(self)
        barra.pack(fill="x")

        ttk.Button(barra, text="Abrir carpeta...", command=self._elegir_carpeta).pack(
            side="left", padx=2, pady=2
        )
        ttk.Button(barra, text="Nuevo archivo", command=self._nuevo_archivo).pack(
            side="left", padx=2, pady=2
        )

        self.arbol = ttk.Treeview(self, show="tree", selectmode="browse")
        self.arbol.pack(fill="both", expand=True)
        self.arbol.tag_configure("principal", font=("TkDefaultFont", 9, "bold"))
        self.arbol.tag_configure("activo", background="#d8ebff")

        self.arbol.bind("<Double-1>", self._al_hacer_doble_clic)
        self.arbol.bind("<Button-3>", self._abrir_menu_contextual)  # click derecho Win/Linux
        self.arbol.bind("<Button-2>", self._abrir_menu_contextual)  # click derecho en algunos Mac

        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Abrir", command=self._abrir_seleccionado)
        self.menu.add_command(label="Renombrar", command=self._renombrar_seleccionado)
        self.menu.add_command(label="Eliminar", command=self._eliminar_seleccionado)
        self.menu.add_separator()
        self.menu.add_command(label="Marcar como archivo principal", command=self._marcar_principal)

        self.etiqueta_estado = ttk.Label(self, text="Ninguna carpeta abierta", anchor="w")
        self.etiqueta_estado.pack(fill="x")


    def cargar_proyecto(self, ruta_carpeta: str) -> None:
        self.directorio_proyecto = ruta_carpeta
        self._cargar_configuracion_proyecto()
        self._refrescar_arbol()
        nombre = os.path.basename(ruta_carpeta.rstrip(os.sep)) or ruta_carpeta
        self.etiqueta_estado.config(text=f"Proyecto: {nombre}")

    def _elegir_carpeta(self) -> None:
        ruta = filedialog.askdirectory(title="Selecciona la carpeta del proyecto")
        if ruta:
            self.cargar_proyecto(ruta)

    def _refrescar_arbol(self) -> None:
        self.arbol.delete(*self.arbol.get_children())
        if not self.directorio_proyecto:
            return

        raiz = self.arbol.insert(
            "", "end", text=os.path.basename(self.directorio_proyecto), open=True, values=("",)
        )
        self._insertar_archivos(raiz, self.directorio_proyecto)

    def _insertar_archivos(self, nodo_padre: str, carpeta: str) -> None:
        try:
            entradas = sorted(os.listdir(carpeta))
        except OSError:
            return

        for nombre in entradas:
            ruta = os.path.join(carpeta, nombre)
            if nombre.startswith(".") or os.path.isdir(ruta):
                continue
            if not nombre.endswith(EXTENSION):
                continue

            etiquetas = []
            if nombre == self.archivo_principal:
                etiquetas.append("principal")
            if ruta == self.archivo_activo:
                etiquetas.append("activo")

            texto = nombre + ("  (principal)" if nombre == self.archivo_principal else "")
            self.arbol.insert(nodo_padre, "end", text=texto, values=(ruta,), tags=tuple(etiquetas))


    def _ruta_configuracion(self) -> str:
        return os.path.join(self.directorio_proyecto, ARCHIVO_PROYECTO)

    def _cargar_configuracion_proyecto(self) -> None:
        self.archivo_principal = None
        ruta_config = self._ruta_configuracion()
        if os.path.isfile(ruta_config):
            try:
                with open(ruta_config, encoding="utf-8") as f:
                    datos = json.load(f)
                self.archivo_principal = datos.get("principal")
            except (OSError, json.JSONDecodeError):
                self.archivo_principal = None

    def _guardar_configuracion_proyecto(self) -> None:
        if not self.directorio_proyecto:
            return
        with open(self._ruta_configuracion(), "w", encoding="utf-8") as f:
            json.dump({"principal": self.archivo_principal}, f, ensure_ascii=False, indent=2)

  
    def _nodo_seleccionado(self):
        seleccion = self.arbol.selection()
        if not seleccion:
            return None
        valores = self.arbol.item(seleccion[0], "values")
        return valores[0] if valores and valores[0] else None

    def _al_hacer_doble_clic(self, _evento) -> None:
        self._abrir_seleccionado()

    def _abrir_seleccionado(self) -> None:
        ruta = self._nodo_seleccionado()
        if ruta:
            self.establecer_archivo_activo(ruta)
            if self.on_abrir_archivo:
                self.on_abrir_archivo(ruta)

    def establecer_archivo_activo(self, ruta: str) -> None:
        self.archivo_activo = ruta
        self._refrescar_arbol()

    def _nuevo_archivo(self) -> None:
        if not self.directorio_proyecto:
            messagebox.showwarning("Enigma", "Primero abre una carpeta de proyecto.")
            return

        nombre = simpledialog.askstring("Nuevo archivo", "Nombre del archivo (sin extension):")
        if not nombre:
            return
        if not nombre.endswith(EXTENSION):
            nombre += EXTENSION

        ruta = os.path.join(self.directorio_proyecto, nombre)
        if os.path.exists(ruta):
            messagebox.showerror("Enigma", f"Ya existe un archivo llamado '{nombre}'.")
            return

        with open(ruta, "w", encoding="utf-8") as f:
            f.write("")

        self._refrescar_arbol()
        self.establecer_archivo_activo(ruta)
        if self.on_abrir_archivo:
            self.on_abrir_archivo(ruta)

    def _renombrar_seleccionado(self) -> None:
        ruta = self._nodo_seleccionado()
        if not ruta:
            return

        nombre_actual = os.path.basename(ruta)
        nuevo_nombre = simpledialog.askstring(
            "Renombrar archivo", "Nuevo nombre:", initialvalue=nombre_actual
        )
        if not nuevo_nombre or nuevo_nombre == nombre_actual:
            return
        if not nuevo_nombre.endswith(EXTENSION):
            nuevo_nombre += EXTENSION

        nueva_ruta = os.path.join(self.directorio_proyecto, nuevo_nombre)
        if os.path.exists(nueva_ruta):
            messagebox.showerror("Enigma", f"Ya existe un archivo llamado '{nuevo_nombre}'.")
            return

        os.rename(ruta, nueva_ruta)

        if self.archivo_principal == nombre_actual:
            self.archivo_principal = nuevo_nombre
            self._guardar_configuracion_proyecto()

        if self.archivo_activo == ruta:
            self.archivo_activo = nueva_ruta

        self._refrescar_arbol()

    def _eliminar_seleccionado(self) -> None:
        ruta = self._nodo_seleccionado()
        if not ruta:
            return

        nombre = os.path.basename(ruta)
        if not messagebox.askyesno("Enigma", f"¿Eliminar '{nombre}'? Esta accion no se puede deshacer."):
            return

        os.remove(ruta)

        if self.archivo_principal == nombre:
            self.archivo_principal = None
            self._guardar_configuracion_proyecto()
        if self.archivo_activo == ruta:
            self.archivo_activo = None

        self._refrescar_arbol()

    def _marcar_principal(self) -> None:
        ruta = self._nodo_seleccionado()
        if not ruta:
            return
        self.archivo_principal = os.path.basename(ruta)
        self._guardar_configuracion_proyecto()
        self._refrescar_arbol()

    def _abrir_menu_contextual(self, evento) -> None:
        fila = self.arbol.identify_row(evento.y)
        if fila:
            self.arbol.selection_set(fila)
            self.menu.tk_popup(evento.x_root, evento.y_root)


    def obtener_archivo_principal(self) -> str | None:
        """Ruta absoluta del archivo principal, o None si no se ha marcado ninguno."""
        if not self.archivo_principal or not self.directorio_proyecto:
            return None
        return os.path.join(self.directorio_proyecto, self.archivo_principal)

    def obtener_directorio_proyecto(self) -> str | None:
        return self.directorio_proyecto

    def obtener_archivo_activo(self) -> str | None:
        return self.archivo_activo


if __name__ == "__main__":
    raiz = tk.Tk()
    raiz.title("Arbol de archivos - prueba")
    raiz.geometry("300x400")
    arbol = ArbolArchivos(raiz, on_abrir_archivo=lambda ruta: print("Abrir:", ruta))
    arbol.pack(fill="both", expand=True)
    raiz.mainloop()