---
description: Mostra a che punto sono le campagne (stato, canali, file e dati mancanti). Sola lettura.
argument-hint: [campagna, facoltativo]
---

Mostra lo stato delle campagne: $ARGUMENTS (se vuoto, tutte).

1. Esegui `python scripts/stato_campagne.py $ARGUMENTS` (sola lettura, senza rete).
2. Leggi anche `calendario.md` (se esiste) e segnala le scadenze imminenti senza una campagna.
3. Riassumi in 5-8 righe: cosa è pubblicato, cosa è ancora in bozza, cosa blocca (dati mancanti, checklist assente, ok da dare) e il prossimo passo consigliato.

Non modificare file e non pubblicare nulla. Per procedere indica il comando giusto (`/pubblica-bozza`, `/pubblica-social`, `/calendario`).
