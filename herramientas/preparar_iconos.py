"""Genera los iconos del IDE (gui/assets/iconos/*.png) dibujandolos como vectores.

No usa librerias externas. Cada icono se define sobre una cuadricula de 24 x 24
con formas simples y se rasteriza con suavizado de bordes (supermuestreo).

    python herramientas/preparar_iconos.py

Genera un solo PNG por icono (gui/assets/iconos/<nombre>.png), en el tamaño que usa el IDE
(ver TAMANOS). Los PNG ya generados estan en el repositorio: no hace falta ejecutar esto para
usar el IDE, solo para cambiar o agregar un icono.

Formas:  ('l', pts)   linea (trazo)         ('pc', pts)  poligono cerrado (trazo)
         ('f', pts)   poligono relleno      ('c', cx, cy, r)  circulo relleno
         ('o', cx, cy, r)  anillo           ('rr', x, y, w, h, radio)  rectangulo redondeado (trazo)
         ('fr', x, y, w, h, radio)  rectangulo redondeado relleno
Un icono es una lista de capas (color, [formas]).
"""
from __future__ import annotations

import math
import os
import struct
import zlib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "gui", "assets", "iconos")
TAMANO_NORMAL = 16     # arbol, pestañas, botones y solapas
TAMANO_GRANDE = 20     # cabecera, "+" del arbol y tarjetas de la guia rapida
TAMANOS = {
    "ajustes": TAMANO_GRANDE, "bombilla": TAMANO_GRANDE, "campana": TAMANO_GRANDE,
    "campana_aviso": TAMANO_GRANDE, "mas": TAMANO_GRANDE, "varita": TAMANO_GRANDE,
}
SUPERMUESTREO = 4
GROSOR = 2.0  # en unidades de la cuadricula de 24

# Colores (los mismos de gui/tema.py)
GRIS = "#9aa0b3"
CLARO = "#c6c8d7"
AMARILLO = "#ffd400"
CARPETA = "#e3bc00"
MORADO = "#b06ad4"
ROJO = "#ff7b7b"


def arco(cx, cy, r, a0, a1, n=14):
    """Puntos de un arco; los angulos van en grados y 90 es 'arriba'."""
    puntos = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        puntos.append((cx + r * math.cos(a), cy - r * math.sin(a)))
    return puntos


ICONOS: dict[str, list] = {
    "vacio": [],  # transparente: reserva el hueco del chevron en las filas de archivos
    "chevron_der": [(GRIS, [("l", [(9, 6), (15, 12), (9, 18)])])],
    "chevron_der_claro": [(CLARO, [("l", [(9, 6), (15, 12), (9, 18)])])],
    "chevron_abajo": [(GRIS, [("l", [(6, 9), (12, 15), (18, 9)])])],
    "mas": [(GRIS, [("l", [(12, 5), (12, 19)]), ("l", [(5, 12), (19, 12)])])],
    "cerrar": [(GRIS, [("l", [(7, 7), (17, 17)]), ("l", [(17, 7), (7, 17)])])],

    "carpeta": [(CARPETA, [("pc", [(3, 6), (9, 6), (11, 8.5), (21, 8.5), (21, 19), (3, 19)])])],
    "carpeta_abierta": [(CARPETA, [
        ("l", [(3, 19), (3, 6), (9, 6), (11, 8.5), (19, 8.5), (19, 11)]),
        ("pc", [(3, 19), (6, 11), (22, 11), (19, 19)]),
    ])],
    "archivo_codigo": [(MORADO, [
        ("l", [(14, 3), (6, 3), (6, 21), (19, 21), (19, 8), (14, 3), (14, 8), (19, 8)]),
        ("l", [(10.5, 12.5), (8.5, 15), (10.5, 17.5)]),
        ("l", [(14.5, 12.5), (16.5, 15), (14.5, 17.5)]),
    ])],
    "lupa": [(GRIS, [("o", 10.5, 10.5, 6), ("l", [(15, 15), (20.5, 20.5)])])],
    "guardar": [(GRIS, [
        ("pc", [(4.5, 4), (16.5, 4), (20, 7.5), (20, 20), (4.5, 20)]),
        ("pc", [(8, 4), (8, 9), (15, 9), (15, 4)]),
        ("pc", [(8, 20), (8, 14), (16.5, 14), (16.5, 20)]),
    ])],
    "comprobar": [(GRIS, [("o", 12, 12, 9), ("l", [(8, 12.5), (11, 15.5), (16.5, 9)])])],
    "play": [(CLARO, [("f", [(7, 4.5), (20, 12), (7, 19.5)])])],

    "campana": [(CLARO, [
        ("pc", arco(12, 10.5, 5.5, 180, 0) + [(17.5, 15), (19.5, 17), (4.5, 17), (6.5, 15)]),
        ("l", arco(12, 19.5, 2, 180, 360, 8)),
        ("l", [(12, 3.5), (12, 5)]),
    ])],
    "campana_aviso": [(CLARO, [
        ("pc", arco(12, 10.5, 5.5, 180, 0) + [(17.5, 15), (19.5, 17), (4.5, 17), (6.5, 15)]),
        ("l", arco(12, 19.5, 2, 180, 360, 8)),
        ("l", [(12, 3.5), (12, 5)]),
    ]), (AMARILLO, [("c", 19, 5, 3.4)])],
    "ajustes": [(CLARO, [
        ("l", [(4, 8), (20, 8)]), ("l", [(4, 16), (20, 16)]),
        ("o", 15, 8, 2.6), ("o", 9, 16, 2.6),
    ])],

    "salida_a": [(AMARILLO, [
        ("rr", 3.5, 4.5, 17, 15, 2.5), ("l", [(7.5, 9), (10.5, 11.5), (7.5, 14)]), ("l", [(12.5, 14), (16, 14)]),
    ])],
    "salida_g": [(GRIS, [
        ("rr", 3.5, 4.5, 17, 15, 2.5), ("l", [(7.5, 9), (10.5, 11.5), (7.5, 14)]), ("l", [(12.5, 14), (16, 14)]),
    ])],
    "codigo_a": [(AMARILLO, [
        ("l", [(9, 7), (4, 12), (9, 17)]), ("l", [(15, 7), (20, 12), (15, 17)]), ("l", [(13.5, 5), (10.5, 19)]),
    ])],
    "codigo_g": [(GRIS, [
        ("l", [(9, 7), (4, 12), (9, 17)]), ("l", [(15, 7), (20, 12), (15, 17)]), ("l", [(13.5, 5), (10.5, 19)]),
    ])],
    "papelera": [(GRIS, [
        ("l", [(4, 7), (20, 7)]),
        ("pc", [(6, 7), (7, 20), (17, 20), (18, 7)]),
        ("l", [(9, 7), (9, 4), (15, 4), (15, 7)]),
        ("l", [(10.5, 11), (10.5, 16)]), ("l", [(13.5, 11), (13.5, 16)]),
    ])],

    "bombilla": [(AMARILLO, [
        ("pc", arco(12, 10, 6, 230, -50, 16) + [(14.5, 16.5), (9.5, 16.5)]),
        ("l", [(9.5, 19.5), (14.5, 19.5)]),
        ("l", [(10.5, 22), (13.5, 22)]),
    ])],
    "varita": [(AMARILLO, [
        ("l", [(4.5, 19.5), (14, 10)]),
        ("l", [(17, 3), (17, 9)]), ("l", [(14, 6), (20, 6)]),
        ("l", [(19.5, 13), (19.5, 17)]), ("l", [(17.5, 15), (21.5, 15)]),
        ("l", [(8, 3.5), (8, 6.5)]), ("l", [(6.5, 5), (9.5, 5)]),
    ])],

    "libro": [(GRIS, [
        ("pc", [(3.5, 5), (11.5, 6.5), (11.5, 20), (3.5, 18.5)]),
        ("pc", [(20.5, 5), (12.5, 6.5), (12.5, 20), (20.5, 18.5)]),
    ])],
    "ayuda": [(GRIS, [
        ("o", 12, 12, 9),
        ("l", arco(12, 9.6, 2.9, 170, -60, 10) + [(12, 13.4)]),
        ("c", 12, 16.8, 1.1),
    ])],
}


# --------------------------------------------------------------------------- #
# Rasterizado
# --------------------------------------------------------------------------- #

def _dist_segmento(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    largo2 = dx * dx + dy * dy
    t = 0.0 if largo2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / largo2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _dentro_poligono(px, py, pts):
    dentro = False
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            dentro = not dentro
    return dentro


def _sdf_rect_redondeado(px, py, x, y, w, h, r):
    cx, cy = x + w / 2, y + h / 2
    qx = abs(px - cx) - (w / 2 - r)
    qy = abs(py - cy) - (h / 2 - r)
    return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - r


def _cubre(forma, px, py, medio):
    tipo = forma[0]
    if tipo in ("l", "pc"):
        pts = forma[1]
        pares = list(zip(pts, pts[1:]))
        if tipo == "pc":
            pares.append((pts[-1], pts[0]))
        return any(_dist_segmento(px, py, a[0], a[1], b[0], b[1]) <= medio for a, b in pares)
    if tipo == "f":
        return _dentro_poligono(px, py, forma[1])
    if tipo == "c":
        return math.hypot(px - forma[1], py - forma[2]) <= forma[3]
    if tipo == "o":
        return abs(math.hypot(px - forma[1], py - forma[2]) - forma[3]) <= medio
    if tipo == "rr":
        return abs(_sdf_rect_redondeado(px, py, *forma[1:])) <= medio
    if tipo == "fr":
        return _sdf_rect_redondeado(px, py, *forma[1:]) <= 0
    raise ValueError(tipo)


def _color(hex_):
    return int(hex_[1:3], 16), int(hex_[3:5], 16), int(hex_[5:7], 16)


def rasterizar(capas, tam: int):
    """Devuelve filas RGBA (bytearray) de un icono de tam x tam."""
    escala = tam / 24
    medio = GROSOR / 2
    filas = [bytearray(tam * 4) for _ in range(tam)]
    for color, formas in capas:
        r, g, b = _color(color)
        for py in range(tam):
            for px in range(tam):
                cubiertos = 0
                for sy in range(SUPERMUESTREO):
                    y = (py + (sy + 0.5) / SUPERMUESTREO) / escala
                    for sx in range(SUPERMUESTREO):
                        x = (px + (sx + 0.5) / SUPERMUESTREO) / escala
                        if any(_cubre(f, x, y, medio) for f in formas):
                            cubiertos += 1
                alfa_capa = cubiertos / (SUPERMUESTREO ** 2)
                if not alfa_capa:
                    continue
                i = px * 4
                fila = filas[py]
                alfa_base = fila[i + 3] / 255
                alfa = alfa_capa + alfa_base * (1 - alfa_capa)
                for k, canal in enumerate((r, g, b)):
                    base = fila[i + k]
                    fila[i + k] = round((canal * alfa_capa + base * alfa_base * (1 - alfa_capa)) / alfa)
                fila[i + 3] = round(alfa * 255)
    return filas


def escribir_png(ruta: str, ancho: int, alto: int, filas) -> None:
    def chunk(tipo: bytes, cuerpo: bytes) -> bytes:
        return struct.pack(">I", len(cuerpo)) + tipo + cuerpo + struct.pack(">I", zlib.crc32(tipo + cuerpo) & 0xFFFFFFFF)

    crudo = b"".join(b"\x00" + bytes(f) for f in filas)
    contenido = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(crudo, 9))
        + chunk(b"IEND", b"")
    )
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(contenido)


def main() -> None:
    for nombre, capas in ICONOS.items():
        tam = TAMANOS.get(nombre, TAMANO_NORMAL)
        escribir_png(os.path.join(SALIDA, f"{nombre}.png"), tam, tam, rasterizar(capas, tam))
    print(f"Listo: {len(ICONOS)} iconos en gui/assets/iconos/")


if __name__ == "__main__":
    main()
