from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk

from gui import dialogos, tema
from gui.barra_busqueda import BarraBusqueda
from gui.barra_pestanas import BarraPestanas
from gui.pestana_editor import PestanaEditor


class EditorCodigo(ttk.Frame):

    def __init__(self, master, on_ejecutar=None, on_compilar=None, on_nuevo=None, on_estado=None, tam_fuente: int = 11, **kwargs):
        super().__init__(master, **kwargs)
        self.on_ejecutar = on_ejecutar
        self.on_compilar = on_compilar
        self._tam_fuente = tam_fuente
        self.on_estado = on_estado  # callback(ruta_activa | None, modificada)
        self._pestanas: dict[str, PestanaEditor] = {}  # ruta absoluta -> pestaña
        self._activa: str | None = None

        self.barra = BarraPestanas(self, self._seleccionar, self.cerrar, al_nuevo=on_nuevo)
        self.barra.pack(side="top", fill="x")
        self.barra.agregar_accion("Ejecutar caso", self._ejecutar, icono="play", ayuda="Compilar y ejecutar (Ctrl+Enter)", destacada=True)
        self.barra.agregar_accion("Compilar", self._compilar, icono="comprobar", ayuda="Solo compilar, sin ejecutar")
        self.barra.agregar_accion("", self.guardar_activo, icono="guardar", ayuda="Guardar (Ctrl+S)")
        self.barra.agregar_accion("", self.alternar_busqueda, icono="lupa", ayuda="Buscar (Ctrl+F)")

        self.busqueda = BarraBusqueda(
            self,
            al_buscar=self._buscar,
            al_siguiente=lambda: self._mover_busqueda(1),
            al_anterior=lambda: self._mover_busqueda(-1),
            al_cerrar=self.cerrar_busqueda,
        )

        self._area = tk.Frame(self, bg=tema.EDITOR)
        self._area.pack(side="top", fill="both", expand=True)
        self._area.grid_rowconfigure(0, weight=1)
        self._area.grid_columnconfigure(0, weight=1)
        self._vacio = tk.Label(
            self._area, text="Abre un archivo desde el árbol para empezar",
            bg=tema.EDITOR, fg=tema.TEXTO_SUAVE,
        )
        self._vacio.grid(row=0, column=0, sticky="nsew")

        self.bind_all("<Control-w>", lambda e: self.cerrar())
        self.bind_all("<Control-f>", lambda e: self.mostrar_busqueda())

    # ---------- API publica ----------

    def abrir(self, ruta: str) -> bool:
        """Abre el archivo en una pestaña (o la selecciona si ya estaba abierto)."""
        ruta = os.path.abspath(ruta)
        if ruta in self._pestanas:
            self._seleccionar(ruta)
            return True

        try:
            with open(ruta, encoding="utf-8", newline="") as f:
                contenido = f.read()
        except (OSError, UnicodeDecodeError) as error:
            dialogos.mostrar_error(self, f"No se pudo abrir '{ruta}':\n{error}")
            return False

        fin_de_linea = "\r\n" if "\r\n" in contenido else "\n"
        pestana = PestanaEditor(
            self._area, ruta, self._actualizar_titulo, self.guardar_activo, self._ejecutar,
            tam_fuente=self._tam_fuente,
        )
        pestana.al_actualizar_busqueda = lambda actual, total, p=pestana: self._contador_de(p, actual, total)
        pestana.texto.bind("<Control-f>", self._atajo_buscar)
        pestana.texto.bind("<Escape>", self._atajo_escape)
        pestana.cargar(contenido.replace("\r\n", "\n"), fin_de_linea)
        pestana.grid(row=0, column=0, sticky="nsew")

        self._pestanas[ruta] = pestana
        self.barra.agregar(ruta, os.path.basename(ruta))
        self._seleccionar(ruta)
        return True

    def obtener_ruta_activa(self) -> str | None:
        return self._activa

    def guardar_activo(self) -> bool:
        pestana = self._pestana_activa()
        return self._guardar(pestana) if pestana else False

    def guardar_todos(self) -> bool:
        """Guarda todos los archivos modificados. True si todo se guardo bien."""
        return all(self._guardar(p) for p in self._pestanas.values() if p.modificado)

    def cerrar(self, ruta: str | None = None) -> bool:
        """Cierra la pestaña de 'ruta' (o la activa). Pregunta si hay cambios
        sin guardar. Devuelve False si el usuario cancelo."""
        if ruta is None:
            ruta = self._activa
        pestana = self._pestanas.get(os.path.abspath(ruta)) if ruta else None
        if pestana is None:
            return True

        if pestana.modificado:
            respuesta = dialogos.confirmar_o_cancelar(
                self,
                f"'{os.path.basename(pestana.ruta)}' tiene cambios sin guardar.\n¿Guardarlos?",
                si="Guardar", no="No guardar",
            )
            if respuesta is None:
                return False
            if respuesta and not self._guardar(pestana):
                return False

        self._quitar(pestana)
        return True

    def descartar(self, ruta: str) -> None:
        """Cierra la pestaña sin preguntar ni guardar (el archivo ya no existe)."""
        pestana = self._pestanas.get(os.path.abspath(ruta))
        if pestana is not None:
            self._quitar(pestana)

    def actualizar_ruta(self, ruta_vieja: str, ruta_nueva: str) -> None:
        """Un archivo abierto fue renombrado: la pestaña pasa a apuntar al nuevo
        nombre (con sus cambios sin guardar, si los tenia)."""
        vieja, nueva = os.path.abspath(ruta_vieja), os.path.abspath(ruta_nueva)
        pestana = self._pestanas.get(vieja)
        if pestana is None:
            return
        pestana.ruta = nueva
        self._pestanas = {(nueva if k == vieja else k): p for k, p in self._pestanas.items()}
        if self._activa == vieja:
            self._activa = nueva
        self.barra.renombrar(vieja, nueva, os.path.basename(nueva), pestana.modificado)
        self._notificar_estado()

    def insertar_texto(self, texto: str) -> bool:
        """Inserta codigo (p. ej. un ejemplo de la guia) en el cursor del archivo
        activo. Devuelve False si no hay ningun archivo abierto."""
        pestana = self._pestana_activa()
        if pestana is None:
            dialogos.mostrar_aviso(self, "Abre o crea un archivo para poder insertar el código.")
            return False
        pestana.texto.insert("insert", texto + "\n")
        pestana.texto.focus_set()
        pestana.texto.see("insert")
        return True

    def hay_cambios_sin_guardar(self) -> bool:
        return any(p.modificado for p in self._pestanas.values())

    def mostrar_busqueda(self) -> None:
        pestana = self._pestana_activa()
        if pestana is None:
            return
        if not self.busqueda.visible:
            self.busqueda.pack(side="top", fill="x", before=self._area)
        self.busqueda.mostrar(pestana.texto_seleccionado().split("\n")[0])
        self._buscar(self.busqueda.consulta())

    def alternar_busqueda(self) -> None:
        """Para el boton Buscar: abre la barra o, si ya esta abierta, la cierra."""
        if self.busqueda.visible:
            self.cerrar_busqueda()
        else:
            self.mostrar_busqueda()

    def cerrar_busqueda(self) -> None:
        if not self.busqueda.visible:
            return
        self.busqueda.ocultar()
        self.busqueda.pack_forget()
        pestana = self._pestana_activa()
        if pestana is not None:
            pestana.buscar("")
            pestana.texto.focus_set()

    # ---------- internos ----------

    def _pestana_activa(self) -> PestanaEditor | None:
        return self._pestanas.get(self._activa) if self._activa else None

    def _quitar(self, pestana: PestanaEditor) -> None:
        posicion = list(self._pestanas).index(pestana.ruta)
        del self._pestanas[pestana.ruta]
        self.barra.quitar(pestana.ruta)
        pestana.destroy()

        if pestana.ruta == self._activa:
            self._activa = None
            if self._pestanas:
                restantes = list(self._pestanas)
                self._seleccionar(restantes[min(posicion, len(restantes) - 1)])
            else:
                self._vacio.tkraise()
                self.cerrar_busqueda()
        self._notificar_estado()

    def _seleccionar(self, ruta: str) -> None:
        if ruta not in self._pestanas:
            return
        anterior = self._pestana_activa()
        if anterior is not None and anterior.ruta != ruta and self.busqueda.visible:
            anterior.buscar("")

        self._activa = ruta
        pestana = self._pestanas[ruta]
        pestana.tkraise()
        self.barra.seleccionar(ruta)
        pestana.texto.focus_set()
        if self.busqueda.visible:
            self._buscar(self.busqueda.consulta(), saltar=False)
        self._notificar_estado()

    def _guardar(self, pestana: PestanaEditor) -> bool:
        contenido = pestana.obtener_contenido().replace("\n", pestana.fin_de_linea())
        try:
            with open(pestana.ruta, "w", encoding="utf-8", newline="") as f:
                f.write(contenido)
        except OSError as error:
            dialogos.mostrar_error(self, f"No se pudo guardar '{pestana.ruta}':\n{error}")
            return False
        pestana.marcar_guardado()
        return True

    def _actualizar_titulo(self, pestana: PestanaEditor) -> None:
        self.barra.actualizar(pestana.ruta, os.path.basename(pestana.ruta), pestana.modificado)
        self._notificar_estado()

    def _notificar_estado(self) -> None:
        if self.on_estado:
            activa = self._pestana_activa()
            self.on_estado(activa.ruta if activa else None, bool(activa and activa.modificado))

    def _ejecutar(self) -> None:
        if self.on_ejecutar:
            self.on_ejecutar()

    def _compilar(self) -> None:
        if self.on_compilar:
            self.on_compilar()

    def cambiar_tamano_fuente(self, tam_fuente: int) -> None:
        """Aplica el tamaño de letra a todas las pestañas (y a las que se abran despues)."""
        self._tam_fuente = tam_fuente
        for pestana in self._pestanas.values():
            pestana.cambiar_fuente(tam_fuente)

    # ---------- busqueda ----------

    def _atajo_buscar(self, _evento) -> str:
        self.mostrar_busqueda()
        return "break"  # evita el Ctrl+F por defecto de Tk (mover el cursor)

    def _atajo_escape(self, _evento) -> str | None:
        if self.busqueda.visible:
            self.cerrar_busqueda()
            return "break"
        return None

    def _buscar(self, consulta: str, saltar: bool = True) -> None:
        pestana = self._pestana_activa()
        if pestana is None:
            return
        total = pestana.buscar(consulta)
        actual = 0
        if saltar and total:
            actual, total = pestana.mover_coincidencia(1)
        self.busqueda.poner_contador(actual, total)

    def _mover_busqueda(self, direccion: int) -> None:
        pestana = self._pestana_activa()
        if pestana is not None:
            actual, total = pestana.mover_coincidencia(direccion)
            self.busqueda.poner_contador(actual, total)

    def _contador_de(self, pestana: PestanaEditor, actual: int, total: int) -> None:
        if pestana is self._pestana_activa() and self.busqueda.visible:
            self.busqueda.poner_contador(actual, total)


if __name__ == "__main__":
    import sys

    from gui.tema import aplicar_tema

    raiz = tk.Tk()
    aplicar_tema(raiz)
    raiz.title("Editor - prueba")
    raiz.geometry("800x500")
    editor = EditorCodigo(
        raiz, on_ejecutar=lambda: print("Ejecutar pedido"), on_nuevo=lambda: print("Nuevo pedido")
    )
    editor.pack(fill="both", expand=True)
    for argumento in sys.argv[1:]:
        editor.abrir(argumento)
    raiz.mainloop()