# Piano d'azione — Sheepper, la web app multi-tenant su Vercel + Supabase

**Sheepper** nasce dall'evoluzione di questo strumento locale (asilo-marketing), che resta come repository di riferimento (specifica e dati storici). Obiettivo: usare il flusso (brief → testi → anteprima → ok → bozza WordPress / post Facebook / post Instagram) da qualsiasi dispositivo, con codice su GitHub, versionato e con pipeline CI/CD, per **più organizzazioni** (tenant). Ciò che oggi sta in `config.yaml` diventa impostazione editabile online, per tenant.

Gli step vanno eseguiti **in ordine**. Ogni step ha: cosa fare, risultato atteso ("Fatto quando"). Non passare al successivo se il "Fatto quando" non è vero.

---

## Direttive di prodotto (fissate)

- **Nome:** Sheepper. **Logo:** una pecora (SVG, in versione a colori, monocromatica e solo-icona/favicon). **Indirizzo iniziale:** `sheepper.vercel.app` (da verificare che sia libero al momento della creazione del progetto).
- **Stesso metodo di Girasole** (`matteopelucco/girasole`), descritto in [bootstrap-progetto.md](bootstrap-progetto.md) con parametri e deroghe di Sheepper: Next.js 16 (App Router, Server Components/Actions, `proxy.ts`), TypeScript, Tailwind 4, shadcn/ui, Supabase (Postgres + Auth + RLS), Vercel **Pro** e Supabase **Pro**; UI in italiano e codice in inglese (salvo termini di dominio); `specs/` con scenari Given/When/Then; `docs/adr/` per le decisioni; Conventional Commits in inglese; trunk-based con PR e anteprima Vercel; hook pre-push (`tsc`, lint, `jscpd`, test, build); repository **pubblico** con le stesse regole di sicurezza (nessun dato reale, `service_role` mai nel client né nel repository, PR esterne riviste prima del merge).
- **Carattere:** interazione giocosa, mai esagerata. Colori e font vivaci, moderni, leggeri. Il gioco sta nei dettagli (mascotte negli stati vuoti, micro-animazioni, testi con un sorriso), non nel rallentare chi lavora: nessuna animazione blocca un'azione, tutte rispettano `prefers-reduced-motion`.
- **UI:** costruita su **Tailwind CSS** con un design system proprio: **shadcn/ui** (componenti Radix + Tailwind, copiati in `components/ui/` e quindi personalizzabili) con colori, font, raggi, ombre e animazioni definiti come *design token* (variabili CSS + tema Tailwind). Mai colori o misure "a mano" nei componenti.
- **Autenticazione e inviti fatti in casa:** Supabase Auth per le sole credenziali (email + password, recupero password, come Girasole); **organizzazioni, ruoli e inviti sono tabelle e codice nostri**, nessun servizio esterno di gestione utenti.
- **Qualità "stato dell'arte":** TypeScript `strict`, ESLint + Prettier, hook Git, Conventional Commits, validazione delle variabili d'ambiente con zod, accessibilità WCAG AA (contrasti, focus, tastiera), dipendenze aggiornate da Dependabot, analisi statica CodeQL, scansione segreti con gitleaks, controllo automatico sull'uso di `service_role`.
- **Test automatici, nessun end-to-end per ora:** (1) unit test Vitest sulla logica pura in `lib/`; (2) **test del database con pgTAP** (`supabase test db`) su uno stack Supabase locale in CI: provano RLS, GRANT, vincoli e isolamento tra tenant; (3) component test (Testing Library) per la UI con logica. Soglia di copertura alta sui moduli critici. Playwright/E2E: rimandato, non installato (Girasole li ha; qui si aggiungeranno in seguito).
- **Pipeline GitHub:** ogni PR esegue lint, typecheck, test, test del database, build e scansioni; `main` è protetto; Vercel crea una Preview per PR e pubblica `main` in produzione solo se la CI è verde. **Le migration in produzione non sono automatiche**: si applicano a mano con `--dry-run` e `--project-ref` esplicito, come in Girasole (ADR 0005); un workflow ricorda in PR che c'è una migration da applicare.

## Multi-tenancy sul database: opzioni valutate

| Opzione | Come funziona | Pro | Contro |
|---|---|---|---|
| **A. Database condiviso, schema condiviso** (`org_id` su ogni riga) + **Row Level Security** | Un solo schema; Postgres filtra le righe per tenant con policy | Semplice, economico, una sola migrazione per tutti, ottimo con tante piccole organizzazioni | L'isolamento dipende da policy e query corrette; backup/cancellazione di un solo tenant richiedono query dedicate |
| **B. Schema per tenant** | Un database, uno schema Postgres per organizzazione | Isolamento logico più netto, esportazione per tenant più facile | Le migrazioni vanno applicate a N schemi; `search_path` e pooling serverless sono delicati; PostgREST/supabase-js non lo gestiscono in modo naturale |
| **C. Database per tenant** | Un progetto Supabase per organizzazione | Isolamento massimo, backup/ripristino/cancellazione per tenant banali (GDPR) | Costo e complessità: N progetti, N migrazioni, registro dei tenant, query trasversali difficili |
| **D. Ibrido** | A di default, C per i tenant grandi o con requisiti contrattuali | Parti semplice e puoi "promuovere" un tenant | Due modalità da mantenere |

**Decisione (confermata): A con RLS.** Come si fa bene con Supabase, tenendo conto degli errori già incontrati in Girasole:
1. Tutte le tabelle di dominio hanno `org_id NOT NULL`, **RLS abilitata e forzata**, e policy basate sull'appartenenza dell'utente (`auth.uid()` presente in `memberships`). Niente `SET LOCAL`: l'utente arriva a Postgres con il proprio JWT.
2. Le regole sono in funzioni helper `SECURITY DEFINER` con `search_path` fisso (`is_member(org)`, `has_role(org, ruoli)`) per **evitare la ricorsione delle policy** (in Girasole: migration 0007 e 0014).
3. **Ogni migration che crea una tabella include nella stessa migration GRANT espliciti e policy** (in Girasole i GRANT dimenticati hanno richiesto 0004, 0008, 0021).
4. L'`org_id` non arriva mai dal client come fonte di verità: il server lo ricava dallo slug dell'URL e dalla membership; le policy `WITH CHECK` lo verificano comunque.
5. `service_role` solo lato server, solo in una lista breve di operazioni cross-tenant (accettare un invito, cron, leggere i segreti del tenant), con uno script `check:service-role` in CI che vieta l'import altrove (come Girasole).
6. Test pgTAP in CI che provano che A non legge né scrive su B, anche con query volutamente senza filtro.
7. Il codice accede ai dati da un solo livello (`lib/data/`): se un giorno serve promuovere un tenant a database dedicato (opzione D) si cambia solo quel punto.

## Scelte di architettura

| Tema | Scelta | Perché |
|---|---|---|
| Framework | **Next.js 16 (App Router) + TypeScript strict** | Come Girasole; target nativo di Vercel; UI e API in un solo progetto |
| UI / design system | **Tailwind CSS 4 + shadcn/ui (Radix)**, token personalizzati Sheepper, font con `next/font`, animazioni con Motion | Componenti accessibili e interamente personalizzabili |
| Database | **Supabase Postgres (Pro)**, migration SQL numerate in `supabase/migrations/` applicate con la Supabase CLI; nessun ORM | Come Girasole: SQL esplicito, RLS nativa, tipi generati con `supabase gen types` |
| Login | **Supabase Auth** (email + password, recupero password) | Già collaudato in Girasole; solo credenziali, il resto è nostro |
| Organizzazioni, ruoli, inviti | **Tabelle e codice nostri** (vedi step 3-4) | Nessuna dipendenza da servizi esterni di gestione utenti |
| Segreti dei tenant | Cifrati nel DB con **AES-256-GCM**; chiave master solo in variabile d'ambiente Vercel; leggibili solo da `service_role` lato server | Mai in chiaro, mai nei log, mai raggiungibili dal client |
| File/immagini | **Supabase Storage** (bucket privati, percorso `org_id/...`, policy per tenant, upload con URL firmato dal browser) | Un fornitore in meno; il limite di 4,5 MB sul body delle funzioni Vercel non conta |
| Testi AI | **API Anthropic** lato server, con le regole di `CLAUDE.md` come system prompt | Sostituisce gli agenti di Claude Code |
| Immagini → JPEG | **sharp** (Node) | Sostituisce `to_jpeg.py` (Pillow) |
| Job periodici | **Vercel Cron** (protetto da `CRON_SECRET`) | Come Girasole |
| Email transazionali | Da scegliere allo step 4 (SMTP personalizzato per Supabase Auth + invio inviti) | Serve per conferma email, recupero password, inviti |
| Test | **Vitest** + **pgTAP** (`supabase test db`) + **Testing Library**; nessun E2E | Vedi direttive |
| CI/CD | **GitHub Actions** + integrazione Git di **Vercel** (preview per PR, produzione da `main`) | Pipeline standard |
| Multi-tenancy | Opzione A, RLS forzata (vedi sopra) | Il modello più semplice e sicuro da mantenere per molte piccole organizzazioni |

Il codice Python attuale **non viene spostato**: resta nel repository `asilo-marketing` (sola lettura) come specifica e fonte dei dati da importare, finché Sheepper non ha la stessa funzionalità (step 13). Sheepper è un repository **nuovo**, creato da zero.

## Le regole di sicurezza non si perdono: diventano vincoli nel codice

Da `CLAUDE.md`, da portare **tali e quali** (con test automatici):
1. WordPress: solo `draft`/`pending`, mai `publish`/`future`, mai data, mai DELETE, mai modifica di contenuti esistenti.
2. Social: un canale e un post per volta, anteprima con **codice** (hash di canale + testo + immagine + alt), pubblicazione solo con `approvedCode` uguale; se qualcosa cambia il codice cambia.
3. Registro dei post usciti (oggi `social-esito.json`) → tabella `publications` con vincolo `UNIQUE(org_id, campaign_id, channel, code)`: impedisce il doppio invio.
4. L'ok è un'azione esplicita dell'utente (pulsante "Approvo e pubblico su Facebook" con riepilogo), registrata in un **audit log** (chi, quando, cosa, codice).
5. Titolo WordPress max 4 parole, estratto 3-4 parole.
6. Regola d'oro: l'AI usa solo i dati del brief; se mancano, la UI li chiede (campi obbligatori / "dati mancanti"), non li inventa.
7. Privacy: flag "consenso immagini" sul media; senza flag, avviso bloccante se la foto ritrae bambini.
8. Repository pubblico: niente credenziali, campagne, brand o dati dell'asilo nel codice; quei dati entrano solo da fuori (step 13).

---

## Step 0 — Decisioni e prerequisiti (mezza giornata)

Già deciso: multi-tenancy opzione A, Supabase + Vercel Pro, auth e inviti fatti in casa, repository pubblico `sheepper`, dominio `sheepper.vercel.app`.

1. **Supabase CLI e Docker:** installa Docker Desktop e la Supabase CLI (`npm install -g supabase`); servono per lo stack locale e per i test del database.
2. **Due progetti Supabase (Pro), regione UE (Francoforte):** `sheepper-prod` (produzione) e `sheepper-test` (usato dalle Preview di Vercel). Annota i *project ref*: non vanno mai salvati come link permanente (`supabase link`), si passano sempre con `--project-ref`.
3. **Vercel Pro:** nessun progetto da creare ora (si importa allo step 2).
4. **Anthropic Console:** crea una chiave API per Sheepper.
5. **Meta App** (decisivo, tempi lunghi): su developers.facebook.com crea un'app di tipo Business. Per far collegare **altre organizzazioni** via "Accedi con Facebook" servono i permessi `pages_show_list`, `pages_manage_posts`, `pages_read_engagement`, `instagram_basic`, `instagram_content_publish` con **Advanced Access**, quindi **App Review** + verifica dell'azienda. Può richiedere settimane: **avvia la richiesta ora**, in parallelo agli altri step. Finché non è approvata, ogni tenant incolla il proprio token di Pagina (come oggi): lo step 5 lo prevede.
6. **Email transazionali:** scegli un servizio di invio (SMTP) per conferma email, recupero password e inviti. Non blocca lo step 1: gli inviti partono comunque con link copiabile (step 4).
7. Raccogli per la revisione Meta: URL della privacy policy e dei termini (da scrivere nello step 14, ma serve una bozza pubblica).

**Fatto quando:** hai Docker e Supabase CLI funzionanti (`supabase --version`), i due progetti Supabase creati, la chiave Anthropic e la richiesta Meta avviata.

## Step 1 — Repository e scaffold (3 ore)

> Modo consigliato: crea il repository vuoto, aprilo in Claude Code, copia in `docs/` il file [bootstrap-progetto.md](bootstrap-progetto.md) di questo piano e incolla il blocco "Prompt" (con la sezione "Sheepper: parametri e deroghe"). L'agente esegue le Fasi A-D e ti elenca i passi manuali della Fase E. I punti sotto sono la sintesi di cosa deve risultare.

1. Crea una cartella nuova **fuori** da `asilo-marketing` (es. `C:/dev/sheepper`) e inizializza: `git init -b main`.
2. Scaffold: `npx create-next-app@latest . --ts --app --eslint --tailwind --import-alias "@/*"` (struttura alla radice, come Girasole: `app/`, `components/`, `lib/`, `supabase/`, `specs/`, `docs/`, `e2e/` assente per ora).
3. Dipendenze di runtime: `@supabase/ssr`, `@supabase/supabase-js`, `radix-ui`, `class-variance-authority`, `clsx`, `tailwind-merge`, `tw-animate-css`, `zod`, `sharp`, `@anthropic-ai/sdk`, `motion`. Regola come in Girasole: **nessuna nuova dipendenza senza chiederlo**.
4. Dipendenze di sviluppo: `vitest`, `@vitest/coverage-v8`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`, `msw`, `prettier`, `prettier-plugin-tailwindcss`, `jscpd`. Niente Husky: gli hook stanno in `.githooks/pre-push` e lo script npm `prepare` esegue `git config core.hooksPath .githooks`, come in Girasole. **Non** installare Playwright/Cypress.
5. Configura: `tsconfig` con `"strict": true` e `noUncheckedIndexedAccess`; script npm `lint` (ESLint + `check:service-role`), `typecheck`, `test:unit`, `test:db` (`supabase test db`), `check:dup` (jscpd), `analyze`, `format`. Hook pre-push: `tsc` → `lint` → `jscpd` → `vitest` → `next build`.
6. `supabase init`; crea `supabase/migrations/` e `supabase/tests/`.
7. Documentazione di progetto, sul modello di Girasole: `README.md` (cos'è Sheepper, setup locale), `AGENTS.md` (regole essenziali, con rimando a `docs/bootstrap-progetto.md`) e `CLAUDE.md` che contiene solo `@AGENTS.md` (regole essenziali: stack, convenzioni, test, **sicurezza del repository pubblico**, regole di sicurezza di questo piano), `docs/sviluppo-dettagli.md`, `docs/adr/` con i primi ADR (0001 multi-tenancy opzione A con RLS; 0002 auth e inviti fatti in casa; 0003 niente automazioni verso la produzione), `specs/00 - overview.md`, `LICENSE` (MIT), `.env.example` (solo nomi), `.gitignore` (`.env*` tranne l'esempio, `.next`, `coverage`, `supabase/.temp`). Copia da Girasole e adatta `.claude/agents/rls-guardian.md` e `.claude/commands/owasp-check.md`, se li vuoi.
8. Crea il repository **pubblico** e fai push: `gh repo create sheepper --public --source . --remote origin --push` (prima mostrami `git status` e controlla che non ci siano segreti o dati dell'asilo).
9. Proteggi `main`: Settings → Branches → richiedi PR, check CI verdi e branch aggiornato prima del merge; vieta il force push (disponibile gratis sui repository pubblici).

**Fatto quando:** `npm run dev` mostra la pagina iniziale, `npm run analyze` e `npm run build` passano in locale e il repository è su GitHub con `main` protetto.

## Step 1B — Identità e design system Sheepper (1-2 giorni)

1. **Logo:** disegna la pecora in SVG (`public/brand/sheepper-logo.svg`, `-mono.svg`, `-icon.svg`); da qui nascono favicon, icona app e immagine Open Graph. Forma semplice, riconoscibile a 16 px, con la lana a nuvola e il muso rotondo.
2. **Token di colore** in `app/globals.css` (token) (variabili CSS) mappati nel tema Tailwind; tema chiaro e scuro. Palette di partenza, **da affinare insieme guardando una pagina di prova** (i valori sono una proposta):
   - *Lana* `#FFF8EC` (sfondo caldo), *Inchiostro* `#1F2430` (testo)
   - *Mirtillo* `#5B5BD6` (primario), *Sole* `#FFC83D` (accento), *Corallo* `#FF6B5E` (errori/azioni delicate), *Prato* `#35B37E` (successo), *Cielo* `#6EC6FF` (informazioni)
   - Regola: ogni coppia testo/sfondo supera il contrasto WCAG AA; i colori vivaci sono per accenti e superfici piccole, mai per blocchi di testo lungo.
3. **Tipografia** con `next/font` (self-hosted, nessuna chiamata a Google a runtime): titoli in un rounded vivace (proposta: *Fredoka*), testo in un sans leggibile e moderno (proposta: *Nunito Sans* o *Inter*). Scala tipografica definita nei token.
4. **Forme e movimento:** raggi generosi (12-16 px), ombre morbide, transizioni 150-250 ms. Micro-interazioni sobrie con Motion: pulsante che "rimbalza" appena al click, la pecora che saltella nei caricamenti ("sto contando le pecore…"), coriandoli leggeri quando un post esce con successo. Tutte disattivate con `prefers-reduced-motion`.
5. **Voce dei testi dell'interfaccia:** italiano semplice, con un tocco di ironia sulle pecore dove non intralcia ("Nessuna campagna ancora. Il gregge aspetta."), mai sulle azioni critiche: pubblicazione e credenziali hanno testi chiari e seri.
6. **Componenti base** con shadcn/ui, personalizzati: Button, Input, Textarea, Select, Dialog, Toast, Tabs, Badge, Card, Table, Skeleton, EmptyState (con la mascotte). Pagina `/design` (solo in sviluppo) che li mostra tutti, in chiaro e scuro.
7. **Test:** component test dei componenti con logica (Dialog di conferma, contatori parole) e test automatico che le coppie di colori dei token rispettino il contrasto AA.

**Fatto quando:** la pagina `/design` mostra logo, palette, tipografia e componenti in tema chiaro e scuro, approvata da te; i test di contrasto passano in CI.

## Step 2 — Pipeline CI/CD e ambienti (3 ore)

1. **GitHub Actions** (`.github/workflows/ci.yml`), su ogni PR e push su `main`, con cache npm e `concurrency` per annullare le esecuzioni superate. Job:
   - `quality`: `npm ci` → `npm run lint` → `npm run typecheck` → `npm run check:dup` → `npm run format -- --check`;
   - `unit`: `npm run test:unit -- --coverage` con soglie sui moduli critici;
   - `db`: installa la Supabase CLI (`supabase/setup-cli`), `supabase start`, `supabase db reset` (applica tutte le migration), `supabase test db` (pgTAP), verifica che i tipi generati siano aggiornati (`supabase gen types` senza differenze);
   - `build`: `npm run build`;
   - `security`: gitleaks, `npm audit --omit=dev --audit-level=high`, CodeQL.
2. **Vercel:** Import Project dal repository GitHub (radice del repository), piano Pro. Produzione = branch `main`; ogni PR genera una **Preview**. Configura il dominio `sheepper.vercel.app` (o il primo disponibile).
3. Variabili d'ambiente su Vercel (mai nel repository), separate per ambiente. **Production → progetto `sheepper-prod`; Preview → progetto `sheepper-test`**:
   - `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` (pubbliche per design: la difesa è la RLS)
   - `SUPABASE_SERVICE_ROLE_KEY` (segreto vero, solo server, mai `NEXT_PUBLIC_`)
   - `APP_ENCRYPTION_KEY` (32 byte base64: `openssl rand -base64 32`; diversa per ogni ambiente)
   - `ANTHROPIC_API_KEY`, `CRON_SECRET`
   - `META_APP_ID`, `META_APP_SECRET` (step 12); variabili del servizio email (step 4)
   - Verifica con zod all'avvio che tutte le variabili obbligatorie siano presenti.
4. **Migrazioni:** niente automazioni verso la produzione. In locale `supabase db push --project-ref <ref-test> --dry-run`, poi senza `--dry-run`; in **produzione le applichi tu a mano** subito dopo il merge di una PR con migration (prima `--dry-run`, mai dal SQL Editor). Un workflow `promemoria-migration.yml` commenta la PR quando contiene file in `supabase/migrations/`.
5. Abilita Dependabot (npm + GitHub Actions) e fai in modo che la produzione parta solo da `main` con CI verde (branch protection + Vercel Deployment Checks). Nessun test E2E in pipeline per ora.

**Fatto quando:** una PR di prova mostra i check verdi e un URL di preview funzionante collegato a `sheepper-test`; il merge su `main` pubblica in produzione.

## Step 3 — Modello dati multi-tenant (1-1,5 giorni)

Migration SQL numerate in `supabase/migrations/` (`0001_init.sql`, …), una per argomento, ognuna con tabelle **+ GRANT + RLS + policy** insieme. Tutte le tabelle di dominio hanno `org_id uuid NOT NULL`.

- `profiles` (id = `auth.users.id`, nome, cognome; creato da trigger alla registrazione)
- `organizations` (id, nome, slug univoco, creata il)
- `memberships` (org_id, user_id, **ruolo**: `owner` | `approver` | `editor` | `viewer`; PK `(org_id, user_id)`)
- `invitations` (id, org_id, email, ruolo, `token_hash`, `expires_at`, `invited_by`, `accepted_at`, `revoked_at`) — vedi step 4
- `org_settings` (org_id, chiave, valore; i segreti **cifrati** e senza SELECT per `authenticated`) — vedi step 5
- `brand_profiles` (org_id, tono di voce, linee guida, hashtag, firma, logo)
- `campaigns` (org_id, nome, slug, stato `bozza|approvato|pubblicato`, data evento, brief in JSON)
- `contents` (org_id, campaign_id, canale, testo, versione, stato)
- `media` (org_id, campaign_id, percorso Storage, alt text, `consenso_immagini`, origine/derivato)
- `publications` (org_id, campaign_id, canale, codice anteprima, id esterno, URL, stato, data, `UNIQUE(org_id, campaign_id, canale, codice)`)
- `audit_log` (org_id, user_id, azione, oggetto, dettagli senza segreti, data; solo INSERT e SELECT per i ruoli ammessi)

**Isolamento (opzione A, vedi sopra):** funzioni `is_member(org)` e `has_role(org, ruoli)` `SECURITY DEFINER` con `search_path` fisso; RLS abilitata e `FORCE` su ogni tabella; policy che usano solo quelle funzioni; GRANT espliciti per `authenticated` e, dove serve, `service_role`. Un'organizzazione si crea con una funzione SQL (`create_organization(nome, slug)`) che inserisce anche la membership `owner` in modo atomico. Genera i tipi: `supabase gen types typescript --local > lib/database.types.ts`.

**Specs e test:** per ogni tabella uno scenario in `specs/` e un test pgTAP in `supabase/tests/` (viewer legge ma non scrive; editor non pubblica; utente senza membership non vede nulla; tentativo di scrivere con `org_id` di un'altra org fallisce).

**Fatto quando:** `supabase db reset` applica tutto, `supabase test db` è verde e un test dimostra che l'org A non legge né scrive righe dell'org B, nemmeno con query volutamente senza filtro.

## Step 4 — Autenticazione, organizzazioni, ruoli e inviti (3-4 giorni)

**Login (come Girasole):** pagine `/login`, `/registrati`, `/recupera-password`, `/reimposta-password`, route `/auth/callback`; Supabase Auth con email + password; regola di complessità della password in `lib/password.ts` (logica pura, testata). `proxy.ts` (Next 16) rinfresca la sessione e protegge `/app/**`. Registrazione aperta con conferma via email; chi si registra senza invito crea la propria organizzazione e ne diventa `owner` (la registrazione si potrà restringere con un'impostazione globale).

**Inviti fatti in casa:**
1. Un `owner` apre "Persone" → "Invita": indica email e ruolo.
2. Il server genera un token casuale (32 byte, `crypto.randomBytes`), salva **solo l'hash SHA-256** in `invitations` (scadenza 7 giorni) e mostra il link `https://…/invito/<token>`, **copiabile**. Se il servizio email è configurato, lo invia anche per email. Il token in chiaro non viene mai salvato né loggato.
3. `/invito/<token>`: il server cerca l'hash; se manca, è scaduto, revocato o già usato, mostra un messaggio chiaro. Se l'utente non è loggato: login o registrazione con l'email dell'invito precompilata e non modificabile. L'email dell'account **deve coincidere** con quella dell'invito.
4. Accettazione = server action con `service_role` (lista breve e dichiarata): in una transazione crea la membership e imposta `accepted_at`; un secondo uso dello stesso link non fa nulla.
5. L'owner può revocare, rigenerare e vedere gli inviti pendenti. Rate limit sul controllo del token. Ogni azione scrive in `audit_log`.
6. Regole sui ruoli: `viewer` legge; `editor` crea campagne e testi; `approver` e `owner` danno l'ok di pubblicazione; solo `owner` gestisce impostazioni, segreti e persone; **l'ultimo owner non si può rimuovere né declassare**. La matrice permessi è in `lib/permessi.ts` (pura, testata) ed è la stessa che riflettono le policy RLS.

**Navigazione:** rotte `/app/[orgSlug]/...`; il layout verifica la membership e carica il ruolo; selettore organizzazione in testata per chi appartiene a più tenant.

**Test:** unit sui moduli puri (`lib/inviti.ts`: generazione token, hash, scadenza, validazione; `lib/permessi.ts`; `lib/password.ts`); pgTAP sulle policy di `invitations` e `memberships` (un editor non può invitare né promuoversi; l'ultimo owner non si rimuove).

**Fatto quando:** due utenti in due organizzazioni diverse vedono solo i propri dati; un invito creato da un owner viene accettato da un nuovo utente con la stessa email e non da un'altra; un `editor` non vede il pulsante di pubblicazione e l'API risponde 403 se forzata.

## Step 5 — Impostazioni al posto di `config.yaml` (1-2 giorni)

Mappa delle chiavi attuali → impostazioni per tenant (pagina `/app/[org]/impostazioni`, solo `owner`):

| Oggi (`config.yaml`) | Nella web app | Segreto |
|---|---|---|
| `wp_url` | WordPress → URL del sito (solo `https://`) | no |
| `wp_user` | WordPress → utente | no |
| `wp_app_password` | WordPress → Application Password | **sì** (cifrata, mostrata solo come `…ab12`) |
| `categoria_default`, `categoria_slider` | WordPress → categorie | no |
| `fb_page_id` | Facebook → ID Pagina | no |
| `fb_page_token` | Meta → token Pagina | **sì** |
| `ig_user_id` | Instagram → ID account | no |
| `graph_version` | Impostazione globale dell'app (non per tenant) | no |

Comportamento richiesto:
1. I segreti sono **write-only**: dopo il salvataggio non vengono mai restituiti al browser, solo un'indicazione "impostato, finisce con …ab12".
2. Pulsante **"Verifica collegamento"** per ogni servizio (porta di `check_setup.py`/`--check`): esegue le chiamate in sola lettura, mostra esito, permessi e **scadenza del token**.
3. Cifratura/decifratura in un solo modulo (`lib/crypto.ts`, AES-256-GCM, nonce casuale per valore, versione della chiave salvata per permettere la rotazione).
4. Ogni modifica alle impostazioni scrive in `audit_log` (senza valori segreti).
5. Impostazioni di brand per tenant (tono, hashtag, firma, logo): precompilate da `brand/linee-guida.md` e `brand/hashtag.md` per il tenant "Asilo Sartorio", editabili; per i nuovi tenant parte un wizard.

**Fatto quando:** un owner inserisce le credenziali, preme "Verifica" e vede l'esito; un secondo owner di un'altra org non può in alcun modo leggerle; un test verifica che nei log e nelle risposte API non compaia mai un segreto.

## Step 6 — Porting della logica core in TypeScript (3-4 giorni)

Crea `lib/` con moduli puri, **testati con Vitest** prima di collegarli alla UI:

| Python | TypeScript | Test chiave |
|---|---|---|
| `publish_post.py` | `lib/wordpress.ts` (REST API, dry-run, ricerca categorie/tag, controllo slug duplicato, upload media) | stato `publish`/`future` rifiutato; titolo >4 parole rifiutato; estratto assente o >4 parole rifiutato; mai invio di `date` |
| `publish_social.py` | `lib/facebook.ts`, `lib/instagram.ts`, `lib/approval-code.ts` | codice cambia se cambia testo/immagine/alt; pubblicazione rifiutata con codice sbagliato o già usato |
| `to_jpeg.py` | `lib/image.ts` (sharp: trasparenza su bianco, niente EXIF, 1440 px max, `padTo` 4:5 senza ritaglio) | proporzioni in uscita 4:5; nessun metadato |
| `upload_media.py` | `lib/wordpress.ts#uploadMedia` | nessuna sostituzione di media con lo stesso nome |
| `check_setup.py` | `lib/health.ts` | token vicino a scadenza → avviso sotto 14 giorni |
| `stato_campagne.py` | query SQL | — |

Usa i docstring degli script in `asilo-marketing/scripts/` come specifica: ogni vincolo dei docstring degli script diventa un test. Le chiamate HTTP verso WordPress/Meta si testano con mock (MSW); **mai** contro i siti reali nei test.

**Fatto quando:** la suite Vitest copre tutti i vincoli di sicurezza elencati sopra ed è verde in CI.

## Step 7 — Campagne e brief (UI) (3-4 giorni)

1. Elenco campagne con stato e canali (equivale a `/stato`).
2. **Wizard "Nuova campagna"** (equivale a `/nuova-campagna`): form con i campi del `templates/brief.md` — evento, data, ora, luogo, hashtag, costi/contatti, locandina, obiettivo, pubblico, titolo (max 4 parole, contatore), estratto (3-4 parole, contatore), categoria, tag, testo alternativo. I campi mancanti restano visibili come "Dati mancanti da chiedere".
3. Il brief è la **fonte unica**: modificarlo marca i testi derivati come "da rigenerare".
4. Checklist pre-pubblicazione per canale (da `templates/checklist.md`) e pagina "Esito" (da `templates/esito.md`), compilate dall'app.
5. Canali WhatsApp e Luino Notizie: l'app genera il testo e offre "Copia" / "Scarica .md"; non invia nulla.

**Fatto quando:** dal browser si crea una campagna completa con brief salvato e visibile solo all'organizzazione.

## Step 8 — Generazione testi con AI (2-3 giorni)

1. Server action che chiama l'API Anthropic con: system prompt = regole di `CLAUDE.md` (tu, tono, regola d'oro, privacy) + profilo di brand **del tenant**; user = solo il brief. Modello: usa il più recente disponibile (verifica gli ID attuali nella documentazione Anthropic al momento dell'implementazione).
2. Prompt per canale presi da `.claude/agents/marketing-strategist.md` e `social-publisher.md` (articolo 100-150 parole, Facebook, Instagram, WhatsApp, Luino Notizie).
3. **Guardrail post-generazione** (validatori deterministici, non fidarsi del modello): nessun segnaposto `[...]`; date/orari/prezzi/contatti presenti nel testo devono comparire nel brief (altrimenti avviso rosso); lunghezze per canale; titolo/estratto entro i limiti.
4. Ogni testo ha versioni e può essere modificato a mano; lo "stato" resta `bozza` finché qualcuno non approva.
5. Limiti di consumo per tenant (richieste/giorno) e registrazione dei token usati.

**Fatto quando:** da un brief si ottengono i testi di tutti i canali; un test con brief incompleto produce la richiesta dei dati mancanti, non testo inventato.

## Step 9 — Flussi di pubblicazione con anteprima e ok (3-4 giorni)

1. **Sito (WordPress):** pulsante "Anteprima bozza" (= `--dry-run`) → schermata con titolo, slug, categorie, tag, estratto, immagine, alt, contenuto, parole → "Approvo: crea la bozza su WordPress" → bozza creata, mostra ID e link di modifica. Promemoria: "Pubblica" lo preme l'utente in WordPress.
2. **Facebook / Instagram:** anteprima con codice → pulsante dedicato per **ciascun canale** ("Approvo e pubblico su Facebook") → server verifica ruolo `approver`+, ricalcola il codice, controlla il vincolo `UNIQUE`, pubblica, registra in `publications` e `audit_log`.
3. Errore di rete durante la pubblicazione: stato `incerto`, la UI avvisa di **controllare prima sulla Pagina** e blocca il reinvio automatico (come oggi).
4. Instagram: se l'immagine non è JPEG 4:5, l'app la converte (sharp), chiede l'ok per il file, la carica sulla libreria media di WordPress per ottenere l'URL pubblico; poi anteprima e ok. Polling dello stato del container Instagram con `maxDuration` adeguato della funzione.
5. Nessuna programmazione, modifica o eliminazione di post esistenti: queste funzioni **non esistono** nell'app.

**Fatto quando:** in un tenant di prova (sito WordPress di test + Pagina/IG di test) si completano i tre flussi; un secondo clic non duplica il post; un `editor` non può pubblicare.

## Step 10 — Media e privacy (1-2 giorni)

1. Upload diretto dal browser a Supabase Storage (URL firmato), con tipi e dimensioni ammessi; il percorso inizia con `org_id/` e le policy dello Storage lo verificano.
2. Gli originali non si modificano: la conversione crea un **derivato** (`locandina-ig.jpg`).
3. Campo obbligatorio **testo alternativo** e flag **consenso immagini** per ogni media con persone; senza consenso, blocco alla pubblicazione.
4. Rimozione dei metadati EXIF/GPS in ogni derivato.

**Fatto quando:** non si può pubblicare un media senza alt; il file di un tenant non è raggiungibile dalle API di un altro.

## Step 11 — Monitoraggio, cron, notifiche (1 giorno)

1. **Vercel Cron** giornaliero (`/api/cron/token-check`, protetto da `CRON_SECRET`): per ogni tenant legge la scadenza del token Meta e, sotto 14 giorni o se invalido, manda email all'owner.
2. Promemoria sulle scadenze di comunicazione (annuncio ~2-3 settimane prima, promemoria 1 settimana, ultimo 1-2 giorni): sostituisce `/calendario`; il modello con le ricorrenze annuali è `templates/calendario.md`.
3. Log strutturati **senza dati personali né segreti**; error tracking (Sentry o simile, con scrubbing dei campi sensibili).

**Fatto quando:** un token di prova in scadenza genera l'email; nei log di prova non compare alcun segreto.

## Step 12 — "Collega con Facebook" (OAuth Meta) (2-3 giorni, dopo l'approvazione Meta)

1. Sostituisce l'incolla manuale del token: l'owner clicca "Collega Facebook", sceglie la Pagina e l'account Instagram collegato; l'app ottiene il token di Pagina di lunga durata e lo salva cifrato.
2. Rotte: `/api/meta/connect` (redirect), `/api/meta/callback` (scambio codice → token, `state` anti-CSRF legato a utente e org).
3. Webhook/endpoint obbligatori per Meta: **cancellazione dati** e **deautorizzazione** (cancellano i token del tenant).
4. Fino all'approvazione, resta attivo l'inserimento manuale del token (step 5).

**Fatto quando:** un owner collega da zero Pagina e Instagram senza vedere un token.

## Step 13 — Migrazione dei dati esistenti e parità (2-3 giorni)

1. Crea il tenant **Asilo Sartorio** e inserisci le impostazioni dall'interfaccia (non importare `config.yaml` da file nel repository).
2. **Ruota le credenziali** al passaggio: nuova Application Password WordPress e nuovo token Meta, revoca delle vecchie (erano in un file su Drive).
3. Script di importazione una tantum (`scripts/import-legacy.ts`, eseguito in locale, non in produzione) che legge `campagne/*/brief.md`, `testi/`, `esito.md` e `social-esito.json` e li inserisce nel DB, **compresi i registri dei post già usciti** (così la Castagnata non può essere ripubblicata).
4. Parità: una campagna di prova end-to-end con entrambi i sistemi (vecchio in `--dry-run`, nuovo in anteprima) deve produrre la stessa anteprima.
5. Archivia il repository `asilo-marketing` (tag `legacy-final`, poi archiviazione su GitHub).

**Fatto quando:** la prossima campagna reale dell'asilo si fa solo dalla web app.

## Step 14 — Hardening e lancio multi-tenant (2-3 giorni)

1. **Privacy e legale:** privacy policy, termini, informativa sui dati trattati; elenco sub-responsabili (Vercel, Supabase, Anthropic, Meta, servizio email); esportazione e cancellazione dei dati di un tenant su richiesta (GDPR).
2. **Sicurezza:** rate limiting sulle API (login, pubblicazione, AI); header di sicurezza (CSP); controllo che nessuna rotta accetti `org_id` dal client; test di penetrazione di base sull'isolamento tra tenant; rotazione di `APP_ENCRYPTION_KEY` documentata e provata.
3. **Backup:** backup di Supabase attivi (valuta l'add-on Point-in-Time Recovery); prova di ripristino.
4. **Onboarding nuovi tenant:** guide `docs/` riscritte per l'utente finale (collegare WordPress e Meta dall'interfaccia), checklist di avvio.
5. **Piani/limiti** per tenant (campagne, generazioni AI, utenti) se serve fatturare.
6. Aggiorna `CLAUDE.md` e `README.md`: il progetto ora è la web app; le regole di sicurezza restano valide ma sono implementate nel codice.

**Fatto quando:** un'organizzazione nuova, mai vista, completa da sola registrazione → collegamento canali → prima bozza WordPress di prova in meno di un'ora.

---

## Ordine e tempi indicativi

Step 0-2 e 1B: 3-4 giorni · Step 3-5: 1,5-2 settimane · Step 6-8: 1,5-2 settimane · Step 9-11: 1 settimana · Step 12: dipende da Meta · Step 13-14: 1 settimana. Totale ≈ **6-8 settimane di lavoro**, con il vincolo esterno della revisione Meta (da avviare subito).

Rischi principali: tempi dell'App Review di Meta; limiti di durata/dimensione delle funzioni Vercel (mitigati da Storage con upload diretto e `maxDuration`); fuga di segreti (mitigata da cifratura, write-only, scansione in CI); errori di isolamento tra tenant (mitigati da RLS forzata, GRANT espliciti, `check:service-role` e test pgTAP).
