# Marketing — Asilo Sartorio

Sistema di lavoro per preparare e pubblicare, in modo ripetibile e sicuro, la comunicazione dell'Asilo Infantile "Domenico Sartorio" (Montegrino Valtravaglia): **sito WordPress, Facebook, Instagram**, più testi pronti per WhatsApp famiglie e Luino Notizie.

> In una frase: **Claude prepara tutto (testi, bozze, anteprime), tu approvi, e nulla esce senza un tuo "ok" esplicito scritto in chat.**

**Indice:** [Primo avvio](#1-primo-avvio-una-volta-sola) · [Uso quotidiano](#2-uso-quotidiano) · [Regole](#3-le-regole-che-non-cambiano) · [Struttura](#4-struttura-della-cartella) · [Riferimento script](#5-riferimento-script) · [Manutenzione](#6-manutenzione-token-e-credenziali) · [Problemi comuni](#7-problemi-comuni) · [Stato](#8-stato-del-progetto)

---

## 1. Primo avvio (una volta sola)

Cosa serve: un computer Windows con **Python 3.8 o superiore**, **Claude Code** (o l'app Claude, scheda Code) con questa cartella aperta, e i permessi di amministratore su sito, Pagina Facebook e account Instagram.

0. **Scarica il progetto:** `git clone <url-del-repository> asilo-marketing` (o scarica lo ZIP da GitHub) e lavora dentro quella cartella.
1. **Apri la cartella in Claude Code.** Compaiono i comandi `/nuova-campagna`, `/pubblica-bozza`, `/pubblica-social`, `/stato`, `/verifica`, `/calendario` e i due agenti.
2. **Installa le librerie:** `python -m pip install --user -r requirements.txt`
   (`--user` le mette nel profilo dell'utente: niente file dentro la cartella su Drive).
3. **Crea `config.yaml`:** copia `config.sample.yaml` in `config.yaml` e sostituisci ogni `INSERISCI_...` con il valore vero. Contiene credenziali: non condividerlo.
4. **Collega WordPress:** segui [docs/setup-wordpress.md](docs/setup-wordpress.md) (5 minuti).
5. **Collega Facebook e Instagram:** segui [docs/setup-meta.md](docs/setup-meta.md) (circa 30 minuti; è la parte più delicata).
6. **Verifica tutto:** `python scripts/check_setup.py` (o `/verifica` in Claude). Alla fine deve dire "tutto a posto". Se manca qualcosa, per ogni voce indica quale guida seguire.

Puoi anche attivare solo ciò che ti serve: WordPress da solo funziona senza Meta, e viceversa.

## 2. Uso quotidiano

### Il flusso di una campagna
1. **`/nuova-campagna [nome]`** — Claude chiede in un unico messaggio i dati (data, ora, luogo, programma, costi, contatti, locandina, canali). Rispondi solo con ciò che sai: i dati mancanti restano segnati nel brief e **non vengono inventati**. Poi crea cartella, brief, testi per ogni canale e checklist.
2. **Rivedi in chat** e chiedi modifiche ("più breve", "togli l'emoji", "aggiungi che…").
3. **Sito: `/pubblica-bozza 2026-nome`** — controlli, dry-run, anteprima. Rispondi "ok, crea la bozza su WordPress" (dicendo slider sì/no e se creare tag nuovi). La **bozza** è creata; il click su "Pubblica" lo fai tu in WordPress.
4. **Facebook: `/pubblica-social 2026-nome facebook`** — controlli, anteprima con un **codice**. Rispondi "ok, pubblica su Facebook": il post esce subito.
5. **Instagram: `/pubblica-social 2026-nome instagram`** — se la locandina non è un JPEG 4:5, Claude la converte e, **con il tuo ok**, la carica sul sito per avere l'URL pubblico richiesto da Instagram. Poi anteprima e "ok, pubblica su Instagram".
6. **WhatsApp e Luino Notizie:** copi tu i testi dai file `.md` (Luino: mail con locandina e foto).
7. **Chiusura:** Claude aggiorna `esito.md` e la checklist; `/calendario` aggiorna le scadenze.

### Comandi
| Comando | Cosa fa |
|---|---|
| `/nuova-campagna [nome]` | Chiede i dati, crea cartella, brief, testi e checklist. Non pubblica nulla. |
| `/pubblica-bozza <campagna>` | Controlli → dry-run → anteprima → tuo ok → **bozza** WordPress → `esito.md`. |
| `/pubblica-social <campagna> <facebook\|instagram>` | Controlli → anteprima con codice → tuo ok per quel canale → pubblicazione → `esito.md`. |
| `/stato [campagna]` | A che punto sono le campagne: stato, canali, file e dati mancanti. Sola lettura. |
| `/verifica` | Controlla installazione, collegamenti e **scadenza del token**. Sola lettura. |
| `/calendario [eventi]` | Aggiorna `calendario.md` con le prossime scadenze. Non inventa date. |

### Abitudini consigliate
- Inizia la sessione con `/stato` (cosa c'è in sospeso) e, prima di pubblicare, `/verifica`.
- Il **brief** è la fonte unica dei dati: se un dato cambia, aggiornalo lì e fai rigenerare i testi.
- Scrivi sempre nel brief il **testo alternativo** in italiano della locandina: lo usano sito, Facebook e Instagram.
- Un "ok" vale per **un canale e un testo**. Se cambia qualcosa, Claude rifà l'anteprima e chiede un nuovo ok.
- Dopo aver pubblicato l'articolo sul sito, aggiungi a mano su Facebook il commento con il link.

## 3. Le regole che non cambiano

1. **Non inventare mai** date, orari, prezzi, nomi, programmi, contatti. Si usano solo i dati del `brief.md`; se manca qualcosa, Claude **te lo chiede**.
2. **Anteprima prima, ok poi.** Ogni pubblicazione passa da un'anteprima in chat e da un tuo ok scritto, per quel contenuto e quel canale.
3. **WordPress: sempre bozza.** Lo script non può impostare `publish` né programmare.
4. **Facebook e Instagram: un post alla volta**, e il post esce subito (non esistono bozze via API). Lo script esige il **codice** dell'anteprima approvata: se testo, immagine o alt cambiano, il codice cambia e rifiuta. Non ripubblica lo stesso testo due volte. Non programma, non modifica, non elimina.
5. **Niente modifiche ai contenuti esistenti** del sito e dei social; nessuna eliminazione.
6. **Privacy:** niente nomi o volti riconoscibili di bambini senza consenso immagini; niente dati personali di famiglie o fornitori.
7. **Credenziali:** solo in `config.yaml` o nelle variabili d'ambiente; mai in chat, nei log, nei commit. Claude non legge né stampa `config.yaml`.

**Tono di voce:** diamo del **tu** (il "voi" solo a più persone), colloquiale, amichevole, non banale, stimolante, italiano semplice. Da evitare: burocratese ("si comunica che"), punti esclamativi a raffica, frasi fatte, promesse non verificabili. Dettagli in `brand/linee-guida.md`; hashtag in `brand/hashtag.md`.

## 4. Struttura della cartella

```
Marketing/
├── README.md                  questa guida
├── CLAUDE.md                  regole permanenti per Claude
├── calendario.md              calendario editoriale (locale, non versionato; nasce da templates/calendario.md)
├── requirements.txt           librerie Python (requests, Pillow)
├── config.yaml                credenziali (NON condividere; ignorato da git)
├── config.sample.yaml         reference di tutte le chiavi, solo segnaposto
├── .env.example               nomi delle variabili d'ambiente alternative
├── docs/                      setup-wordpress.md, setup-meta.md
├── brand/                     linee-guida.md, hashtag.md, logo/
├── templates/                 brief, articolo, post social, WhatsApp, mail Luino, checklist, esito
├── campagne/AAAA-nome/        una cartella per campagna (locale, non versionata):
│     brief.md · testi/ · immagini/ · checklist.md · esito.md · social-esito.json
├── luino-notizie/             AAAA-nome.md: mail pronte (spedite a mano; locale, non versionata)
├── scripts/                   gli script (vedi sotto)
└── .claude/                   agents/ (marketing-strategist, social-publisher) e commands/
```
Gli originali di locandine e loghi restano nell'archivio dell'asilo (`02 - Comunicazione e Locandine`, `01 - Brand e Logo`): qui si lavora su **copie**.

**Convenzioni:** cartelle `AAAA-nome-in-minuscolo`; file in minuscolo, senza spazi né accenti. Ogni testo definitivo sta **in un solo file**: `post-social.md` (sezioni Facebook e Instagram) oppure `post-facebook.md`/`post-instagram.md`, che hanno la precedenza. Il `social-esito.json` è il registro dei post usciti: lo scrive solo lo script.

## 5. Riferimento script

Di solito non li lanci tu: lo fanno i comandi. Li trovi in `scripts/`; ognuno ha `--help` e un'intestazione che spiega vincoli ed esempi.

| Script | Cosa fa | Note |
|---|---|---|
| `check_setup.py [--offline]` | Controlla Python, librerie, chiavi di config, collegamenti, scadenza token | Sola lettura |
| `stato_campagne.py [campagna]` | Riepilogo campagne | Sola lettura, senza rete |
| `publish_post.py` | Crea la **bozza** di articolo WordPress (`--dry-run` per l'anteprima) | Titolo max 4 parole, `--excerpt` obbligatorio (3-4 parole); solo `draft`/`pending`; non crea categorie; i tag nuovi solo con `--create-tags`; si ferma se lo slug esiste |
| `publish_social.py` | Anteprima o pubblicazione di **un** post Facebook/Instagram | `--publish` richiede `--approved-code`; `--check` mostra tipo, permessi e scadenza del token |
| `to_jpeg.py` | Converte un'immagine in JPEG per Instagram (`--pad-to 4:5` per aggiungere bordo senza ritagliare) | Non sovrascrive originali; toglie i metadati EXIF/GPS |
| `upload_media.py` | Carica **un** file nei media di WordPress e stampa l'URL | Non sostituisce media esistenti; prima `--dry-run` |
| `_common.py` | Funzioni condivise (configurazione, errori) | Non si lancia da solo |

Esempio completo per Instagram:
```
python scripts/to_jpeg.py campagne/2026-nome/immagini/locandina.png --pad-to 4:5 --out campagne/2026-nome/immagini/locandina-ig.jpg
python scripts/upload_media.py campagne/2026-nome/immagini/locandina-ig.jpg --alt "Descrizione in italiano" --dry-run
python scripts/publish_social.py --channel instagram --campaign 2026-nome --image-url https://www.asilosartorio.it/wp-content/uploads/...jpg
```

## 6. Manutenzione: token e credenziali

- **Token Facebook/Instagram:** se è un token da 60 giorni scade; se invece è stato ricavato da un token utente esteso non scade mai ([docs/setup-meta.md](docs/setup-meta.md), sezione 2). `/verifica` e `publish_social.py --check` mostrano la scadenza e avvisano sotto i 14 giorni. Dal 17/10/2026 il token in uso è permanente (tipo Page, non scade); può comunque essere revocato da Meta.
- **Revoca:** se un token o una password finiscono in chat o sembrano compromessi, vanno revocati (Meta: Integrazioni aziendali; WordPress: Application Passwords) e rigenerati.
- **Continuità:** meglio due amministratori sulla Pagina e su Instagram, e un utente WordPress dedicato, così nessuno è indispensabile.
- **Chiavi:** ogni nuova chiave letta dagli script va aggiunta a `config.sample.yaml`, `.env.example` e alla guida pertinente.
- **Versione Graph API** (`graph_version`): Meta ritira le versioni vecchie; se un giorno le chiamate danno errori di versione, aggiornala in `config.yaml`.

## 7. Problemi comuni

| Sintomo | Cosa fare |
|---|---|
| `check_setup.py`: libreria mancante | `python -m pip install --user -r requirements.txt` |
| `config.yaml` assente o chiavi segnaposto | Copia `config.sample.yaml`, compila, aspetta la sincronizzazione di Drive |
| WordPress HTTP 401 / 403 / 404 | Vedi [docs/setup-wordpress.md](docs/setup-wordpress.md), sezione "Problemi tipici" |
| "Esiste già un articolo / media con…" | Cambia titolo, `--slug` o nome del file: gli script non sostituiscono nulla |
| "Tag inesistenti" | Correggi i nomi o autorizza `--create-tags` |
| Meta: errore 190 (token scaduto/revocato), 200 (permesso mancante), ID non numerico, Pagina che non compare | Vedi [docs/setup-meta.md](docs/setup-meta.md), tabella "Problemi tipici" |
| Instagram rifiuta l'immagine | Deve essere JPEG, 4:5, con URL https pubblico: `to_jpeg.py` + `upload_media.py` |
| "Già pubblicato su…" | Il registro `social-esito.json` blocca il doppio invio: è voluto |
| Errore di rete durante la pubblicazione | **Controlla prima sulla Pagina/Instagram se il post è uscito**, poi eventualmente riprova |
| Comandi o agenti non compaiono | Riapri la cartella `Marketing` in Claude Code |

**Cartella su Drive:** un solo editor alla volta sullo stesso file (evita copie "in conflitto"); non toccare i file `~$...`; niente ambienti virtuali o cartelle di cache nella cartella (gli script non creano `__pycache__`).

### Versioni e ripartenza (git / GitHub)
Il repository contiene **solo gli strumenti**: `scripts/`, `.claude/`, `templates/`, `brand/`, `docs/`, `requirements.txt`, `config.sample.yaml`, `.env.example`, `CLAUDE.md`, `README.md`. **Non** contiene (`.gitignore`): `config.yaml` e `.env` (segreti), `campagne/*`, `luino-notizie/*`, `calendario.md`, `*.zip`. Le cartelle `campagne/` e `luino-notizie/` esistono grazie a un `.gitkeep`.

- **Salvare un'evolutiva:** `git add -A && git commit -m "cosa è cambiato" && git push`. Prima di ogni commit controlla con `git status` che non compaiano `config.yaml` o cartelle di campagna. Ricorda la regola: ogni modifica a script, comandi o chiavi si riflette anche in `CLAUDE.md`, `README.md`, `config.sample.yaml`/`.env.example` e `docs/`.
- **Ripartire da zero su un computer nuovo:** `git clone` → `python -m pip install --user -r requirements.txt` → copia `config.sample.yaml` in `config.yaml` e compilalo (i valori reali stanno nel gestore di password dell'asilo, **mai** nel repository) → `python scripts/check_setup.py` → apri la cartella in Claude Code e lancia `/nuova-campagna`. `/calendario` ricrea `calendario.md` dal modello.
- **Backup delle campagne:** non stanno su git; restano sul Drive/archivio dell'asilo.
- **Se un segreto finisce per sbaglio in un commit:** revocalo subito (WordPress/Meta) e rigeneralo; cancellare il commit non basta.

## 8. Stato del progetto
- **Caso pilota: Castagnata 2026** (`campagne/2026-castagnata/`): Facebook e Instagram **pubblicati il 17/10/2026**; bozza WordPress ID 1438 da pubblicare a mano; WhatsApp e Luino Notizie in bozza (mancano destinatario, contatti, firma).
- **Da confermare** in `brand/linee-guida.md`: codici dei colori, font ufficiale, firma e formule fisse.
- `calendario.md` è una ricostruzione da sito e archivio: le date sono **indicative** e vanno verificate.
- **Titolo e riassunto WordPress:** brevissimi (titolo max 4 parole, estratto 3-4 parole); `publish_post.py` rifiuta testi più lunghi.
- **Possibili sviluppi:** programmazione dei post, modello di rendiconto post-evento, Instagram Stories e Reels, cartella `immagini/` con ritaglio automatico per formato.
