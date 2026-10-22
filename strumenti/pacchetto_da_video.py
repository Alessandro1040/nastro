#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Da un video (file o link YouTube) al pacchetto demo di Nastro.

    python3 strumenti/pacchetto_da_video.py video.mp4 --uscita demo-mio
    python3 strumenti/pacchetto_da_video.py "https://youtu.be/XXXX" --uscita demo-mio

Scrive nella cartella indicata, con i nomi che l'app si aspetta:

    cover.jpg     un fotogramma del video (l'immagine di partenza)
    filmato.mp4   il video stesso, 720p H.264 senza audio
    sfondo.jpg    il fotogramma sfocato e spento: il fondo della scena
    immagine.png  l'opera ritagliata, col resto trasparente: è lo strato che trema
    buio.png      un nero pieno: l'app lo accende solo sul colpo
    mix.wav       il brano completo, come sta nel video
    kick.wav      la cassa isolata
    bass808.wav   il basso/808 isolato
    hat.wav       gli hi-hat isolati
    pacchetto.json  il manifesto: durata, BPM, colpi, pila dei livelli

Come lavora:

  1. scarica (solo se il link è un URL) e misura il file con ffprobe;
  2. tira fuori l'audio, poi chiama demucs per separare batteria e basso dal
     resto: se demucs non c'è, ripiega sulle bande del mix;
  3. filtra le bande giuste e riscrive tutto a 32 kHz, come il pacchetto che
     sta in demo/;
  4. prende un fotogramma a metà brano per la copertina;
  5. copia il filmato a 720p senza audio;
  6. scompone un fotogramma in strati: trova il riquadro dell'opera (la parte
     netta dentro il fondo sfocato), la ritaglia su un PNG trasparente, sfoca e
     spegne il resto per farne lo sfondo, aggiunge un nero da accendere sul
     colpo. Il manifesto elenca la pila con i valori di partenza: sfondo fermo,
     buio reattivo, immagine che trema sul colpo, neve sul colpo.

La neve sul colpo non si disegna in casa: lo strato cita il video che l'autore
pubblica su YouTube (canale, pagina, download) e il file non viaggia col
pacchetto. Se non c'è, l'app mostra la carta che chiede di caricarlo e lo mette
al suo posto; il titolo non viene aggiunto in automatico. La scomposizione
riguarda quello che un fotogramma permette, cioè l'opera e il fondo. Se il video
è già pieno schermo non c'è nessun riquadro da ritagliare, e il pacchetto resta
col solo filmato (o con --senza-strati).
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


def prepara_filmato(
    video: Path, destinazione: Path, inizio: float, durata: float | None, altezza: int
) -> None:
    """Il video in una forma che il browser apre senza sorprese: H.264, niente audio.

    L'audio del filmato non serve: le tracce del pacchetto lo sostituiscono, e
    tenerlo dentro significherebbe due brani sovrapposti.
    """
    parti = ["ffmpeg", "-y", "-v", "error", "-ss", str(inizio), "-i", str(video)]
    if durata:
        parti += ["-t", str(durata)]
    parti += [
        "-an", "-vf", f"scale=-2:{altezza}",
        "-c:v", "libx264", "-crf", "28", "-preset", "slow", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(destinazione),
    ]
    comando(*parti)


# ---------------------------------------------------------------- strati ---
def leggi_fotogramma(video: Path, quando: float, larghezza: int = 480) -> np.ndarray:
    """Un fotogramma in scala di grigi, ridotto: serve solo a trovare i bordi."""
    esito = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{quando:.3f}", "-i", str(video),
         "-frames:v", "1", "-vf", f"scale={larghezza}:-2", "-pix_fmt", "gray",
         "-f", "rawvideo", "-"],
        capture_output=True,
    )
    if esito.returncode != 0 or not esito.stdout:
        messaggio = esito.stderr.decode("utf-8", "replace")[:200]
        raise RuntimeError("ffmpeg non ha dato il fotogramma: " + messaggio)
    altezza = len(esito.stdout) // larghezza
    fotogramma = np.frombuffer(esito.stdout, dtype=np.uint8)[: altezza * larghezza]
    return fotogramma.reshape(altezza, larghezza)


def trova_riquadro(fotogramma: np.ndarray) -> tuple[int, int, int, int] | None:
    """Il rettangolo della carta (l'immagine incorniciata) dentro il fotogramma.

    Il montaggio tipico di questi video è un poster fermo e netto sopra uno
    sfondo sfocato: la cornice è un salto di luminanza verticale e orizzontale,
    quindi si guardano i profili medi delle colonne e delle righe e si prende il
    primo salto forte partendo dal margine. Non il più forte: sulla cornice
    dorata i salti si ripetono a raggiera e il massimo cade dentro l'immagine.
    Il rettangolo si allarga poi di qualche pixel, perché un filo di sfondo ai
    bordi è meglio di una cornice tagliata. Se il risultato non è credibile —
    video già pieno schermo, rettangolo troppo piccolo, nessun salto di
    luminanza — torna None: non c'è niente da scomporre.
    """
    alto, largo = fotogramma.shape
    if alto < 8 or largo < 8:
        return None
    grigio = fotogramma.astype(np.float32)
    salto_col = np.abs(np.diff(grigio.mean(axis=0)))
    salto_riga = np.abs(np.diff(grigio.mean(axis=1)))
    if salto_col.size < 2 or salto_riga.size < 2:
        return None

    def primo_bordo(salti: np.ndarray, da_sinistra: bool) -> int | None:
        soglia = max(6.0, float(salti.max()) * 0.3)
        indici = range(len(salti)) if da_sinistra else range(len(salti) - 1, -1, -1)
        return next((i for i in indici if salti[i] >= soglia), None)

    bordi = (primo_bordo(salto_col, True), primo_bordo(salto_riga, True),
             primo_bordo(salto_col, False), primo_bordo(salto_riga, False))
    if any(b is None for b in bordi):
        return None
    sinistra, sopra, destra, sotto = (int(b) for b in bordi)

    margine = max(2, round(largo * 0.004))
    x0, y0 = max(0, sinistra - margine), max(0, sopra - margine)
    x1, y1 = min(largo, destra + 1 + margine), min(alto, sotto + 1 + margine)
    larghezza, altezza = x1 - x0, y1 - y0

    if larghezza < largo * 0.25 or altezza < alto * 0.25:
        return None
    if larghezza > largo * 0.99 or altezza > alto * 0.99:
        return None
    if not 0.8 <= larghezza / altezza <= 1.25:
        return None

    # Dentro e fuori devono essere due luminanze diverse, altrimenti il
    # rettangolo è solo la zona più movimentata di un video pieno schermo.
    dentro = float(grigio[y0:y1, x0:x1].mean())
    fuori = np.concatenate([grigio[:, :x0].ravel(), grigio[:, x1:].ravel()])
    if not fuori.size or min(dentro, fuori.mean()) <= 0:
        return None
    if min(dentro, fuori.mean()) / max(dentro, fuori.mean()) > 0.92:
        return None

    return x0, y0, larghezza, altezza


def prepara_strati(
    video: Path,
    cartella: Path,
    quando: float,
    riquadro: tuple[int, int, int, int],
    larghezza: int,
    altezza: int,
) -> None:
    """Scompone il fotogramma in tre file che l'app impila da sola.

    sfondo.jpg    il margine del fotogramma, stirato su tutto il quadro: il
                  fondale del video senza l'opera dentro (sfocare il fotogramma
                  intero lascerebbe l'opera doppia, dietro la sua copia);
    immagine.png  l'opera ritagliata con la sua cornice, col resto trasparente;
    buio.png      un nero pieno: l'app lo accende solo sul colpo (reattivo).
    """
    x, y, w, h = riquadro
    # La fascia a sinistra dell'opera è fondale puro: la stiro su tutto, la
    # riduco a una manciata di pixel e la rimetto in grande, che è il modo più
    # economico di sfocarla senza lasciare struttura.
    fascia = max(8, x - 12)
    spunto = max(2, round(80 * altezza / larghezza))
    comando(
        "ffmpeg", "-y", "-v", "error", "-ss", f"{quando:.3f}", "-i", str(video),
        "-frames:v", "1", "-vf",
        f"scale={larghezza}:{altezza},crop={fascia}:{altezza}:0:0,"
        f"scale=80:{spunto},scale={larghezza}:{altezza}:flags=bicubic,"
        f"gblur=sigma={max(8, round(altezza / 40))},"
        f"eq=brightness=-0.10:saturation=0.80",
        "-q:v", "4", str(cartella / "sfondo.jpg"),
    )
    comando(
        "ffmpeg", "-y", "-v", "error", "-ss", f"{quando:.3f}", "-i", str(video),
        "-filter_complex",
        f"[0:v]scale={larghezza}:{altezza},format=rgba,crop={w}:{h}:{x}:{y},"
        f"pad={larghezza}:{altezza}:{x}:{y}:color=black@0[fuori]",
        "-map", "[fuori]", "-frames:v", "1", "-pix_fmt", "rgba",
        str(cartella / "immagine.png"),
    )
    comando(
        "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=32x32",
        "-frames:v", "1", str(cartella / "buio.png"),
    )


NEVE_VIDEO = "neve.mp4"
NEVE_FONTE = {
    "tipo": "youtube",
    "videoId": "NDV9RovS6U8",
    "titolo": "Free Snowfall Overlay — 4K Loop-Ready Winter Snow Video Background",
    "canale": "Enchanted Studios",
    "url": "https://www.youtube.com/watch?v=NDV9RovS6U8",
    "download": "https://www.enchanted.media/downloads/snow-overlay-footage-free-clip/",
}


def livelli_demo() -> list[dict]:
    """La pila che l'app monta per un pacchetto scomposto, dal fondo alla cima.

    Lo sfondo è il fondale del video, senza l'opera dentro; il buio è un nero che
    entra solo sul colpo, così la scena si spegne sul kick e sull'808; l'immagine
    ritagliata trema sul colpo; la neve sul colpo è il video esterno pubblicato su
    YouTube, non un surrogato disegnato in casa: il file non viaggia col pacchetto
    (i crediti restano al canale), quindi in "fonte" ci sono pagina e download, e
    se manca l'app mostra la carta che chiede di caricarlo. Niente titolo: non si
    aggiunge più niente che non sia nel video.
    """
    banda = "cassa808"
    return [
        {"file": "sfondo.jpg", "nome": "Sfondo", "effetti": [],
         "opacita": 1.0, "banda": banda},
        {"file": "buio.png", "nome": "Buio sul colpo", "effetti": [],
         "opacita": 0.86, "reattivo": 1.0, "attacco": 0.01, "banda": banda},
        {"file": "immagine.png", "nome": "Immagine", "effetti": ["tremolio"],
         "opacita": 1.0, "forza": 0.85, "attacco": 0.008, "banda": banda,
         "scelto": True,
         "parametri": {"tremolio": {"ampiezza": 0.9, "scatti": 24}}},
        {"file": NEVE_VIDEO, "nome": "Neve sul colpo", "effetti": [],
         "fusione": "schermo", "opacita": 0.95, "reattivo": 0.94, "attacco": 0.01,
         "banda": banda, "fonte": NEVE_FONTE},
    ]


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
    argomenti.add_argument("--senza-filmato", action="store_true",
                           help="niente video nel pacchetto: solo tracce e copertina")
    argomenti.add_argument("--senza-strati", action="store_true",
                           help="niente scomposizione: solo filmato e copertina, "
                                "senza sfondo/immagine/buio")
    argomenti.add_argument("--altezza", type=int, default=720,
                           help="altezza del filmato e degli strati (default 720)")
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

        if not argomenti.senza_filmato:
            prepara_filmato(video, uscita / "filmato.mp4",
                            argomenti.inizio, argomenti.durata, argomenti.altezza)
            print(f"filmato: {argomenti.altezza}p, senza audio")

        # La scomposizione: se il video è un'immagine sopra un fondo sfocato, la
        # ritaglio e la impilo; se non lo è, resta il solo filmato.
        strati = False
        if not argomenti.senza_strati:
            quando = argomenti.inizio + durata * 0.5
            try:
                fotogramma = leggi_fotogramma(video, quando)
                scala = argomenti.altezza / max(1, info["altezza"])
                larghezza = int(round(info["larghezza"] * scala / 2)) * 2
                riquadro = trova_riquadro(fotogramma)
                if riquadro:
                    k = larghezza / fotogramma.shape[1]
                    x, y, w, h = (round(v * k) for v in riquadro)
                    x = max(0, min(x, larghezza - w))
                    y = max(0, min(y, argomenti.altezza - h))
                    prepara_strati(video, uscita, quando, (x, y, w, h),
                                   larghezza, argomenti.altezza)
                    strati = True
                    print(f"strati: immagine {w}×{h} dentro {larghezza}×{argomenti.altezza}, "
                          f"sfondo sfocato e buio sul colpo")
                else:
                    print("strati: nessuna immagine riconoscibile, resta il solo filmato")
            except RuntimeError as errore:
                print("strati non riusciti:", errore)

    ritmo = conta_colpi(uscita / "kick.wav", uscita / "mix.wav")
    bpm = f"{ritmo['bpm']} BPM, " if ritmo["bpm"] else ""
    print(f"ritmo: {bpm}{ritmo['colpi']} colpi di cassa")

    # Il manifesto serve all'app per sapere com'è fatto il pacchetto senza
    # indovinare: se non c'è, resta valido il comportamento di sempre. Con
    # "livelli" l'app monta la pila scomposta invece di usare il filmato intero.
    manifesto = {
        "nome": uscita.name,
        "sorgente": argomenti.sorgente,
        "durata": round(durata, 3),
        "bpm": ritmo["bpm"],
        "colpi": ritmo["colpi"],
        "filmato": None if argomenti.senza_filmato else "filmato.mp4",
    }
    if strati:
        manifesto["banda"] = "cassa808"
        manifesto["livelli"] = livelli_demo()
    (uscita / "pacchetto.json").write_text(
        json.dumps(manifesto, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    nomi = ["cover.jpg"]
    if (uscita / "filmato.mp4").exists():
        nomi.append("filmato.mp4")
    if strati:
        nomi += ["sfondo.jpg", "immagine.png", "buio.png"]
    nomi += ["mix.wav", "kick.wav", "bass808.wav", "hat.wav"]
    totale = sum((uscita / nome).stat().st_size for nome in nomi)
    print(f"\npacchetto in {uscita} ({totale / 1e6:.1f} MB):")
    for nome in nomi:
        print(f"  {nome:13} {(uscita / nome).stat().st_size / 1e6:6.2f} MB")
    print("\nper provarlo:"
          f"\n  cp -R \"{uscita}\" demo-video   # dentro il progetto"
          "\n  python3 strumenti/serve.py e apri http://127.0.0.1:7870/?demo=demo-video"
          "\n(oppure sostituisci demo/ e apri index.html senza parametri)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

