# Nastro

Studio audio-reattivo a livelli, nel browser. Ogni livello ha il suo media, il suo
effetto WebGL, la sua forza, la sua opacità e la sua fusione; ogni colpo — kick,
808, snare, hi-hat — accende gli effetti del livello che ascolta quel colpo. Le
tracce audio si mutano, si mettono in solo, entrano in ritardo.

Tutto in un solo `index.html`: niente build, niente dipendenze JS.

## Come si apre

Online: **https://alessandro1040.github.io/nastro/**

In locale, il pacchetto demo viene letto con `fetch()`, quindi conviene un server (con doppio
clic su `index.html` l'app parte lo stesso, ma la demo viene sintetizzata invece
di essere caricata dai file):

```bash
python3 strumenti/serve.py                    # http://127.0.0.1:7870/
python3 strumenti/serve.py --porta 8000       # porta diversa
python3 strumenti/serve.py --senza-browser    # senza aprire il browser
```

Poi: **Carica il pacchetto demo** → **Riproduci**. In alternativa trascini i tuoi
file sullo schermo: immagini e video diventano livelli, gli audio diventano
tracce.

## Come si usa

1. **Carica il pacchetto demo** per avere una scena di partenza: cover, aura e
   titolo, quattro tracce, dodici secondi di timeline.
2. **Aggiungi un livello**: trascina un video o un'immagine sullo schermo, oppure
   usa **+ Video o immagine** nel blocco *Livelli*. Nasce in cima allo stack,
   quindi copre quello che sta sotto; se è un loop su fondo nero mettilo in
   **fusione Schermo** e abbassa l'opacità.
3. **Scegli il livello dallo stack** e dagli un effetto (o lascialo pulito), poi
   **Riproduci**. La durata del progetto è la sorgente più lunga: un video più
   corto si ripete da capo finché la timeline non finisce.
4. **Esporta** con *Registra*: parte dall'inizio, si ferma alla fine e scrive un
   WebM con l'audio che stai sentendo.

Il blocco **Esempi** dell'effetto Neve fa i primi due passi da solo: **Aggiungi al
progetto** mette il loop locale sopra lo stack, già in Schermo. **Ho già il file**
serve se hai scaricato il tuo overlay: diventa un livello normale, con le stesse
manopole degli altri.

## L'interfaccia

**Palco.** La pillola in alto a sinistra è il tempo, quella a destra dice cosa
stai guardando: `A · <effetto>` o `B · <n> livelli`. Sotto: play, ricerca, loop,
prova colpo, registra. Lo spettro in basso mostra l'inviluppo del trigger e i
colpi riconosciuti.

**A/B.** I due chip sopra lo stack isolano la vista senza toccare il progetto:
`A` mostra solo il livello scelto (con il suo effetto, la sua fusione e la sua
opacità), `B` lo stack intero. È l'A/B di un player: stesso punto della timeline,
stesso segnale, una variabile per volta. Da tastiera: `A` e `B`.

**Livelli.** Lo stack si legge dall'alto in basso come l'immagine finale: la riga
in cima è il livello che sta sopra. `↑`/`↓` lo spostano davvero, `●`/`○` lo
spengono senza perderne le impostazioni. Ogni riga mostra miniatura, nome, effetto
e i tre numeri che contano: forza, opacità, fusione. Il primo livello che aggiungi
nasce col Contorno nero; quelli dopo restano puliti, così una scritta o un logo si
sovrappone senza effetti.

**Livello scelto.** Dodici effetti più «Nessun effetto», ognuno con i suoi
parametri; poi forza del livello, attacco (quanto ci mette ad accendersi), opacità,
fusione (normale, somma, schermo, moltiplica) e inquadratura (riempi il frame o
adatta intera).

**Esempi.** L'effetto Neve porta con sé un blocco *Esempi* sotto i parametri: il
loop locale (`demo/neve.mp4`) entra nello stack con un clic, in fusione Schermo e
senza effetto; il riferimento esterno resta lì con miniatura, titolo, canale,
durata, data, categoria e visualizzazioni, più i link al video e alla pagina di
download del canale. Il player parte solo se lo chiedi.

**Trigger.** Sorgente: il mix delle tracce udibili, una traccia sola (anche se è
muta: serve per far pilotare la cassa e tenere il mix muto) oppure il colpo di
prova. Modo impulso o sostenuto, banda (kick 40–170 Hz, 808 25–90 Hz, snare
180 Hz–3 kHz, hat 4,5–10 kHz, tutto), sensibilità, tempo di tenuta, coda e forza
globale.

**Tracce.** `M` muta, `S` mette in solo (con un solo acceso si sentono solo le
tracce in solo), `×` toglie la traccia. Ogni traccia ha il suo volume e il suo
ritardo d'ingresso: la coda di un 808 può entrare due secondi dopo. La durata del
progetto è la traccia più lunga.

**Export.** Risoluzione e fps si scelgono nel pannello. Registra riporta la
timeline all'inizio, sospende il loop e si ferma da sola alla fine: il file esce
in WebM (VP9 + Opus), che è il formato in cui MediaRecorder scrive.

## Come funziona

**Analisi.** Le tracce udibili vengono sommate (rispettando i ritardi) e filtrate
con un passa-banda in un `OfflineAudioContext`; l'energia RMS si calcola ogni 5 ms
su finestre da 20 ms e si normalizza al 99,5° percentile. La soglia è adattiva —
mediana mobile su ±0,8 s, moltiplicata per la sensibilità — con isteresi e durata
minima del colpo. Il risultato va in cache per combinazione di tracce, banda e
sensibilità.

**Renderer.** Un programma GLSL per effetto, tutti con lo stesso contratto:
`uvMedia()` per campionare il media (con il flip Y corretto), `uForza` come
intensità del colpo e `uP0…uP5` come parametri. I livelli si disegnano dal basso
verso l'alto, ognuno nella sua texture; la fusione con l'opacità avviene in una
passata di compositing (normale, somma, schermo, moltiplica). Ogni livello ha il
suo ping-pong di framebuffer, quindi la scia di un livello non sporca gli altri, e
il suo clock, quindi due nevicate possono correre a velocità diverse.

**Media.** La texture di ogni livello resta in cache finché la tela sorgente non
cambia versione (`_telaVersione`): un'immagine si ricarica una volta sola, un video
si aggiorna a ogni fotogramma. Il massimo del Sobel (il 99,5° percentile che
normalizza il Contorno) viene stimato una volta per sorgente su una copia a 256 px,
non a ogni frame.

**Trasporto.** La linea del tempo è un orologio unico, quello del browser, e il
caposaldo si sposta a ogni fotogramma (`inizioTempo`): sommare il tempo trascorso a
un `stato.t` già avanzato lo farebbe correre sempre più forte. I video non vengono
rincorsi a colpi di `currentTime`: se sono un filo indietro li si fa correre un po'
più forte, e si salta solo quando la timeline torna al principio. Così un 4K che
non decodifica in tempo scorre lento ma fluido, invece di ripartire da capo dieci
volte al secondo. Se un contenitore non dichiara la durata (`duration` infinita:
WebM senza indice, MP4 tagliati), si prova a fargliela dire una volta e intanto non
si riavvolge a caso.

**Audio.** Un grafo Web Audio con un bus master: ogni traccia ha guadagno, muto,
solo e ritardo; il master alimenta anche la `MediaStreamDestination` della
registrazione, così il video esportato ha l'audio che stai sentendo.

**Demo.** Se la cartella `demo/` è servita da un server, la demo usa i file veri
(`cover.jpg`, `mix.wav`, `kick.wav`, `bass808.wav`, `hat.wav`); da `file://` la
sintetizza sul momento, così l'app funziona anche con doppio clic.

## Esempi e crediti

Il blocco **Esempi** dell'effetto Neve mostra due cose.

**Neve · loop locale.** `demo/neve.mp4`: 960 × 540, 6 secondi, 30 fps, senza audio.
Lo disegna `strumenti/genera_neve.py` — particelle su tre profondità con
avvolgimento verticale periodico, sprite morbidi in numpy, codifica H.264 via
ffmpeg. Nessun filmato di terzi dentro al progetto.

**Free Snowfall Overlay — 4K Loop-Ready Winter Snow Video Background.** Il
riferimento, con i dati letti dalla pagina pubblica del video (ottobre 2026):

| | |
|---|---|
| Canale | [Enchanted Studios](https://www.youtube.com/@EnchantedStudiosUK) |
| Video | [youtube.com/watch?v=NDV9RovS6U8](https://www.youtube.com/watch?v=NDV9RovS6U8) |
| Durata | 0:10 |
| Pubblicato | 30 settembre 2025 |
| Categoria | Film e animazione |
| Visualizzazioni | 13.876 |

Il file non è nel pacchetto, e non l'ho preso da YouTube: i termini del servizio
non ammettono il download dei video. L'autore però lo distribuisce gratis, anche
per lavori commerciali, dalla sua
[pagina di download](https://www.enchanted.media/downloads/snow-overlay-footage-free-clip/):
prendilo lì, poi nel blocco Esempi usa **Ho già il file** (o trascinalo sullo
schermo) e diventa un livello in fusione Schermo. I crediti restano al canale.

## Tasti

`Spazio` play/pausa · `A` isola il livello scelto · `B` torna allo stack ·
`P` colpo di prova.

## File

```
index.html                 l'app: CSS, markup, Web Audio, shader, export
demo/cover.jpg             copertina 1600×900 generata
demo/neve.mp4              neve su fondo nero, 960×540, 6 s, loop esatto
demo/mix.wav               brano completo (12 s, 120 BPM, 32 kHz)
demo/kick.wav              solo cassa
demo/bass808.wav           solo 808
demo/hat.wav               solo hi-hat
strumenti/genera_demo.py   rigenera demo/ (numpy + Pillow)
strumenti/genera_neve.py   rigenera demo/neve.mp4 (numpy + ffmpeg)
strumenti/serve.py         server statico per l'uso in locale
```

Le tracce sono sintetizzate da `genera_demo.py`, il loop di neve da
`genera_neve.py`: nessun campione né filmato esterno, nessuna licenza da chiedere.

## Limiti

La registrazione gira in tempo reale: se il computer arranca, il file arranca con
lui. La scia e il ping-pong costano memoria in proporzione a risoluzione e numero
di livelli: a 1080p con molti livelli conviene 720p. L'effetto Velocità agisce solo
sui video (sulle immagini non c'è nulla da accelerare) e non tocca l'audio.

