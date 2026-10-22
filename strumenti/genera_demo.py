#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera il pacchetto demo di Nastro.

    python3 strumenti/genera_demo.py

Scrive in demo/:
    cover.jpg     una copertina astratta 1600x900
    mix.wav       il brano completo (kick + 808 + hat)
    kick.wav      solo la cassa
    bass808.wav   solo l'808
    hat.wav       solo gli hi-hat

Le tracce sono sintetizzate qui: niente campioni esterni, niente licenze.
Sono mono, 32 kHz, 16 bit e durano 12 secondi (6 battute a 120 BPM).
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SR = 32_000
BPM = 120
BATTITO = 60.0 / BPM
DURATA = 12.0
CARTELLA = Path(__file__).resolve().parent.parent / "demo"
rng = np.random.default_rng(7)


# ---------------------------------------------------------------- audio ----
def campioni(secondi: float) -> int:
    return int(round(secondi * SR))


def vuoto() -> np.ndarray:
    return np.zeros(campioni(DURATA), dtype=np.float32)


def inviluppo(n: int, attacco: float, decadimento: float) -> np.ndarray:
    t = np.arange(n) / SR
    salita = np.clip(t / max(attacco, 1e-4), 0.0, 1.0)
    return salita * np.exp(-t / max(decadimento, 1e-4))


def colpo_kick() -> np.ndarray:
    """Cassa sintetica: glissando 160 -> 48 Hz, corpo corto e click."""
    n = campioni(0.5)
    t = np.arange(n) / SR
    frequenza = 48.0 + 112.0 * np.exp(-t / 0.045)
    fase = 2.0 * np.pi * np.cumsum(frequenza) / SR
    corpo = np.sin(fase) * inviluppo(n, 0.0015, 0.15)
    click = rng.standard_normal(n) * np.exp(-t / 0.004) * 0.4
    click = np.diff(np.concatenate([click[:1], click]))  # passa-alto semplice
    return np.tanh((corpo + click * 0.7) * 1.5).astype(np.float32)


def colpo_hat(accento: float) -> np.ndarray:
    n = campioni(0.11)
    t = np.arange(n) / SR
    rumore = rng.standard_normal(n)
    rumore = np.diff(np.concatenate([rumore[:1], rumore]))  # via i bassi
    env = inviluppo(n, 0.001, 0.028)
    return (rumore * env * accento).astype(np.float32)


def nota_808(frequenza: float, durata: float, glissando: float = 6.0) -> np.ndarray:
    n = campioni(durata)
    t = np.arange(n) / SR
    f = frequenza + glissando * np.exp(-t / 0.07)
    fase = 2.0 * np.pi * np.cumsum(f) / SR
    onda = np.sin(fase) + 0.22 * np.sin(2.0 * fase) + 0.08 * np.sin(3.0 * fase)
    env = inviluppo(n, 0.01, durata * 0.62)
    return np.tanh(onda * env * 1.7).astype(np.float32)


def somma(destinazione: np.ndarray, pezzo: np.ndarray, quando: float, guadagno: float) -> None:
    inizio = campioni(quando)
    fine = min(len(destinazione), inizio + len(pezzo))
    if fine > inizio:
        destinazione[inizio:fine] += pezzo[: fine - inizio] * guadagno


def costruisci_tracce() -> dict[str, np.ndarray]:
    kick = vuoto()
    basso = vuoto()
    hat = vuoto()

    kick_colpo = colpo_kick()
    battiti = int(DURATA / BATTITO)
    for b in range(battiti):
        somma(kick, kick_colpo, b * BATTITO, 1.0)

    # 808: un disegno diverso ogni battuta, con note lunghe e sincopi.
    disegno = [
        [(0.0, 0.85, 55.0), (2.5, 0.45, 55.0)],
        [(0.0, 0.55, 49.0), (1.5, 0.4, 55.0), (2.0, 0.7, 41.2)],
        [(0.0, 1.2, 41.2)],
        [(0.0, 0.6, 49.0), (1.5, 0.5, 61.7), (3.0, 0.5, 55.0)],
        [(0.0, 0.8, 55.0), (2.0, 0.8, 49.0)],
        [(0.0, 1.4, 41.2), (3.0, 0.45, 55.0)],
    ]
    for indice, battuta in enumerate(disegno):
        base = indice * 4 * BATTITO
        for passo, durata, frequenza in battuta:
            somma(basso, nota_808(frequenza, durata), base + passo * BATTITO, 0.9)
        if base + 4 * BATTITO > DURATA:
            break

    # hi-hat: ottavi, con l'accento sul battere.
    hat_colpo = colpo_hat(1.0)
    hat_debole = colpo_hat(0.45)
    for ottavo in range(int(DURATA / (BATTITO / 2))):
        pezzo = hat_colpo if ottavo % 2 == 0 else hat_debole
        somma(hat, pezzo, ottavo * (BATTITO / 2), 0.55)

    mix = kick * 0.95 + basso * 0.85 + hat * 0.4
    return {"kick": kick, "bass808": basso, "hat": hat, "mix": mix}


def scrivi_wav(percorso: Path, dati: np.ndarray) -> None:
    picco = float(np.max(np.abs(dati))) or 1.0
    normalizzato = dati / picco * 0.89
    interi = np.clip(normalizzato * 32767.0, -32768, 32767).astype("<i2")
    with wave.open(str(percorso), "wb") as uscita:
        uscita.setnchannels(1)
        uscita.setsampwidth(2)
        uscita.setframerate(SR)
        uscita.writeframes(interi.tobytes())



# --------------------------------------------------------------- cover ----
def costruisci_cover(percorso: Path, larghezza: int = 1600, altezza: int = 900) -> None:
    """Copertina astratta: gradiente notturno, anelli caldi e grana."""
    y = np.linspace(0.0, 1.0, altezza, dtype=np.float32)[:, None]
    x = np.linspace(0.0, 1.0, larghezza, dtype=np.float32)[None, :]

    base = np.zeros((altezza, larghezza, 3), dtype=np.float32)
    base[..., 0] = 0.055 + 0.10 * x + 0.05 * y
    base[..., 1] = 0.045 + 0.035 * x + 0.02 * y
    base[..., 2] = 0.085 + 0.14 * (1.0 - x) + 0.04 * y

    # alone arancione in basso a destra
    dx = x - 0.72
    dy = y - 0.68
    alone = np.exp(-((dx / 0.20) ** 2 + (dy / 0.30) ** 2))
    base[..., 0] += alone * 0.62
    base[..., 1] += alone * 0.18
    base[..., 2] += alone * 0.05

    # alone freddo in alto a sinistra
    dx = x - 0.22
    dy = y - 0.18
    freddo = np.exp(-((dx / 0.28) ** 2 + (dy / 0.22) ** 2))
    base[..., 2] += freddo * 0.25
    base[..., 1] += freddo * 0.10

    immagine = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8), "RGB")

    # anelli concentrici, disegnati su un livello a parte e sfocati appena
    strati = Image.new("RGBA", immagine.size, (0, 0, 0, 0))
    disegno = ImageDraw.Draw(strati)
    centro = (int(larghezza * 0.72), int(altezza * 0.68))
    for indice in range(9):
        raggio = 60 + indice * 58
        colore = (255, 150 + indice * 8, 90, max(18, 120 - indice * 12))
        disegno.ellipse(
            [centro[0] - raggio, centro[1] - raggio, centro[0] + raggio, centro[1] + raggio],
            outline=colore,
            width=2 + indice // 3,
        )
    # una diagonale chiara che taglia la scena
    disegno.line([(0, int(altezza * 0.86)), (larghezza, int(altezza * 0.36))],
                 fill=(230, 240, 255, 38), width=3)
    strati = strati.filter(ImageFilter.GaussianBlur(3))
    immagine = Image.alpha_composite(immagine.convert("RGBA"), strati).convert("RGB")

    # grana leggerissima
    grana = rng.normal(0.0, 5.5, (altezza, larghezza, 1)).repeat(3, axis=2)
    finale = np.clip(np.asarray(immagine, dtype=np.float32) + grana, 0, 255).astype(np.uint8)
    Image.fromarray(finale, "RGB").save(percorso, quality=88, optimize=True)


def main() -> int:
    CARTELLA.mkdir(parents=True, exist_ok=True)
    tracce = costruisci_tracce()
    for nome, dati in tracce.items():
        percorso = CARTELLA / f"{nome}.wav"
        scrivi_wav(percorso, dati)
        print(f"  {percorso.relative_to(CARTELLA.parent)}  ({percorso.stat().st_size / 1024:.0f} KB)")
    cover = CARTELLA / "cover.jpg"
    costruisci_cover(cover)
    print(f"  {cover.relative_to(CARTELLA.parent)}  ({cover.stat().st_size / 1024:.0f} KB)")
    print("Pacchetto demo pronto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
