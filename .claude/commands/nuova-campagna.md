---
description: Crea una nuova campagna (cartella, brief e bozze dei testi per ogni canale). Non pubblica nulla.
argument-hint: [nome evento, facoltativo]
---

Crea una nuova campagna di comunicazione per Asilo Sartorio. Argomento (può essere vuoto): $ARGUMENTS

Leggi prima `CLAUDE.md`, `brand/linee-guida.md`, `brand/hashtag.md` e i template in `templates/`.

## 1. Raccogli i dati (non inventare nulla)
Chiedimi, in un solo messaggio raggruppato, ciò che non so già:
- nome dell'evento/iniziativa;
- data, ora, luogo;
- dettagli: programma, costi, prenotazioni, contatti, cosa succede in caso di maltempo, hashtag;
- asset: locandina, foto (percorsi; guarda anche in `..\..\02 - Comunicazione e Locandine\ANNO\`; se ce n'è più di una, chiedi quale);
- obiettivo e pubblico;
- canali da usare: sito, Facebook, Instagram, WhatsApp, Luino Notizie;
- per il sito: slider sì/no, tag.
Se un dato manca, scrivilo in "Dati mancanti da chiedere" del brief e non riempirlo tu.

## 2. Crea la struttura
- `campagne/AAAA-nome-in-minuscolo-con-trattini/` con `brief.md` (da `templates/brief.md`), `testi/`, `immagini/` (copia lì la locandina/foto: gli originali non si toccano), `checklist.md` (da `templates/checklist.md`) ed `esito.md` (da `templates/esito.md`).
- Il file per Luino Notizie va in `luino-notizie/AAAA-nome.md`.

## 3. Scrivi le bozze
1. Usa l'agente `marketing-strategist` per messaggio, articolo (100-150 parole, HTML semplice), WhatsApp e mail Luino Notizie.
2. Usa l'agente `social-publisher` per adattare i post Facebook/Instagram, preparare titolo (max 4 parole) ed estratto (3-4 parole), slug, testo alternativo in italiano e la `checklist.md`.
3. Se gli agenti non sono disponibili in questa sessione, applica tu le loro regole (sono in `.claude/agents/`).

## 4. Mostrami tutto in anteprima in chat
Riepilogo con: dati usati, dati mancanti, testi per canale, avvisi (es. date incoerenti). Poi fermati.

## Regole
- Tutto resta BOZZA: niente pubblicazioni, invii o post. Per WordPress si usa solo `/pubblica-bozza`, per Facebook/Instagram solo `/pubblica-social`: sempre con anteprima e mio ok esplicito.
- Nel brief scrivi sempre il testo alternativo in italiano della locandina: lo usano sito, Facebook e Instagram.
- Aggiorna `calendario.md` solo se te lo chiedo (usa `/calendario`).
