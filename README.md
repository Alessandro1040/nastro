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
tracce. Per i brani interi del sito (non l'estratto della demo) serve anche il sito
acceso, nella sua cartella: `python3 strumenti/serve.py`, porta 7862 — è
l'indirizzo che il pannello *Brani dal sito* si aspetta.

## Come si usa

1. **Carica il pacchetto demo** per avere una scena di partenza: la cover della
   Remixes Collection Vol. 3 sopra lo sfondo, con il velo di fuoco e la neve che
   stanno in `demo-video/`, sedici secondi di timeline e quattro tracce (il mix e le
   tre mute che guidano il trigger). Sono gli stessi cinque strati dello stack
   composto, montati dal manifesto. La demo è un **estratto** di sedici secondi: per
   il brano intero c'è *Brani dal sito*, qui sotto. Con `?demo=demo-video` la demo è
   invece il video scomposto in strati (sfondo, fuoco, buio, neve, immagine): vedi
   *Da un video al pacchetto*.
2. **Aggiungi un livello**: trascina un video o un'immagine sullo schermo, oppure
   usa **+ Video o immagine** nel blocco *Livelli*. Nasce in cima allo stack,
   quindi copre quello che sta sotto; se è un loop su fondo nero mettilo in
   **fusione Schermo** e abbassa l'opacità. Con **×** sulla riga lo elimini.
3. **Aggiungi audio**: trascina un file audio sullo schermo, oppure usa **+ Audio**
   accanto a *+ Video o immagine*, oppure **+ Aggiungi audio** nel blocco *Tracce
   audio*. Gli audio non diventano livelli: finiscono nelle tracce, dove la **×**
   toglie la traccia, **M** la muta, **S** la isola, e le due manopole regolano
   volume e ritardo d'ingresso. Il suono di un livello video non si sente: nel
   progetto l'audio arriva solo dalle tracce.
4. **Scegli il livello dallo stack** e dagli uno o più effetti (o lascialo pulito),
   poi **Riproduci**. La durata del progetto è la sorgente più lunga: un video più
   corto si ripete da capo finché la timeline non finisce.
5. **Esporta** con *Registra*: parte dall'inizio, si ferma alla fine e scrive un
   WebM con l'audio che stai sentendo.

Il blocco **Esempi** dell'effetto Neve porta il riferimento al video del canale:
**Ho già il file** serve se hai scaricato quell'overlay (il file non viaggia col
progetto, i crediti restano a chi l'ha fatto): diventa un livello normale, con le
stesse manopole degli altri.

**Componi come nel video.** Nel blocco *Livelli*, **Componi come nel video** prende
due immagini e il mix — o già gli stems — e monta lo stack identico al pacchetto
`demo-video`: sfondo, velo di fuoco all'8% in fusione Schermo, buio sul colpo, neve
reattiva e immagine con Tremolio + Saturazione (0,40% a 24 Hz e +35%), gli stessi
numeri del manifesto tranne il tremolio, tenuto più leggero. Il primo layer entra
in **Adatta intera** al 100%, come il primo piano della demo: tutta l'immagine
dentro il frame 1280 × 720, senza tagli. **+ Mix o stems** accetta i file uno alla
volta: ognuno compare come voce con la sua **×** e si toglie senza rifare la scelta,
mentre **Togli l'audio** svuota l'elenco. Un file solo passa da Demucs (lo
scaricatore su `:5070`) e diventa batteria + basso, col gate sulla banda del colpo;
se Demucs non risponde, il mix intero passa lo stesso dal gate sulla banda scelta,
così gli effetti restano agganciati a quella frequenza. Con **Sorgente del colpo**
scegli se gli effetti devono seguire il mix, lo stem della batteria (kick) o quello
dell'808 (basso): il trigger analizza solo quella traccia, anche se è muta. Fuoco e
neve si cercano nella cartella del pacchetto, poi in `demo-video/` (è il pacchetto
grosso, quello che sul sito pubblicato non c'è) e infine allo scaricatore, come per i
video del blocco Esempi; **File del fuoco** e **File della neve** li scavalcano
entrambi, così la scena si monta anche con i video che hai tu. È lo stesso meccanismo
della demo: il manifesto di `demo/` elenca cinque strati e i due mp4 li prende da
`demo-video/`. Se non arrivano lo stack si monta lo stesso e la riga di stato dice
cosa manca. Con **Registra il video appena
composto** la composizione parte subito in registrazione e si ferma da sola alla
fine dell'audio: il WebM arriva senza altri clic.

**Brani dal sito.** Sempre nel blocco *Tracce audio*, **Brani dal sito** porta dentro
i brani veri di Raedius Productions, interi e non gli estratti della demo.
L'indirizzo di serie è `http://127.0.0.1:7862/`, il sito in locale (nella sua cartella:
`python3 strumenti/serve.py`); se un giorno il sito va in rete, si incolla lì.
**Leggi il catalogo** carica `assets/data/album.js` e `lavori.js` come `<script>` —
il catalogo non passa da `fetch`, quindi non ha bisogno del CORS — e riempie un solo
elenco: le raccolte (Vol. 1, Vol. 2, **Remixes Collection Vol. 3** con i suoi
quarantuno brani, versioni comprese, e i mashup) e l'archivio diviso per catalogo
(remix, type beat, strumentali), con la testata del gruppo quando cambia. Lo stesso
file che sta in una raccolta e anche nell'archivio compare una volta sola.

Sopra l'elenco c'è **Cerca un brano**: si scrive e le righe si stringono mentre
digiti (accenti e maiuscole non contano, le parole possono arrivare in disordine),
**Invio** prende il primo risultato, **Esc** svuota il campo. Se incolli un percorso
che sembra un audio (`assets/audio/…/nome.mp3`) e non è a catalogo, l'elenco te lo
propone lo stesso: è la via per i file rimasti fuori da `album.js` e `lavori.js`.

Sotto la lista c'è il brano scelto con artisti, durata e raccolta, e quattro
pulsanti. **Ascolta** fa sentire l'mp3 dal sito senza toccare il progetto (un
`<audio>` suo: si zittisce da solo quando scegli un altro brano o premi
Riproduci). **+ Alle tracce** scarica il file e lo aggiunge alle tracce, col titolo
del brano al posto del nome-hash del file. **Al posto dell'audio** fa lo stesso ma
prima toglie le tracce che ci sono — è il modo per cambiare brano senza rifare il
progetto: i livelli restano come sono. **Componi la scena** monta lo stack di
*Componi come nel video* con la copertina del brano come primo layer e la stessa
copertina sfocata come sfondo: il pezzo parte intero, con fuoco, buio, neve e
immagine già sui loro numeri. Audio e copertine si scaricano con `fetch`, quindi il
server del sito deve mandare `Access-Control-Allow-Origin` (lo fa il suo
`strumenti/serve.py`, e lo fa GitHub Pages se il sito è in rete). L'indirizzo resta
in memoria: alla riapertura è già lì.

**Chi accende l'animazione.** In fondo a *Componi come nel video*, **Chi accende
l'animazione** decide chi comanda il gate degli strati. *Il brano* sono i colpi del
mix o dello stem scelto, come nel video. *Un file MIDI* cambia il gate: contano le
note — una nota lunga tiene accesi insieme fuoco, neve, buio e immagine, il silenzio
li spegne; la riga per scegliere il `.mid` compare solo con questa voce. *La mia
mano* fa ripartire il brano da capo e registra i click sul pad (o il tasto **H**):
poi li ripete da solo, e il video esce già con il gesto giusto.

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
adatta intera). La manopola **Larghezza** (10–200%) ridimensiona il livello senza
deformarlo: 100% è la misura dell'inquadratura, e l'output dice anche quanti pixel
occupa sul frame e se viene tagliata ai bordi. **Formato demo · 1280 × 720**
mette tutta l'immagine dentro il frame del primo piano della demo, senza
tagliarla: una foto quadrata diventa 720 × 720. Per riempire tutto il frame,
scegli «Riempi il frame». Un'immagine appena aggiunta nasce già in «Adatta
intera», un video invece riempie il frame; le tinte piatte (il nero del buio,
un PNG 32 × 32) riempiono sempre il frame, perché «adatta intera» ne farebbe un
quadrato in mezzo al fondale invece di abbassare tutta la scena. Gli strati di un
pacchetto demo riempiono il frame salvo che il manifesto dica `"adatta": 1`.

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
progetto è la traccia più lunga. Sotto le tracce c'è **Brani dal sito**: il catalogo
di Raedius Productions in una lista cercabile, con **Ascolta** per sentire il brano
prima, **+ Alle tracce** per aggiungerlo, **Al posto dell'audio** per cambiare brano
tenendo il progetto e **Componi la scena** per portarlo fino ai livelli.

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
(`cover.jpg`, `sfondo.jpg`, `buio.png` e le quattro tracce `mix.wav`, `kick.wav`,
`bass808.wav`, `hat.wav`); da `file://` la
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
demo/cover.jpg             la cover: la variante «(1)» dell'opera della Remixes
                           Collection Vol. 3 (1200×1200)
demo/sfondo.jpg            il fondale sfocato che le sta dietro (1280×720)
demo/buio.png              un nero 32×32, acceso sul colpo
demo/mix.wav               estratto di 16 s (112 BPM, 32 kHz mono)
demo/kick.wav              solo cassa
demo/bass808.wav           solo 808
demo/hat.wav               solo hi-hat
demo/pacchetto.json        durata, BPM, colpi e pila dei livelli; il fuoco e la
                           neve li rimanda a demo-video/ (vedi sotto)
strumenti/genera_demo.py   rigenera demo/ sintetica (numpy + Pillow)
strumenti/demo_da_brano.py  il pacchetto da un brano e due immagini
strumenti/pacchetto_da_video.py  costruisce un pacchetto da un tuo filmato
strumenti/serve.py         server statico per l'uso in locale
```

Le tracce del pacchetto sono **Off The Wall (Remix) [Instrumental]**, dalla
*Remixes Collection Vol. 3* di Raedius Productions (l'archivio di `sito-beat/`): il
pacchetto ne tiene sedici secondi a 112 BPM, separati con Demucs e filtrati come i
brani caricati a mano. Chi vuole il pacchetto sintetico di prima lo rigenera con
`genera_demo.py`: cassa, 808 e hi-hat a 120 BPM, nessun campione esterno. L'unico
filmato di terzi che l'app cita è l'overlay di neve, e resta sul sito del suo
autore.

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


## Da un brano al pacchetto

Quando il brano c'è ma il video no, la scena si monta da due immagini:

```
python3 strumenti/demo_da_brano.py brano.mp3 \
    --cover opera.jpeg --sfondo fondale.jpeg --uscita demo --durata 16
```

Lo strumento prende un estratto (di serie 16 s, dalla finestra con più cassa nel
brano; `--inizio` la fissa a mano), separa batteria e basso con Demucs, filtra le
bande che l'app ascolta e scrive le quattro tracce a 32 kHz mono, come fa
`pacchetto_da_video.py`. L'opera diventa `cover.jpg` (1200 × 1200), il fondale
`sfondo.jpg` (1280 × 720), il buio `buio.png`; il manifesto elenca la pila dal fondo
alla cima — sfondo, buio, opera — con il buio al 42% che si accende sul colpo e
l'opera in «adatta intera» con Tremolio e Saturazione. Senza `--sfondo` la pila
resta buio + opera, e sotto c'è il nero del palco. `--sorgente` è il nome che
finisce nel manifesto (per i crediti del brano), `--uscita` la cartella. Con
`--con-fuoco` la pila diventa quella della demo di serie — sfondo, velo di fuoco
all'8%, buio, neve, opera — e sono gli stessi strati che l'app cerca in `demo-video/`
(il manifesto ne dichiara la fonte, i file non si copiano).

Il `demo/` pubblicato è fatto così: *Off The Wall (Remix) [Instrumental]* della
Remixes Collection Vol. 3, quindi sedici secondi a 112 BPM, con la cover della
raccolta e il suo fondale, più il fuoco e la neve presi da `demo-video/`.


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
