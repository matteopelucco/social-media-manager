---
description: Porta in BOZZA su WordPress l'articolo di una campagna, sempre con dry-run e conferma esplicita.
argument-hint: <cartella campagna, es. 2026-castagnata>
---

Porta in bozza su WordPress il contenuto della campagna: $ARGUMENTS
(se l'argomento è vuoto, elenca le cartelle in `campagne/` e chiedimi quale.)

Leggi `CLAUDE.md` e `campagne/<campagna>/brief.md`.

## 1. Controlli (fermati e chiedi se uno fallisce)
- `testi/articolo-blog.html` esiste, non ha segnaposto `[...]`, ha 100-150 parole.
- Nel brief: titolo (max 4 parole), slug, estratto (3-4 parole, obbligatorio), categoria, tag, immagine in evidenza, testo alternativo in italiano.
- Data, ora e luogo dell'articolo coincidono con quelli del brief e della locandina.
- Esiste già un articolo con lo stesso slug? (lo script lo controlla: non modifico mai articoli esistenti).
- `python scripts/publish_post.py --check` va a buon fine (solo se non è già stato fatto in questa sessione).

## 2. Dry-run
Esegui `scripts/publish_post.py` con `--dry-run` e i dati del brief:
`--title`, `--content-file`, `--image`, `--alt`, `--category`, `--tags`, `--excerpt`, `--slug`.
- `--slider` solo se il brief o io lo abbiamo confermato.
- `--create-tags` solo se ho autorizzato la creazione dei tag mancanti.
- Non usare mai `--status` diverso da `draft` (lo script rifiuta `publish`/`future`).

Mostrami l'anteprima completa (titolo, slug, categorie, tag, estratto, immagine, testo alternativo, contenuto, parole) e **fermati**.

## 3. Conferma
Procedi solo con un mio OK esplicito in chat per questo contenuto (es. "ok, crea la bozza su WordPress"). Se cambi qualcosa dopo l'anteprima, rimostra e richiedi l'ok.

## 4. Crea la bozza
Lancia lo stesso comando senza `--dry-run`. Poi:
- riporta ID, link di anteprima e link di modifica;
- aggiorna `campagne/<campagna>/esito.md` (ID articolo, media ID, data) e lo stato nel `brief.md`;
- ricordami che "Pubblica" lo premo io in WordPress.

## Regole
- Mai pubblicare, programmare, eliminare o modificare contenuti esistenti.
- Non leggere né stampare `config.yaml`.
- Se l'API è bloccata o l'autenticazione fallisce: fermati, spiega perché, non aggirare nulla.
- Facebook e Instagram non passano da qui: si usa `/pubblica-social`. WhatsApp e Luino Notizie restano file `.md` che spedisco io.
- Se serve un'immagine per Instagram (JPEG 4:5 con URL pubblico): `scripts/to_jpeg.py` e `scripts/upload_media.py`, ma solo dopo mio ok esplicito per quel file.
