# Marketing — Asilo Sartorio (e Sheepper)

Base per la comunicazione dell'Asilo Infantile "Domenico Sartorio" (scuola dell'infanzia paritaria, Montegrino Valtravaglia, VA; associazione senza fini di lucro). Canali: sito https://www.asilosartorio.it (WordPress), Facebook e Instagram (pubblicati con gli script del progetto; in alternativa Metricool o post diretti), Luino Notizie (mail con articolo e foto), WhatsApp famiglie.

## Chi siamo e a chi parliamo
- Associazione che gestisce l'asilo: vuole farsi vedere, portare nuove famiglie, promuovere attività didattiche e sociali.
- Pubblico: social = chi segue la pagina e i gruppi dove facciamo forward; Luino Notizie e sito = generalista, obiettivo nuove famiglie.

## Tono di voce
Diamo del **tu** (il "voi" solo se parliamo a più persone). Colloquiale, amichevole, non banale, stimolante, convincente. Italiano semplice, frasi brevi.
**Evitare:** burocratese ("si comunica che", "gentili genitori"), punti esclamativi a raffica, frasi fatte, promesse non verificabili. Dettagli in `brand/linee-guida.md`.

## Regola d'oro
**Non inventare mai** date, orari, prezzi, nomi, programmi, contatti o altri dettagli. Se mancano, **chiedere**. Usare solo i dati scritti nel `brief.md` della campagna.

## Regola di sicurezza
- Tutto nasce come **BOZZA** e viene mostrato in anteprima in chat (per WordPress: `--dry-run`).
- Si procede **solo con un OK esplicito scritto in chat** (es. "ok, pubblica su sito"), per quel contenuto e quel canale. Se il testo cambia dopo l'ok, serve un nuovo ok.
- "Pubblica su sito" significa **creare la bozza su WordPress**: lo script non può impostare `publish` né programmare. L'ultimo click su "Pubblica" lo fa l'utente in WordPress.
- Mail (Luino Notizie) e WhatsApp: Claude prepara solo il testo in file `.md`. Non invia mai.
- **Facebook e Instagram** si pubblicano con `scripts/publish_social.py` (`/pubblica-social`), **un canale e un post per volta**: anteprima in chat con CODICE ANTEPRIMA → OK esplicito scritto per quel canale e quel testo (es. "ok, pubblica su Facebook") → `--publish --approved-code <codice>`. Un ok per un canale non vale per l'altro; se testo, immagine o alt cambiano, serve un nuovo ok. Mai programmare, modificare o eliminare post esistenti. Il post è subito online (nessuna bozza): per questo il controllo è prima.
- Nessuna modifica a impostazioni, plugin, utenti o contenuti esistenti del sito. Nessuna eliminazione.
- Privacy: niente nomi o foto riconoscibili di bambini senza consenso immagini; niente dati personali di famiglie o fornitori. Mai copiare nel progetto file da cartelle con documenti personali dell'archivio.

## Credenziali
- Stanno in `config.yaml` (chiavi `wp_user`, `wp_app_password`; social: `fb_page_id`, `fb_page_token`, `ig_user_id`, opzionale `graph_version`; DeepSeek: `deepseek_api_key`, opzionali `deepseek_model`, `deepseek_base_url`) o nelle variabili `WP_URL`, `WP_USER`, `WP_APP_PASSWORD`, `FB_PAGE_ID`, `FB_PAGE_TOKEN`, `IG_USER_ID`, `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL`; le variabili hanno la precedenza. Il file è ignorato da git; il rischio di tenerlo nella cartella su Drive è accettato dall'amministratore.
- `config.sample.yaml` è il reference di tutte le chiavi, con soli segnaposto. **Va aggiornato a ogni modifica** che aggiunge, rinomina o rimuove una chiave letta dagli script (e insieme a `.env.example`).
- **Mai** nel codice, nei log, nei commit o in chat. Non leggere né stampare `config.yaml`: lo legge solo lo script.

## Agenti (`.claude/agents/`)
- `marketing-strategist`: messaggio e testi (articolo, Luino Notizie, WhatsApp), coerenza di tono e brand.
- `social-publisher`: formati e tecnica per canale (Facebook, Instagram, WhatsApp, WordPress, Metricool), alt text, checklist.
Flusso: brief → strategist scrive → publisher adatta e compila la checklist → anteprima in chat → OK esplicito per canale → bozza WordPress / post Facebook / post Instagram.

## Strumenti (`scripts/`)
Tutti in Python 3.8+, dipendenze in `requirements.txt` (`python -m pip install --user -r requirements.txt`). Codice comune (configurazione, errori) in `scripts/_common.py`.
- `check_setup.py [--offline]`: controlla Python, librerie, chiavi di `config.yaml` (solo presente/mancante), collegamenti WordPress/Facebook/Instagram e **scadenza del token**. Sola lettura. Da usare all'inizio di una sessione di pubblicazione e quando qualcosa non va.
- `stato_campagne.py [campagna]`: riepilogo di stato, canali, file e dati mancanti. Sola lettura, senza rete.
- `publish_post.py`: bozza di articolo su WordPress (solo `draft`/`pending`; titolo max 4 parole, `--excerpt` obbligatorio di 3-4 parole). Usato da `/pubblica-bozza`.
- `publish_social.py`: post su Facebook o Instagram, uno per volta, con anteprima+codice. Testo da `testi/post-<canale>.md` o dalla sezione del canale in `post-social.md`; testo alternativo dal brief. Usato da `/pubblica-social`. `--check` mostra anche tipo, permessi e scadenza del token.
- `to_jpeg.py <immagine> [--pad-to 4:5|1:1|1.91:1] [--out file.jpg]`: converte in **JPEG per Instagram** (trasparenza su bianco, niente metadati EXIF/GPS, 1440 px max, nessun ritaglio). Da usare **ogni volta che un'immagine per Instagram non è JPEG** o ha proporzioni fuori range (feed: da 4:5 a 1.91:1; una locandina verticale richiede `--pad-to 4:5`). Non sovrascrive originali né file esistenti.
- `upload_media.py <immagine> --alt "..." [--title "..."] [--dry-run]`: carica **un** file nella libreria media di WordPress e stampa ID e URL pubblico (serve per `--image-url` di Instagram). Solo dopo mio ok esplicito per quel file; prima `--dry-run`. Non sostituisce media con lo stesso nome, non tocca articoli, nessuna cancellazione.
- `test_deepseek.py [--prompt "..."] [--model ...]`: prova la connessione all'API di DeepSeek con un prompt semplice e stampa la risposta. Una sola richiesta, nessuna scrittura; il prompt esce verso un servizio esterno, quindi solo testo di prova, mai dati personali.
Catena per Instagram: `to_jpeg.py` → (ok) `upload_media.py` → `publish_social.py --image-url`.

## Comandi (`.claude/commands/`)
- `/nuova-campagna`: chiede i dati, crea cartella campagna, brief e bozze per ogni canale.
- `/pubblica-bozza <campagna>`: dry-run, anteprima, ok esplicito, poi bozza su WordPress.
- `/pubblica-social <campagna> <facebook|instagram>`: controlli, anteprima con codice, ok esplicito per canale, poi pubblicazione.
- `/calendario`: aggiorna `calendario.md` con le prossime scadenze.
- `/stato [campagna]`: a che punto sono le campagne (sola lettura).
- `/verifica`: controlla installazione, collegamenti e scadenza del token (sola lettura).

## Struttura e convenzioni
```
CLAUDE.md  README.md  calendario.md (locale)  requirements.txt
config.yaml (segreto)  config.sample.yaml  .env.example  .gitignore
docs/            setup-wordpress.md, setup-meta.md (guide di installazione e manutenzione), piano-webapp.md, bootstrap-progetto.md, adr/ (decisioni)
.github/         workflow (CI `verifica`, triage, chiusura issue), template di issue e PR, ruleset di `main`
scripts/*.sh     setup-labels, setup-project, apply-ruleset, classify-changes (framework my-ai-squad)
brand/           linee-guida.md, hashtag.md, logo/ (logo-rosso.png principale, logo-blu.png)
campagne/AAAA-nome/   brief.md, testi/, immagini/, checklist.md, esito.md, social-esito.json (scritto dallo script)
luino-notizie/   AAAA-nome-campagna.md (mail pronta, spedita a mano)
templates/       calendario.md, brief.md, articolo-blog.html, post-social.md, whatsapp-famiglie.md, email-luino-notizie.md, checklist.md, esito.md
scripts/         _common.py, check_setup.py, stato_campagne.py, publish_post.py, publish_social.py, to_jpeg.py, upload_media.py, test_deepseek.py
.claude/agents/  .claude/commands/
```
- Cartelle campagna: `AAAA-nome-in-minuscolo-con-trattini` (es. `2026-castagnata`). Nomi file in minuscolo, senza spazi né accenti, con trattini.
- Testi: `articolo-blog.html`, `post-social.md` (sezioni Facebook e Instagram), `whatsapp.md`. Se un canale richiede un adattamento: `post-facebook.md` / `post-instagram.md`, che hanno la precedenza su `post-social.md`. **Ogni testo definitivo sta in un solo file** (nell'altro, un rimando).
- Immagini: originale (`locandina.png`) + derivato per Instagram (`locandina-ig.jpg`, 4:5). Gli originali non si modificano.
- Il `brief.md` ha stato (`bozza|approvato|pubblicato`), `approvato_da`, dati confermati e dati WordPress (titolo, slug, **titolo ≤4 parole, estratto 3-4 parole**, categoria, tag, **testo alternativo**, usato anche dai social).
- Il `social-esito.json` è il registro dei post social usciti (canale, codice, ID, data): lo scrive solo lo script e impedisce il doppio invio.
- WordPress: categoria `avvisi` per gli eventi; `slider` solo se deve andare nel carosello della home (flag esplicito).
- Hashtag: `brand/hashtag.md`.
- Ogni modifica a scripts, comandi o chiavi di configurazione va riflessa nello stesso intervento in `AGENTS.md`, `README.md`, `config.sample.yaml`/`.env.example` (se tocca chiavi) e nelle guide in `docs/`.

## Repository git
Il progetto è un repository: versionati solo gli strumenti (scripts, `.claude/`, templates, brand, docs, config.sample.yaml, .env.example). **Mai** in git: `config.yaml`, `.env`, `campagne/*`, `luino-notizie/*`, `calendario.md`, `*.zip` (vedi `.gitignore`). Prima di ogni commit controlla `git status`; commit e push solo su richiesta dell'utente. Un'installazione nuova deve partire con: clone → `pip install -r requirements.txt` → `config.yaml` da `config.sample.yaml` → `check_setup.py`. Se aggiungi un file che serve a una installazione nuova, assicurati che non sia ignorato.

## Squadra di agenti (my-ai-squad)

Il progetto adotta il framework [my-ai-squad](https://github.com/matteopelucco/my-ai-squad) (v0.4.0): agenti, skill e guardrail vengono dal plugin `squad-core` (`/squad-core:work-on-issue`, `/squad-core:next-task`, …); perimetri di scrittura, comandi di verifica e modalità di merge sono in `.claude/squad.json`. Gli agenti `marketing-strategist` e `social-publisher` e i comandi `/nuova-campagna`, `/pubblica-*`, `/stato`, `/verifica`, `/calendario` sono **specifici del dominio** e restano in `.claude/`. Decisione e scostamenti dal template: [ADR 0001](docs/adr/0001-adozione-my-ai-squad.md).

### Regole di sviluppo
- Backlog = GitHub Issues di questo repository. Una issue alla volta, branch `<tipo>/<n>-slug`, PR verso `main`. **Mai commit o push su `main`** (l'unica eccezione è il primo caricamento della storia esistente sul remoto, deciso dall'utente).
- Titoli di issue e PR: `<tipo>(<ambito>): <descrizione>` (Conventional Commits). Codice, identificatori e commit in inglese; documenti, issue e PR in italiano.
- Repository pubblico: niente segreti, niente dati reali o personali, nemmeno nelle fixture. `config.yaml` e `.env*` non si leggono (regola `deny` in `.claude/settings.json`).
- Una decisione architetturale nuova o cambiata → ADR in `docs/adr/`.
- Il merge delle PR è sempre dell'utente (`mergeMode: human`): gli agenti aprono la PR in bozza e si fermano.
- Le issue `status:ready` si lavorano per priorità del Project (più in alto = prima); a parità, prima i `type:bug`.

### Controlli
- Rapidi (a fine lavoro) e completi (prima della PR): `python -B -c "import ast,glob;[ast.parse(open(f,encoding='utf-8').read()) for f in glob.glob('scripts/*.py')]"` (controllo di sintassi degli script; `.claude/squad.json` è la fonte). La CI (`.github/workflows/ci.yml`, job `verifica`) esegue lo stesso comando sulle PR che toccano codice e lo salta se cambiano solo documenti.
- La PR riporta comando ed esito dei controlli e ciò che non è stato verificato.

## Setup standard di progetto e web app Sheepper

Il modo in cui questo tipo di progetto è impostato (stack, infrastruttura,
SDLC, PR, CI/CD, test, aggiornamento delle dipendenze, agenti) è descritto in
[docs/bootstrap-progetto.md](docs/bootstrap-progetto.md), adattato a Sheepper
(parametri e deroghe in testa al file). È indipendente dal dominio: i requisiti
stanno in `specs/` e le regole operative in questo file. Consultalo quando
imposti o cambi l'architettura, la CI o il flusso di lavoro, non per le task di
feature.

L'evoluzione di questo strumento in web app multi-tenant (Sheepper, Next.js +
Supabase + Vercel) è pianificata, passo per passo, in
[docs/piano-webapp.md](docs/piano-webapp.md). Lo strumento locale descritto
sopra resta la specifica funzionale finché Sheepper non ha la stessa funzionalità.

## Dove trovare cose
- Locandine e storico: `..\..\02 - Comunicazione e Locandine\ANNO\...` (solo lettura).
- Loghi originali: `..\..\01 - Brand e Logo\Logo ufficiale\` (non modificarli).
- Calendario editoriale: `calendario.md` (locale; se manca, crealo da `templates/calendario.md`).

## Lavorare su Drive
Niente ambienti virtuali o cache dentro la cartella (`PYTHONDONTWRITEBYTECODE=1`); non toccare i file `~$*` (aperti in Office); un solo editor alla volta sullo stesso file, per evitare copie in conflitto.
