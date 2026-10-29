---
description: Controlla che il progetto sia pronto (Python, librerie, config, collegamenti, scadenza token). Sola lettura.
---

Verifica che il progetto sia pronto all'uso.

1. Esegui `python scripts/check_setup.py` (sola lettura: non pubblica e non scrive nulla; non stampa credenziali).
2. Riassumi in poche righe: cosa funziona, cosa manca, e **quanti giorni restano al token Facebook/Instagram** (se scade, indicalo in evidenza).
3. Per ogni problema indica la guida: `docs/setup-wordpress.md` o `docs/setup-meta.md`, oppure `python -m pip install --user -r requirements.txt` se mancano librerie.

Non leggere né stampare `config.yaml`. Se un controllo fallisce: spiega e fermati, senza aggirare nulla.
