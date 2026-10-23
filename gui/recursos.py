"""Imagenes del IDE: logo, icono de la ventana y los iconos PNG (carpeta gui/assets)."""
from __future__ import annotations

import os
import tkinter as tk

CARPETA_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
CARPETA_ICONOS = os.path.join(CARPETA_ASSETS, "iconos")  # los genera herramientas/preparar_iconos.py
TAMANO_RESPALDO = 16
LOGO_CUBO = "logo_cubo.png"  # 256 x 256, fondo transparente (ver herramientas/preparar_logo.py)


def cargar_imagen(nombre: str, reducir: int = 1, master=None) -> tk.PhotoImage | None:
    """Devuelve la imagen reducida 'reducir' veces, o None si no existe.
    Quien la use debe guardar la referencia (si no, Tk la descarta)."""
    ruta = os.path.join(CARPETA_ASSETS, nombre)
    try:
        imagen = tk.PhotoImage(master=master, file=ruta)
    except tk.TclError:
        return None
    return imagen.subsample(reducir, reducir) if reducir > 1 else imagen


def poner_icono(ventana) -> None:
    """Usa el cubo como icono de la ventana y de la barra de tareas."""
    iconos = [cargar_imagen(LOGO_CUBO, reducir, master=ventana) for reducir in (4, 8)]  # 64 y 32 px
    iconos = [i for i in iconos if i is not None]
    if iconos:
        ventana._iconos = iconos  # referencia: si no, Tk la descarta
        ventana.iconphoto(True, *iconos)



def icono(nombre: str, master=None) -> tk.PhotoImage:
    """Devuelve el icono 'nombre'. Se guarda en la ventana raiz para que Tk no lo
    descarte; si falta el archivo, devuelve una imagen transparente."""
    raiz = master.winfo_toplevel() if master is not None else tk._default_root
    cache = raiz.__dict__.setdefault("_cache_iconos", {})
    if nombre not in cache:
        ruta = os.path.join(CARPETA_ICONOS, f"{nombre}.png")
        try:
            cache[nombre] = tk.PhotoImage(master=raiz, file=ruta)
        except tk.TclError:
            cache[nombre] = tk.PhotoImage(master=raiz, width=TAMANO_RESPALDO, height=TAMANO_RESPALDO)
    return cache[nombre]
