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

1. **Carica il pacchetto demo** per avere una scena di partenza: cover e quattro
   tracce, dodici secondi di timeline. Con `?demo=demo-video` la demo è invece il
   video scomposto in strati (sfondo, buio, immagine, neve): vedi *Da un video al
   pacchetto*.
2. **Aggiungi un livello**: trascina un video o un'immagine sullo schermo, oppure
   usa **+ Video o immagine** nel blocco *Livelli*. Nasce in cima allo stack,
   quindi copre quello che sta sotto; se è un loop su fondo nero mettilo in
   **fusione Schermo** e abbassa l'opacità. Con **×** sulla riga lo elimini.
3. **Scegli il livello dallo stack** e dagli uno o più effetti (o lascialo pulito),
   poi **Riproduci**. La durata del progetto è la sorgente più lunga: un video più
   corto si ripete da capo finché la timeline non finisce.
4. **Esporta** con *Registra*: parte dall'inizio, si ferma alla fine e scrive un
   WebM con l'audio che stai sentendo.

Il blocco **Esempi** dell'effetto Neve porta il riferimento al video del canale:
**Ho già il file** serve se hai scaricato quell'overlay (il file non viaggia col
progetto, i crediti restano a chi l'ha fatto): diventa un livello normale, con le
stesse manopole degli altri.

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
spengono senza perderne le impostazioni, `×` lo elimina (spegne il media, libera
l'URL e toglie la sua texture). Ogni riga mostra miniatura, nome, effetti in
catena e i tre numeri che contano: forza, opacità, fusione. Il primo livello che
aggiungi nasce col Contorno nero; quelli dopo restano puliti, così una scritta o un
logo si sovrappone senza effetti.

**Livello scelto.** Dodici effetti più «Nessun effetto», ognuno con i suoi
parametri; poi forza del livello, attacco (quanto ci mette ad accendersi), opacità,
fusione (normale, somma, schermo, moltiplica) e inquadratura (riempi il frame o
adatta intera).

**Catena.** La griglia degli effetti è un interruttore: ogni clic aggiunge
l'effetto in fondo alla catena (col numero della posizione sul bottone), un altro
lo toglie. Sopra la griglia l'elenco ordinato dice chi viene prima e chi dopo,
con `↑`/`↓` per cambiare l'ordine e `×` per togliere un passaggio. Il secondo
effetto legge il risultato del primo, quindi **Neve → Tremolio** non è **Tremolio
→ Neve**; i parametri restano quelli di ogni effetto, e il tetto è quattro
passaggi. «Nessun effetto» svuota la catena.

**Esempi.** L'effetto Neve porta con sé un blocco *Esempi* sotto i parametri: il
riferimento esterno con miniatura, titolo, canale, durata, data, categoria e
visualizzazioni, più i link al video e alla pagina di download del canale. Il
player parte solo se lo chiedi. Il file non è nel progetto.

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
verso l'alto, ognuno nella sua texture. Se un livello ha più effetti, la catena
gira in ping-pong su due bersagli: il primo passaggio legge il media, ognuno dei
successivi legge il risultato del precedente, e solo l'ultimo va in compositing
(normale, somma, schermo, moltiplica) con l'opacità. Ogni livello ha anche il suo
ping-pong per la scia, quindi non sporca gli altri, e il suo clock, quindi due
nevicate possono correre a velocità diverse.

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
sintetizza sul momento, così l'app funziona anche con doppio clic. Se il manifesto
del pacchetto elenca `livelli`, al posto della base si monta quella pila; uno
strato può dichiarare una `fonte` esterna (il video della neve su YouTube) e, se
il file non c'è, al suo posto compare una carta che chiede di caricarlo: appena
arriva entra nello stack con gli stessi parametri.

## Esempi e crediti

Il blocco **Esempi** dell'effetto Neve mostra il riferimento al video, e nient'altro:
il file non viaggia col progetto, così i crediti restano a chi l'ha fatto.

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
demo/mix.wav               brano completo (12 s, 120 BPM, 32 kHz)
demo/kick.wav              solo cassa
demo/bass808.wav           solo 808
demo/hat.wav               solo hi-hat
strumenti/genera_demo.py   rigenera demo/ (numpy + Pillow)
strumenti/pacchetto_da_video.py  costruisce un pacchetto da un tuo filmato
strumenti/serve.py         server statico per l'uso in locale
```

Le tracce sono sintetizzate da `genera_demo.py`: nessun campione esterno, nessuna
licenza da chiedere. L'unico filmato di terzi che l'app cita è l'overlay di neve,
e resta sul sito del suo autore.

## Da un video al pacchetto

Se hai già un filmato con il tuo brano, `pacchetto_da_video.py` ne ricava tutto
quello che serve al trigger:

```
python3 strumenti/pacchetto_da_video.py mio-video.mp4 --uscita demo-video
python3 strumenti/pacchetto_da_video.py "https://youtu.be/…" --uscita demo-video --mono
```

Demucs (se installato) separa batteria e basso, poi lo strumento filtra la cassa
(30–170 Hz), l'808 (25–250 Hz) e gli hi-hat (sopra i 6 kHz), riscrive tutto a
32 kHz come il pacchetto di serie, prende un fotogramma a metà brano per la
copertina e copia il filmato a 720p senza audio in `filmato.mp4`. `--mono`
dimezza lo spazio, `--inizio`/`--durata` tagliano una parte, `--senza-filmato`
lascia solo le tracce, `--altezza 540` alleggerisce il video.

Con la scomposizione, il manifesto elenca una pila di quattro strati dal fondo
alla cima: `sfondo.jpg` (il fondale senza l'opera), `buio.png` (un nero che entra
solo sul colpo), `immagine.png` (l'opera ritagliata, con `effetti: ["tremolio"]`)
e `neve.mp4`. La neve non è un surrogato disegnato in casa: lo strato dichiara la
`fonte` (il video di Enchanted Studios su YouTube, con pagina e download) e il
file non viaggia col pacchetto. Se `neve.mp4` non c'è, l'app mostra sotto lo stack
una carta che lo chiede: **Carica il file** e lo strato entra al suo posto, con
`reattivo: 0.94` e fusione Schermo, quindi la neve compare solo sul colpo. Non
c'è nessun titolo aggiunto in automatico: la pila è solo quello che si vede.

Per provare un pacchetto senza toccare `demo/`, la cartella si sceglie
dall'indirizzo:

```
demo-video/                      # dentro il progetto, ignorata da git
python3 strumenti/serve.py
# poi apri http://127.0.0.1:7870/?demo=demo-video
```

Senza parametri l'app carica `demo/`. `demo-video/` sta nel `.gitignore` perché
un pacchetto fatto da un video può contenere un brano che non è tuo: in locale
sì, sul sito pubblicato no.

Un avvertimento onesto: dal video **non** si ricavano gli strati veri. Un filmato
già montato è un'immagine sola (più zoom e particelle, se ci sono), quindi lo
strumento separa quello che un fotogramma permette — l'opera dal fondale, il nero
da accendere sul colpo — e la neve resta il video del suo autore, caricato a mano.


## Limiti

La registrazione gira in tempo reale: se il computer arranca, il file arranca con
lui. La scia e il ping-pong costano memoria in proporzione a risoluzione e numero
di livelli: a 1080p con molti livelli conviene 720p. L'effetto Velocità agisce solo
sui video (sulle immagini non c'è nulla da accelerare) e non tocca l'audio.


## Pubblicazione

Il sito è su GitHub Pages (ramo `main`, radice del repo):
**https://alessandro1040.github.io/nastro/**

Per aggiornarlo basta un push:

```bash
git add -A && git commit -m "cosa cambia" && git push
```

Pages ricostruisce da solo in un minuto circa. Il file `.nojekyll` evita che Jekyll
tocchi la pagina; tutti i percorsi sono relativi, quindi l'app funziona sia in
locale sia nella sottocartella di Pages.
