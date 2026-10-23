"""Cabecera del IDE (como en el diseno): logo y nombre, menus, archivo activo con su
estado, y a la derecha campana y ajustes."""
from __future__ import annotations

import os
import tkinter as tk

from gui import recursos, tema
from gui.botones import BotonIcono

FUENTE = "Segoe UI"
ALTO = 66


class Cabecera(tk.Frame):
    def __init__(self, master, al_campana=None, al_ajustes=None):
        super().__init__(master, bg=tema.CABECERA, height=ALTO)
        self.pack_propagate(False)

        tk.Frame(self, height=1, bg=tema.BORDE).pack(side="bottom", fill="x")
        fila = tk.Frame(self, bg=tema.CABECERA)
        fila.pack(side="top", fill="both", expand=True)

        # Marca: logo + nombre
        marca = tk.Frame(fila, bg=tema.CABECERA)
        marca.pack(side="left", padx=(18, 14))
        self._logo = recursos.cargar_imagen(recursos.LOGO_CUBO, 7, master=self)  # ~36 px
        if self._logo is not None:
            tk.Label(marca, image=self._logo, bg=tema.CABECERA).pack(side="left", padx=(0, 12))
        textos = tk.Frame(marca, bg=tema.CABECERA)
        textos.pack(side="left")
        tk.Label(
            textos, text="ENIGMA", bg=tema.CABECERA, fg=tema.TEXTO_FUERTE, font=(FUENTE, 12, "bold"), anchor="w"
        ).pack(fill="x")
        tk.Label(
            textos, text="Laboratorio de razonamiento", bg=tema.CABECERA, fg=tema.TEXTO_SUAVE,
            font=(FUENTE, 8), anchor="w",
        ).pack(fill="x")

        # Menus (los llena la ventana principal)
        self.menus = tk.Frame(fila, bg=tema.CABECERA)
        self.menus.pack(side="left", padx=(8, 0))

        # Ajustes y campana (de derecha a izquierda)
        self._img_campana = recursos.icono("campana", master=self)
        self._img_campana_aviso = recursos.icono("campana_aviso", master=self)
        self._ajustes = BotonIcono(
            fila, recursos.icono("ajustes", master=self), al_ajustes or (lambda: None),
            ayuda="Preferencias", fondo=tema.CABECERA,
        )
        self._ajustes.pack(side="right", padx=(0, 18))
        self._campana = BotonIcono(
            fila, self._img_campana, al_campana or (lambda: None),
            ayuda="Historial de compilaciones", fondo=tema.CABECERA,
        )
        self._campana.pack(side="right")

        # Archivo activo y estado, centrados
        self._centro = centro = tk.Frame(self, bg=tema.CABECERA)
        centro.place(relx=0.5, y=(ALTO - 1) // 2, anchor="center")
        self._fila = fila
        self._proyecto = tk.Label(centro, bg=tema.CABECERA, fg=tema.TEXTO_SUAVE, font=(FUENTE, 9))
        self._proyecto.pack(side="left")
        self._separador = tk.Label(
            centro, image=recursos.icono("chevron_der", master=self), bg=tema.CABECERA
        )
        self._archivo = tk.Label(centro, bg=tema.CABECERA, fg=tema.TEXTO_FUERTE, font=(FUENTE, 9))
        self._estado = tk.Label(centro, bg=tema.CABECERA, font=(FUENTE, 9))

        self.bind("<Configure>", self._reposicionar)
        self.actualizar(None, None, False)

    def _reposicionar(self, _evento=None) -> None:
        """Centra la ruta del archivo, pero sin pisar los menus cuando la ventana es angosta."""
        self.update_idletasks()
        ancho = self.winfo_width()
        borde_menus = self.menus.winfo_rootx() - self.winfo_rootx() + self.menus.winfo_width() + 24
        mitad = self._centro.winfo_reqwidth() / 2
        x = max(ancho / 2, borde_menus + mitad)
        self._centro.place(x=x, relx=0, y=(ALTO - 1) // 2, anchor="center")

    def actualizar(self, directorio_proyecto: str | None, ruta_archivo: str | None, modificado: bool) -> None:
        """Muestra proyecto > archivo activo, y si esta guardado."""
        proyecto = self._nombre_proyecto(directorio_proyecto)
        if ruta_archivo is None:
            self._proyecto.config(text=proyecto or "Sin archivo abierto")
            for widget in (self._separador, self._archivo, self._estado):
                widget.pack_forget()
            self.after_idle(self._reposicionar)
            return

        self._proyecto.config(text=proyecto)
        self._archivo.config(text=os.path.basename(ruta_archivo))
        if modificado:
            self._estado.config(text="●  Sin guardar", fg=tema.AVISO)
        else:
            self._estado.config(text="●  Guardado", fg=tema.EXITO)

        self._separador.pack_forget()
        self._archivo.pack_forget()
        self._estado.pack_forget()
        if proyecto:
            self._separador.pack(side="left", padx=2)
        self._archivo.pack(side="left")
        self._estado.pack(side="left", padx=(14, 0))
        self.after_idle(self._reposicionar)

    def marcar_aviso(self, hay_aviso: bool) -> None:
        """La campana muestra un punto amarillo cuando hay resultados sin revisar."""
        self._campana.cambiar_icono(self._img_campana_aviso if hay_aviso else self._img_campana)

    @staticmethod
    def _nombre_proyecto(directorio: str | None) -> str:
        if not directorio:
            return ""
        return os.path.basename(directorio.rstrip("/\\")) or directorio
