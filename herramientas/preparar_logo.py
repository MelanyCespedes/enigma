"""Genera los recursos del logo a partir de docs/logo_original.png.

No usa librerias externas (solo struct y zlib). Uso, desde la raiz del proyecto:

    python herramientas/preparar_logo.py

Produce:
    gui/assets/logo_cubo.png   cubo cuadrado de 256 px, fondo transparente
                               (icono de la ventana y cabecera del IDE)
    docs/logo_enigma.png       logo completo (cubo + nombre), fondo transparente
                               (README y portada de la documentacion)

El PNG original debe ser RGBA de 8 bits, sin entrelazado.
"""
from __future__ import annotations

import os
import struct
import zlib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = os.path.join(RAIZ, "docs", "logo_original.png")

# Zona del cubo y del logo completo dentro de la imagen original (940 x 660).
RECORTE_CUBO = (235, 30, 705, 500)
RECORTE_COMPLETO = (150, 30, 790, 610)

UMBRAL_NEGRO = 6      # por debajo de este brillo, el pixel es fondo
SUAVIZADO = 26        # ancho de la transicion fondo -> logo (bordes suaves)


def leer_png(ruta: str) -> tuple[int, int, list[bytearray]]:
    datos = open(ruta, "rb").read()
    if datos[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("No es un PNG")
    pos, idat, ancho, alto = 8, b"", 0, 0
    while pos < len(datos):
        largo, = struct.unpack(">I", datos[pos:pos + 4])
        tipo = datos[pos + 4:pos + 8]
        cuerpo = datos[pos + 8:pos + 8 + largo]
        if tipo == b"IHDR":
            ancho, alto, prof, color, _, _, entrelazado = struct.unpack(">IIBBBBB", cuerpo)
            if (prof, color, entrelazado) != (8, 6, 0):
                raise ValueError("Se espera un PNG RGBA de 8 bits sin entrelazado")
        elif tipo == b"IDAT":
            idat += cuerpo
        pos += 12 + largo

    crudo = zlib.decompress(idat)
    paso = ancho * 4
    filas: list[bytearray] = []
    anterior = bytearray(paso)
    for y in range(alto):
        inicio = y * (paso + 1)
        filtro = crudo[inicio]
        fila = bytearray(crudo[inicio + 1:inicio + 1 + paso])
        for i in range(paso):
            a = fila[i - 4] if i >= 4 else 0
            b = anterior[i]
            c = anterior[i - 4] if i >= 4 else 0
            if filtro == 1:
                fila[i] = (fila[i] + a) & 255
            elif filtro == 2:
                fila[i] = (fila[i] + b) & 255
            elif filtro == 3:
                fila[i] = (fila[i] + (a + b) // 2) & 255
            elif filtro == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                fila[i] = (fila[i] + pred) & 255
        filas.append(fila)
        anterior = fila
    return ancho, alto, filas


def escribir_png(ruta: str, ancho: int, alto: int, filas: list[bytearray]) -> None:
    def chunk(tipo: bytes, cuerpo: bytes) -> bytes:
        crc = zlib.crc32(tipo + cuerpo) & 0xFFFFFFFF
        return struct.pack(">I", len(cuerpo)) + tipo + cuerpo + struct.pack(">I", crc)

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


def recortar(filas, recorte):
    x1, y1, x2, y2 = recorte
    return [bytearray(f[x1 * 4:x2 * 4]) for f in filas[y1:y2]]


def fondo_a_transparente(filas) -> None:
    """El fondo es negro: el brillo del pixel decide su opacidad."""
    for fila in filas:
        for i in range(0, len(fila), 4):
            brillo = max(fila[i], fila[i + 1], fila[i + 2])
            alfa = (brillo - UMBRAL_NEGRO) * 255 // SUAVIZADO
            fila[i + 3] = max(0, min(255, alfa))


def reducir(filas, ancho: int, alto: int, nuevo_ancho: int):
    """Reduccion por promedio de area (conserva bordes suaves)."""
    factor = ancho / nuevo_ancho
    nuevo_alto = round(alto / factor)
    resultado = []
    for ny in range(nuevo_alto):
        y0, y1 = int(ny * factor), max(int(ny * factor) + 1, int((ny + 1) * factor))
        fila = bytearray(nuevo_ancho * 4)
        for nx in range(nuevo_ancho):
            x0, x1 = int(nx * factor), max(int(nx * factor) + 1, int((nx + 1) * factor))
            r = g = b = a = n = 0
            for y in range(y0, min(y1, alto)):
                origen = filas[y]
                for x in range(x0, min(x1, ancho)):
                    k = x * 4
                    alfa = origen[k + 3]
                    r += origen[k] * alfa
                    g += origen[k + 1] * alfa
                    b += origen[k + 2] * alfa
                    a += alfa
                    n += 1
            if a:
                fila[nx * 4:nx * 4 + 4] = bytes((r // a, g // a, b // a, a // n))
        resultado.append(fila)
    return resultado, nuevo_ancho, nuevo_alto


def main() -> None:
    ancho, alto, filas = leer_png(ORIGINAL)

    cubo = recortar(filas, RECORTE_CUBO)
    fondo_a_transparente(cubo)
    x1, y1, x2, y2 = RECORTE_CUBO
    cubo, w, h = reducir(cubo, x2 - x1, y2 - y1, 256)
    escribir_png(os.path.join(RAIZ, "gui", "assets", "logo_cubo.png"), w, h, cubo)

    completo = recortar(filas, RECORTE_COMPLETO)
    fondo_a_transparente(completo)
    x1, y1, x2, y2 = RECORTE_COMPLETO
    escribir_png(os.path.join(RAIZ, "docs", "logo_enigma.png"), x2 - x1, y2 - y1, completo)
    print("Listo: gui/assets/logo_cubo.png y docs/logo_enigma.png")


if __name__ == "__main__":
    main()
