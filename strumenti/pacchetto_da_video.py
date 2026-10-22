#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Da un video (file o link YouTube) al pacchetto demo di Nastro.

    python3 strumenti/pacchetto_da_video.py video.mp4 --uscita demo-mio
    python3 strumenti/pacchetto_da_video.py "https://youtu.be/XXXX" --uscita demo-mio

Scrive nella cartella indicata, con i nomi che l'app si aspetta:

    cover.jpg     un fotogramma del video (l'immagine di partenza)
    mix.wav       il brano completo, come sta nel video
    kick.wav      la cassa isolata
    bass808.wav   il basso/808 isolato
    hat.wav       gli hi-hat isolati

Come lavora:

  1. scarica (solo se il link è un URL) e misura il file con ffprobe;
  2. tira fuori l'audio, poi chiama demucs per separare batteria e basso dal
     resto: se demucs non c'è, ripiega sulle bande del mix;
  3. filtra le bande giuste e riscrive tutto a 32 kHz, come il pacchetto che
     sta in demo/;
  4. prende un fotogramma a metà brano per la copertina.

Il video NON viene scomposto in strati: da un filmato già montato non si
separano titolo, neve e sfondo. Quelli li genera l'app (Titolo, Aura, Neve).
Le dipendenze obbligatorie sono ffmpeg, numpy, scipy e soundfile; demucs e
librosa, se presenti, migliorano il risultato.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import scipy.signal as ss
import soundfile as sf
from scipy.signal import butter, sosfilt

SR = 32_000
SR_SORGENTE = 44_100
CASSA = (30.0, 170.0)     # la banda che l'app ascolta per il kick
BASSO = (25.0, 250.0)     # l'808 sta sotto i 250 Hz
HAT = (6_000.0, None)     # gli hi-hat stanno sopra i 6 kHz


def comando(*parti: str) -> str:
    """Esegue un comando e restituisce l'output; si ferma se fallisce."""
    esito = subprocess.run(parti, capture_output=True, text=True)
    if esito.returncode != 0:
        raise RuntimeError(f"{parti[0]} è uscito con {esito.returncode}: {esito.stderr.strip()[:400]}")
    return esito.stdout


def hai(programma: str) -> bool:
    return shutil.which(programma) is not None


def hai_python(modulo: str) -> bool:
    esito = subprocess.run([sys.executable, "-c", f"import {modulo}"], capture_output=True)
    return esito.returncode == 0


# ------------------------------------------------------------------ input ---
def scarica(url: str, cartella: Path) -> Path:
    if not hai("yt-dlp"):
        raise RuntimeError("serve yt-dlp per i link: python3 -m pip install yt-dlp")
    print("scarico", url)
    uscita = comando(
        "yt-dlp",
        "-f", "bv*[height<=1080]+ba/b[height<=1080]",
        "--merge-output-format", "mp4",
        "--no-warnings",
        "--print", "after_move:filepath",
        "-o", str(cartella / "%(id)s.%(ext)s"),
        url,
    ).strip().splitlines()
    percorso = Path(uscita[-1])
    if not percorso.exists():
        raise RuntimeError("yt-dlp non ha prodotto un file leggibile")
    return percorso


def misura(video: Path) -> dict:
    testo = comando(
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration:stream=width,height,codec_type",
        "-of", "json", str(video),
    )
    dati = json.loads(testo)
    visivo = next((f for f in dati.get("streams", []) if f.get("codec_type") == "video"), {})
    return {
        "durata": float(dati.get("format", {}).get("duration", 0.0)),
        "larghezza": int(visivo.get("width", 0)),
        "altezza": int(visivo.get("height", 0)),
    }


def estrai_audio(video: Path, destinazione: Path, inizio: float, durata: float | None) -> None:
    parti = ["ffmpeg", "-y", "-v", "error", "-ss", str(inizio), "-i", str(video)]
    if durata:
        parti += ["-t", str(durata)]
    parti += ["-vn", "-ac", "2", "-ar", str(SR_SORGENTE), str(destinazione)]
    comando(*parti)


def estrai_copertina(video: Path, destinazione: Path, quando: float) -> None:
    comando(
        "ffmpeg", "-y", "-v", "error",
        "-ss", f"{quando:.3f}", "-i", str(video),
        "-frames:v", "1", "-q:v", "4", str(destinazione),
    )


# ----------------------------------------------------------------- audio ---
def leggi(percorso: Path) -> np.ndarray:
    dati, frequenza = sf.read(percorso, always_2d=True)
    if frequenza != SR_SORGENTE:
        dati = ss.resample_poly(dati, SR_SORGENTE, frequenza, axis=0)
    return dati


def filtra(dati: np.ndarray, banda: tuple[float, float | None]) -> np.ndarray:
    basso, alto = banda
    normale = SR_SORGENTE / 2
    if alto:
        sos = butter(4, [basso / normale, alto / normale], btype="band", output="sos")
    else:
        sos = butter(4, basso / normale, btype="high", output="sos")
    return sosfilt(sos, dati, axis=0)


def scrivi(percorso: Path, dati: np.ndarray, picco: float, mono: bool) -> None:
    if mono:
        dati = dati.mean(axis=1, keepdims=True)
    massimo = float(np.max(np.abs(dati))) or 1.0
    finale = ss.resample_poly(dati / massimo * picco, SR, SR_SORGENTE, axis=0)
    sf.write(percorso, finale, SR, subtype="PCM_16")


def separa_steli(audio: Path, cartella: Path) -> tuple[Path | None, Path | None]:
    """demucs: batteria e basso. Restituisce (batteria, basso), o (None, None)."""
    if not hai_python("demucs"):
        print("demucs assente: separo le bande direttamente dal mix")
        return None, None
    print("sepo le tracce con demucs (qualche decina di secondi)…")
    esito = subprocess.run(
        [sys.executable, "-m", "demucs.separate", "-n", "htdemucs", "--shifts", "0",
         "-o", str(cartella), str(audio)],
        capture_output=True, text=True,
    )
    if esito.returncode != 0:
        print("demucs non è andato a buon fine, uso le bande del mix")
        print("  ", (esito.stderr or esito.stdout).strip().splitlines()[-1][:200])
        return None, None
    uscita = cartella / "htdemucs" / audio.stem
    batteria = uscita / "drums.wav"
    basso = uscita / "bass.wav"
    return (batteria if batteria.exists() else None), (basso if basso.exists() else None)


def inviluppo_banda(mono: np.ndarray, banda: tuple[float, float], passo: float = 0.01) -> np.ndarray:
    """Energia della banda in finestre di 10 ms, normalizzata: la stessa idea dell'app."""
    sos = butter(4, [banda[0] / (SR / 2), banda[1] / (SR / 2)], btype="band", output="sos")
    filtrato = sosfilt(sos, mono)
    n = max(1, int(passo * SR))
    quanti = len(filtrato) // n
    if not quanti:
        return np.zeros(1)
    energia = np.sqrt((filtrato[: quanti * n].reshape(quanti, n) ** 2).mean(axis=1))
    return energia / (float(energia.max()) or 1.0)


def conta_eventi(mono: np.ndarray, banda: tuple[float, float], passo: float = 0.01) -> int:
    """Soglia adattiva + isteresi, come l'analisi che gira nel browser."""
    from scipy.ndimage import median_filter  # noqa: PLC0415 - serve solo qui

    env = inviluppo_banda(mono, banda, passo)
    mezzo = max(2, int(round(0.8 / passo)))
    mediana = median_filter(env, size=2 * mezzo + 1, mode="nearest")
    soglia = mediana * 2.0 + 0.012  # rapporto 2.0: sensibilità 1

    acceso, inizio, eventi = False, 0, []
    for i, valore in enumerate(env):
        if not acceso:
            if valore > soglia[i]:
                acceso, inizio = True, i
        elif valore < soglia[i] * 0.62 and i - inizio > 2:
            acceso = False
            eventi.append((inizio, i))
    if acceso:
        eventi.append((inizio, len(env)))

    uniti: list[list[float]] = []
    for i0, i1 in eventi:
        t = i0 * passo
        d = max(0.02, min((i1 - i0) * passo, 0.45))
        if uniti and t - (uniti[-1][0] + uniti[-1][1]) < 0.06:
            uniti[-1][1] = max(uniti[-1][1], t + d - uniti[-1][0])
        else:
            uniti.append([t, d])
    return len(uniti)


def conta_colpi(cassa: Path, mix: Path) -> dict:
    """Colpi di cassa (rilevatore locale) e BPM (librosa, se c'è)."""
    dati, _ = sf.read(cassa, always_2d=True)
    colpi = conta_eventi(dati.mean(axis=1), CASSA)

    bpm = None
    if hai_python("librosa"):
        try:
            import librosa  # noqa: PLC0415 - opzionale, importato solo qui

            # Il BPM va cercato sul brano intero: la cassa da sola è troppo sparsa.
            y, sr = librosa.load(str(mix), sr=22_050, mono=True)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            bpm = round(float(np.atleast_1d(tempo)[0]), 2)
        except Exception as errore:
            print("il BPM salta:", errore)
    return {"bpm": bpm, "colpi": colpi}


# ------------------------------------------------------------------- main ---
def main() -> int:
    argomenti = argparse.ArgumentParser(description="Da un video al pacchetto demo di Nastro.")
    argomenti.add_argument("sorgente", help="file video oppure link (YouTube e simili)")
    argomenti.add_argument("--uscita", default="demo-video",
                           help="cartella di destinazione (default demo-video)")
    argomenti.add_argument("--inizio", type=float, default=0.0, help="secondo da cui partire")
    argomenti.add_argument("--durata", type=float, default=None, help="quanti secondi tenere")
    argomenti.add_argument("--mono", action="store_true", help="tracce mono (metà dello spazio)")
    argomenti = argomenti.parse_args()

    for programma in ("ffmpeg", "ffprobe"):
        if not hai(programma):
            print(f"manca {programma}: installalo prima di continuare")
            return 1

    uscita = Path(argomenti.uscita).expanduser().resolve()
    uscita.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="nastro-video-") as temporanea:
        cartella = Path(temporanea)
        if argomenti.sorgente.startswith(("http://", "https://")):
            video = scarica(argomenti.sorgente, cartella)
        else:
            video = Path(argomenti.sorgente).expanduser().resolve()
            if not video.exists():
                print("file non trovato:", video)
                return 1

        info = misura(video)
        print(f"video: {info['larghezza']}×{info['altezza']}, {info['durata']:.2f} s")

        audio = cartella / "audio.wav"
        estrai_audio(video, audio, argomenti.inizio, argomenti.durata)
        durata = info["durata"] - argomenti.inizio
        if argomenti.durata:
            durata = min(durata, argomenti.durata)
        print(f"audio estratto: {durata:.2f} s")

        batteria, basso = separa_steli(audio, cartella)
        mix = leggi(audio)
        drums = leggi(batteria) if batteria else mix
        bassi = leggi(basso) if basso else mix

        scrivi(uscita / "mix.wav", mix, 0.89, argomenti.mono)
        scrivi(uscita / "kick.wav", filtra(drums, CASSA), 0.95, argomenti.mono)
        scrivi(uscita / "bass808.wav", filtra(bassi, BASSO), 0.95, argomenti.mono)
        scrivi(uscita / "hat.wav", filtra(drums, HAT), 0.95, argomenti.mono)

        # La copertina viene da metà brano: lì il montaggio ha già mostrato tutto.
        estrai_copertina(video, uscita / "cover.jpg", argomenti.inizio + durata * 0.5)

    ritmo = conta_colpi(uscita / "kick.wav", uscita / "mix.wav")
    bpm = f"{ritmo['bpm']} BPM, " if ritmo["bpm"] else ""
    print(f"ritmo: {bpm}{ritmo['colpi']} colpi di cassa")

    nomi = ("cover.jpg", "mix.wav", "kick.wav", "bass808.wav", "hat.wav")
    totale = sum((uscita / nome).stat().st_size for nome in nomi)
    print(f"\npacchetto in {uscita} ({totale / 1e6:.1f} MB):")
    for nome in nomi:
        print(f"  {nome:12} {(uscita / nome).stat().st_size / 1e6:6.2f} MB")
    print("\nper provarlo: sostituisci demo/ con questa cartella e apri index.html.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

