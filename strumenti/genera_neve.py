#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera il loop di neve usato come esempio dell'effetto Neve.

    python3 strumenti/genera_neve.py

Scrive in demo/:
    neve.mp4      neve su fondo nero, 960x540, 6 s, 30 fps, senza audio

Il fiocco è disegnato qui (sfere morbide su nero, tre profondità, avvolgimento
verticale periodico) e codificato con ffmpeg in H.264: niente filmati di terzi,
niente licenze. Su fondo nero il livello si usa bene in fusione "somma" o
"schermo", così la neve si vede sopra la cover senza coprirla.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np

LARGHEZZA = 960
ALTEZZA = 540
FPS = 30
DURATA = 6.0
FOTOGRAMMI = int(FPS * DURATA)
CARTELLA = Path(__file__).resolve().parent.parent / "demo"
USCITA = CARTELLA / "neve.mp4"
rng = np.random.default_rng(11)


def sprite(raggio: int) -> np.ndarray:
    """Sfera di luce morbida, valori 0..1, con bordo sfumato."""
    lato = raggio * 2 + 1
    y, x = np.mgrid[0:lato, 0:lato]
    cx = cy = raggio
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / max(raggio, 1)
    alone = np.clip(1.0 - dist, 0.0, 1.0) ** 1.6
    nucleo = np.clip(1.0 - dist * 1.8, 0.0, 1.0) ** 2.2
    return np.clip(alone * 0.55 + nucleo * 0.65, 0.0, 1.0)


def fiocchi(quanti: int, raggio_min: int, raggio_max: int, velocita: tuple[float, float]):
    """Particelle con velocità costante: il loop torna al punto di partenza."""
    n = rng.integers(raggio_min, raggio_max + 1, size=quanti)
    return {
        "x": rng.uniform(0, LARGHEZZA, quanti),
        "y": rng.uniform(0, ALTEZZA, quanti),
        # passo in pixel/fotogramma, scelto perché il totale cada su un multiplo
        # esatto dell'altezza: a fine loop la scena è identica al primo frame.
        "v": rng.uniform(*velocita, quanti),
        "r": n,
        "a": rng.uniform(0.35, 1.0, quanti),
        # deriva laterale lenta, anch'essa periodica
        "dx": rng.uniform(-0.35, 0.35, quanti),
        "fase": rng.uniform(0, 2 * np.pi, quanti),
    }


def passo_esatto(velocita: float, secondi: float) -> float:
    """Velocità in px/frame che in `secondi` percorre un numero intero di schermate."""
    totale = velocita * FPS * secondi
    giri = max(1.0, round(totale / ALTEZZA))
    return giri * ALTEZZA / (FPS * secondi)


def disegna(gruppo, t: float, destinazione: np.ndarray, sprites) -> None:
    altezza, larghezza = destinazione.shape
    for i in range(len(gruppo["x"])):
        r = int(gruppo["r"][i])
        y = (gruppo["y"][i] + gruppo["v"][i] * t * FPS) % altezza
        x = (gruppo["x"][i] + np.sin(t * 0.7 + gruppo["fase"][i]) * 9) % larghezza
        s = sprites[r]
        lato = s.shape[0]
        x0 = int(round(x)) - r
        y0 = int(round(y)) - r
        x1, y1 = x0 + lato, y0 + lato
        # coordinate ritagliate ai bordi della tela, con avvolgimento orizzontale
        for ox in (0, -larghezza, larghezza):
            bx0 = max(0, x0 + ox)
            bx1 = min(larghezza, x1 + ox)
            if bx0 >= bx1:
                continue
            sx0 = bx0 - (x0 + ox)
            by0 = max(0, y0)
            by1 = min(altezza, y1)
            if by0 >= by1:
                continue
            sy0 = by0 - y0
            pezzo = s[sy0:sy0 + (by1 - by0), sx0:sx0 + (bx1 - bx0)]
            destinazione[by0:by1, bx0:bx1] += pezzo * gruppo["a"][i]


def main() -> int:
    if not CARTELLA.exists():
        print(f"manca {CARTELLA}", file=sys.stderr)
        return 1

    lontani = fiocchi(520, 2, 3, (0.55, 0.9))
    medi = fiocchi(260, 4, 6, (1.1, 1.7))
    vicini = fiocchi(70, 8, 15, (2.2, 3.1))
    gruppi = (lontani, medi, vicini)
    raggi = sorted({int(raggio) for gruppo in gruppi for raggio in gruppo["r"]})
    sprites = {r: sprite(r) for r in raggi}
    for gruppo in gruppi:
        for i in range(len(gruppo["v"])):
            gruppo["v"][i] = passo_esatto(float(gruppo["v"][i]), DURATA)

    comando = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{LARGHEZZA}x{ALTEZZA}", "-r", str(FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "26",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(USCITA),
    ]
    processo = subprocess.Popen(comando, stdin=subprocess.PIPE)

    fondo = np.array([6, 8, 14], dtype=np.float32)
    for f in range(FOTOGRAMMI):
        t = f / FPS
        tela = np.zeros((ALTEZZA, LARGHEZZA), dtype=np.float32)
        disegna(lontani, t, tela, sprites)
        disegna(medi, t, tela, sprites)
        disegna(vicini, t, tela, sprites)
        luminanza = np.clip(tela, 0.0, 1.0)[:, :, None]
        # neve leggermente fredda, fondo quasi nero
        rgb = fondo + luminanza * (np.array([236.0, 242.0, 255.0]) - fondo)
        processo.stdin.write(np.clip(rgb, 0, 255).astype(np.uint8).tobytes())
        if f % 30 == 0:
            print(f"\r{f}/{FOTOGRAMMI} fotogrammi", end="", flush=True)

    processo.stdin.close()
    codice = processo.wait()
    print()
    if codice != 0:
        print("ffmpeg ha fallito", file=sys.stderr)
        return codice
    print(f"scritto {USCITA} ({USCITA.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
