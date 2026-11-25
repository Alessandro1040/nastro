#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Da un brano (e due immagini) al pacchetto demo di Nastro.

    python3 strumenti/demo_da_brano.py brano.mp3 \\
        --cover opera.jpeg --sfondo fondale.jpeg --uscita demo

Scrive nella cartella indicata, con i nomi che l'app si aspetta:

    cover.jpg     l'opera in primo piano (l'immagine che trema sul colpo)
    sfondo.jpg    il fondale, se lo passi: altrimenti resta solo l'opera
    buio.png      un nero pieno: l'app lo accende solo sul colpo
    mix.wav       l'estratto del brano
    kick.wav      la cassa isolata
    bass808.wav   il basso/808 isolato
    hat.wav       gli hi-hat isolati
    pacchetto.json  il manifesto: durata, BPM, colpi, pila dei livelli

Come lavora: prende un estratto (di serie 16 s, dalla finestra con più cassa nel
brano), separa batteria e basso con demucs, filtra le bande che l'app ascolta,
riscrive tutto a 32 kHz mono come il pacchetto che sta in `demo/`, e legge i
colpi dalle tracce separate. Le immagini si ridimensionano: l'opera a 1200 × 1200,
il fondale a 1280 × 720.

Il manifesto monta la pila dal fondo alla cima — sfondo, buio, opera — con gli
stessi numeri del pacchetto pubblicato: il buio al 42% che si accende sul colpo,
l'opera in «adatta intera» con Tremolio e Saturazione. Senza `--sfondo` la pila è
buio + opera, e sotto resta il nero del palco. Con `--con-fuoco` entrano anche il
velo di fuoco e la neve, come nella demo di serie: i due mp4 non si scrivono qui,
restano in `demo-video/`, e lo strato ne dichiara la fonte.

Le dipendenze sono quelle di `pacchetto_da_video.py`: ffmpeg, numpy, scipy,
soundfile e Pillow; demucs, se c'è, separa davvero batteria e basso.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pacchetto_da_video as pv  # noqa: E402

LATO_OPERA = 1200
FONDO = (1280, 720)


def scegli_inizio(brano: Path, durata: float) -> float:
    """Il secondo da cui parte l'estratto: la finestra con più cassa dentro."""
    dati = pv.leggi(brano).mean(axis=1)
    inviluppo = pv.inviluppo(pv.filtra(dati[:, None], pv.CASSA), passo=0.01).ravel()
    passo = 0.01
    finestra = int(round(durata / passo))
    if len(inviluppo) <= finestra:
        return 0.0
    cumulo = np.concatenate([[0.0], np.cumsum(inviluppo)])
    totali = cumulo[finestra:] - cumulo[:-finestra]
    return round(int(np.argmax(totali)) * passo, 2)


def prepara_opera(immagine: Path, destinazione: Path) -> None:
    """L'opera in un JPEG quadrato: il livello la mostra intera dentro il frame."""
    with Image.open(immagine) as foto:
        opera = foto.convert("RGB")
    opera = opera.resize((LATO_OPERA, LATO_OPERA), Image.LANCZOS)
    opera.save(destinazione, "JPEG", quality=88, optimize=True, progressive=True)


def prepara_fondale(immagine: Path, destinazione: Path) -> None:
    """Il fondale a 1280 × 720: se l'immagine non ha quel formato, si ritaglia."""
    with Image.open(immagine) as foto:
        fondale = foto.convert("RGB")
    proporzione = FONDO[0] / FONDO[1]
    larghezza, altezza = fondale.size
    if larghezza / altezza > proporzione:
        nuova = int(round(altezza * proporzione))
        margine = (larghezza - nuova) // 2
        fondale = fondale.crop((margine, 0, margine + nuova, altezza))
    else:
        nuova = int(round(larghezza / proporzione))
        margine = (altezza - nuova) // 2
        fondale = fondale.crop((0, margine, larghezza, margine + nuova))
    fondale = fondale.resize(FONDO, Image.LANCZOS)
    fondale.save(destinazione, "JPEG", quality=86, optimize=True, progressive=True)


def prepara_nero(destinazione: Path) -> None:
    """Il buio è un PNG minuscolo: l'app lo riempie sul frame e lo accende sul colpo."""
    Image.new("RGB", (32, 32), (0, 0, 0)).save(destinazione, "PNG", optimize=True)


def prepara_tracce(brano: Path, uscita: Path, lavoro: Path, inizio: float,
                   durata: float) -> dict:
    """L'estratto, le quattro tracce a 32 kHz mono e i colpi del trigger."""
    estratto = lavoro / "estratto.wav"
    pv.comando("ffmpeg", "-y", "-v", "error", "-ss", str(inizio), "-i", str(brano),
               "-t", str(durata), "-vn", "-ac", "2", "-ar", str(pv.SR_SORGENTE),
               str(estratto))
    print(f"estratto da {inizio:.2f} s per {durata:.0f} s")

    batteria, basso = pv.separa_steli(estratto, lavoro / "stems")
    mix = pv.leggi(estratto)
    drums = pv.leggi(batteria) if batteria else mix
    bassi = pv.leggi(basso) if basso else mix

    pv.scrivi(uscita / "mix.wav", mix, 0.85, True)
    pv.scrivi(uscita / "kick.wav", pv.filtra(drums, pv.CASSA), 0.95, True)
    pv.scrivi(uscita / "bass808.wav", pv.filtra(bassi, pv.BASSO), 0.95, True)
    pv.scrivi(uscita / "hat.wav", pv.filtra(drums, pv.HAT), 0.95, True)

    ritmo = pv.conta_colpi(uscita / "kick.wav", uscita / "mix.wav")
    eventi = pv.colpi_trigger(uscita / "kick.wav", uscita / "bass808.wav",
                              uscita / "mix.wav")
    print(f"ritmo: {ritmo['bpm']} BPM, {ritmo['colpi']} colpi · "
          + ", ".join(f"{len(v)} sulla banda {k}" for k, v in eventi.items()))
    return {"bpm": ritmo["bpm"], "colpi": ritmo["colpi"], "eventi": eventi,
            "inizio": inizio}


FUOCO_VIDEO = "sfondo-fuoco.mp4"
FUOCO_FONTE = {
    "tipo": "youtube",
    "videoId": "5jqPvtdGoUU",
    "titolo": "Burning Fire Background | 30 minutes | 4K screensaver loops",
    "canale": "Boss of Screensavers",
    "url": "https://www.youtube.com/watch?v=5jqPvtdGoUU",
    "nota": "estratto da 0:24, bianco e nero, 3840x2160, loop di 58,27 s",
}


def strati(banda: str, con_fondale: bool, con_fuoco: bool = False) -> list[dict]:
    """La pila dal fondo alla cima: sfondo, fuoco, buio, neve, opera.

    Gli stessi numeri del pacchetto pubblicato: il buio al 42% si accende sul
    colpo e resta giù finché suona l'808 (`finoAlSuono`); l'opera sta in «adatta
    intera», quindi una foto quadrata resta tutta dentro il frame 1280 × 720, e
    sul colpo trema e prende un po' di saturazione.

    Con `con_fuoco` la pila è quella del pacchetto video: dopo lo sfondo il velo
    di fuoco all'8% in fusione Schermo e, dopo il buio, la neve reattiva. I due
    mp4 non si scrivono qui — sono i video esterni che stanno in `demo-video/`:
    lo strato dichiara la `fonte`, e Nastro il file lo cerca nella cartella del
    pacchetto, poi in `demo-video/`, poi allo scaricatore; se non lo trova lascia
    la carta che lo chiede.
    """
    pila: list[dict] = []
    if con_fondale:
        pila.append({"file": "sfondo.jpg", "nome": "Sfondo", "effetti": [],
                     "opacita": 1.0, "banda": banda, "adatta": 0})
    if con_fuoco:
        pila.append({"file": FUOCO_VIDEO, "nome": "Fuoco · velo", "effetti": [],
                     "fusione": "schermo", "opacita": 0.08, "banda": banda,
                     "fonte": FUOCO_FONTE, "adatta": 0})
    pila.append({"file": "buio.png", "nome": "Buio sul colpo", "effetti": [],
                 "opacita": 0.42, "reattivo": 1.0, "attacco": 0.01,
                 "finoAlSuono": True, "banda": banda, "adatta": 0})
    if con_fuoco:
        pila.append({"file": pv.NEVE_VIDEO, "nome": "Neve", "effetti": [],
                     "fusione": "schermo", "opacita": 1.0, "reattivo": 1.0,
                     "finoAlSuono": True, "attacco": 0.02, "banda": banda,
                     "fonte": pv.NEVE_FONTE, "adatta": 0})
    pila.append({"file": "cover.jpg", "nome": "Cover",
                 "effetti": ["tremolio", "saturo"], "opacita": 1.0, "forza": 0.85,
                 "attacco": 0.008, "banda": banda, "scelto": True, "adatta": 1,
                 "parametri": {"tremolio": {"ampiezza": 0.9, "scatti": 24},
                               "saturo": {"sat": 0.35}}})
    return pila


def scrivi_manifesto(uscita: Path, etichetta: str, ritmo: dict,
                     con_fondale: bool, con_fuoco: bool = False) -> None:
    import soundfile as sf

    durata = float(sf.info(str(uscita / "mix.wav")).duration)
    banda = "cassa808"
    manifesto = {
        "nome": uscita.name,
        "sorgente": (etichetta +
                     f", estratto da {ritmo['inizio']:.2f} s per {durata:.2f} s"),
        "durata": round(durata, 3),
        "bpm": ritmo["bpm"],
        "colpi": ritmo["colpi"],
        "filmato": None,
        "banda": banda,
        "livelli": strati(banda, con_fondale, con_fuoco),
    }
    if ritmo["eventi"]:
        manifesto["eventi"] = ritmo["eventi"]
    pv.scrivi_manifesto(uscita / "pacchetto.json", manifesto)
    print(f"manifesto: {durata:.2f} s, {ritmo['bpm']} BPM, "
          f"{len(ritmo['eventi'].get(banda, []))} colpi sulla banda {banda}")


def main() -> int:
    argomenti = argparse.ArgumentParser(
        description="Da un brano (e due immagini) al pacchetto demo di Nastro.")
    argomenti.add_argument("brano", help="file audio (o video: l'audio si estrae)")
    argomenti.add_argument("--cover", required=True,
                           help="immagine dell'opera: diventa cover.jpg")
    argomenti.add_argument("--sfondo", default=None,
                           help="immagine del fondale: diventa sfondo.jpg (facoltativa)")
    argomenti.add_argument("--uscita", default="demo-remix",
                           help="cartella di destinazione (default demo-remix)")
    argomenti.add_argument("--inizio", type=float, default=None,
                           help="secondo da cui partire (default: la finestra con più cassa)")
    argomenti.add_argument("--durata", type=float, default=16.0,
                           help="quanti secondi tenere (default 16)")
    argomenti.add_argument("--sorgente", default=None,
                           help="come si chiama la sorgente nel manifesto "
                                "(default: il nome del file)")
    argomenti.add_argument("--con-fuoco", action="store_true",
                           help="aggiunge il velo di fuoco e la neve alla pila "
                                "(i due mp4 si prendono da demo-video/)")
    scelte = argomenti.parse_args()

    brano = Path(scelte.brano)
    cover = Path(scelte.cover)
    fondale = Path(scelte.sfondo) if scelte.sfondo else None
    for percorso in [brano, cover] + ([fondale] if fondale else []):
        if not percorso.exists():
            print(f"manca {percorso}", file=sys.stderr)
            return 2

    uscita = Path(scelte.uscita)
    uscita.mkdir(parents=True, exist_ok=True)
    lavoro = Path(tempfile.mkdtemp(prefix="nastro-brano-"))
    try:
        prepara_opera(cover, uscita / "cover.jpg")
        if fondale:
            prepara_fondale(fondale, uscita / "sfondo.jpg")
        prepara_nero(uscita / "buio.png")

        pv.estrai_audio(brano, lavoro / "intero.wav", 0.0, None)
        inizio = (scelte.inizio if scelte.inizio is not None
                  else scegli_inizio(lavoro / "intero.wav", scelte.durata))
        ritmo = prepara_tracce(brano, uscita, lavoro, inizio, scelte.durata)
        scrivi_manifesto(uscita, scelte.sorgente or brano.name, ritmo, bool(fondale),
                         scelte.con_fuoco)
    finally:
        shutil.rmtree(lavoro, ignore_errors=True)

    nomi = ["cover.jpg", "sfondo.jpg", "buio.png", "pacchetto.json",
            "mix.wav", "kick.wav", "bass808.wav", "hat.wav"]
    presenti = [nome for nome in nomi if (uscita / nome).exists()]
    totale = sum((uscita / nome).stat().st_size for nome in presenti)
    print(f"\npacchetto in {uscita} ({totale / 1e6:.2f} MB):")
    for nome in presenti:
        print(f"  {nome:13} {(uscita / nome).stat().st_size / 1e6:6.2f} MB")
    print(f"\nper provarlo: python3 strumenti/serve.py e apri "
          f"http://127.0.0.1:7870/?demo={uscita}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
