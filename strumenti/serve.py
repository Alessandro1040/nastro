#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Server statico per aprire Nastro in locale.

Serve solo la cartella del progetto: l'app carica il pacchetto demo con fetch(),
quindi il doppio clic su index.html non basta e va aperta da qui.

Uso:
    python3 strumenti/serve.py                  # http://127.0.0.1:7870/
    python3 strumenti/serve.py --porta 8000
    python3 strumenti/serve.py --senza-browser
    PORT=7870 python3 strumenti/serve.py        # porta da variabile d'ambiente

Non serve per pubblicare: è un http.server con i tipi MIME giusti per i file
audio/video e senza cache, così mentre si modifica l'app si ricarica subito.
"""

from __future__ import annotations

import argparse
import functools
import http.server
import os
import socketserver
import sys
import threading
import webbrowser
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
PORTA_PREDEFINITA = 7870

# http.server non conosce alcuni dei formati che l'app registra con MediaRecorder.
TIPI = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".webm": "video/webm",
    ".ico": "image/x-icon",
}


class Gestore(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler con MIME extra e niente cache."""

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, formato: str, *argomenti: object) -> None:
        # Log breve: interessa solo sapere quale file è stato servito.
        sys.stderr.write("  %s\n" % (formato % argomenti))
        sys.stderr.flush()


class Server(socketserver.ThreadingTCPServer):
    """ThreadingTCPServer che riusa la porta subito dopo un riavvio."""

    allow_reuse_address = True
    daemon_threads = True


def apri_browser(url: str) -> None:
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()


def main() -> int:
    analizzatore = argparse.ArgumentParser(
        description="Serve Nastro su http://127.0.0.1 (default porta 7870)."
    )
    analizzatore.add_argument(
        "-p", "--porta", type=int,
        default=int(os.environ.get("PORT", PORTA_PREDEFINITA)),
        help="porta di ascolto (default %d, oppure la variabile PORT)" % PORTA_PREDEFINITA,
    )
    analizzatore.add_argument(
        "--senza-browser", action="store_true",
        help="non aprire il browser all'avvio",
    )
    argomenti = analizzatore.parse_args()

    if not (RADICE / "index.html").is_file():
        print("ERRORE: non trovo %s" % (RADICE / "index.html"), file=sys.stderr)
        return 1

    indirizzo = "127.0.0.1"
    url = "http://%s:%d/" % (indirizzo, argomenti.porta)
    gestore = functools.partial(Gestore, directory=str(RADICE))
    for estensione, tipo in TIPI.items():
        Gestore.extensions_map[estensione] = tipo

    try:
        with Server((indirizzo, argomenti.porta), gestore) as server:
            print("Nastro su %s" % url)
            print("  cartella: %s" % RADICE)
            print("  ferma con Ctrl+C")
            if not argomenti.senza_browser:
                apri_browser(url)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\n  server fermato")
    except OSError as errore:
        print("ERRORE: non riesco ad aprire la porta %d (%s)." % (argomenti.porta, errore),
              file=sys.stderr)
        print("        Prova un'altra porta: python3 strumenti/serve.py --porta 8000",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
