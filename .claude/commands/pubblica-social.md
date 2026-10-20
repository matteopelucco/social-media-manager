---
description: Pubblica un post di una campagna su Facebook o Instagram, sempre con anteprima e ok esplicito per canale.
argument-hint: <cartella campagna> <facebook|instagram>
---

Pubblica il post della campagna sul canale indicato: $ARGUMENTS
(se manca la campagna, elenca le cartelle in `campagne/` e chiedimi quale; se manca il canale, chiedimelo. Un canale per volta.)

Leggi `CLAUDE.md`, `campagne/<campagna>/brief.md`, `testi/post-social.md` (o `post-facebook.md` / `post-instagram.md`) e `checklist.md`.

## 1. Controlli (fermati e chiedi se uno fallisce)
- Il brief è `approvato` e la checklist non ha voci aperte per quel canale.
- Il testo non ha segnaposto `[...]`; data, ora e luogo coincidono con brief e locandina.
- Nessun nome o volto riconoscibile di bambini senza consenso immagini.
- Se il testo rimanda all'articolo del sito: l'articolo è già pubblicato (lo pubblico io). Se non lo è, il link non va nel post.
- Testo alternativo in italiano presente nel brief o nel file.
- `python scripts/publish_social.py --check` va a buon fine (solo se non già fatto in questa sessione).
- **Instagram:** serve un URL https pubblico di un'immagine **JPEG** (di solito il media già caricato su WordPress). Se l'immagine è PNG o ha proporzioni fuori range, convertila con `python scripts/to_jpeg.py <immagine> --pad-to 4:5`, poi dimmi che il JPG va caricato sul sito (non caricarlo senza il mio ok) e usa l'URL ottenuto.

## 2. Anteprima
Esegui `scripts/publish_social.py` **senza** `--publish`:
`--channel <facebook|instagram> --campaign <campagna>` più `--image <file>` (solo Facebook) oppure `--image-url <https://...>`.
Il testo lo prende da `testi/post-<canale>.md` o dalla sezione del canale in `post-social.md`; il testo alternativo lo prende dal brief. Usa `--text-file`, `--from-md`/`--section` o `--alt` solo se servono eccezioni. L'anteprima dice da dove vengono testo e alt: verificalo.

Mostrami l'anteprima completa e il **CODICE ANTEPRIMA**, poi **fermati**.

## 3. Conferma
Procedi solo con un mio OK esplicito in chat per **quel canale e quel testo** (es. "ok, pubblica su Facebook"). Un ok per Facebook non vale per Instagram. Se testo, immagine o alt cambiano, rifai l'anteprima: il codice cambia e serve un nuovo ok.

## 4. Pubblica
Rilancia lo stesso comando con `--publish --approved-code <codice>`. Poi:
- riporta ID del post e conferma l'esito;
- aggiorna `campagne/<campagna>/esito.md` con canale, ID, data e ora (il registro `social-esito.json` lo scrive lo script) e la checklist (ok ricevuto: chi, quando);
- ricordami che il post è già online: per correzioni o eliminazione vado io su Facebook/Instagram.

## Regole
- Un solo canale e un solo post per esecuzione. Mai programmare, modificare o eliminare post esistenti.
- Mai usare `--publish` senza anteprima approvata nello stesso turno di conversazione. Mai lanciare `--publish` "per prova": l'unico test ammesso è l'anteprima.
- Non leggere né stampare `config.yaml`; il token non va mai in chat né nei log.
- Se l'API risponde con un errore (token scaduto, permessi, limiti): fermati, spiega, non aggirare nulla. Dopo un errore di rete durante la pubblicazione, **controlla prima sulla Pagina se il post è uscito**, poi eventualmente riprova.
- WhatsApp e Luino Notizie non passano da qui: restano file `.md` che spedisco io.
