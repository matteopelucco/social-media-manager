#!/usr/bin/env python3
"""Carica UN'immagine nella libreria media di WordPress (asilosartorio.it) e ne stampa l'URL pubblico.

Serve soprattutto per Instagram, che vuole un URL https pubblico (--image-url di publish_social.py).

Sicurezza (vincoli nel codice):
  - solo POST di un nuovo file media e del suo testo alternativo; nessun articolo creato o modificato;
  - se esiste già un media con lo stesso nome file (slug) si ferma: non sostituisce né duplica;
  - niente DELETE; formati ammessi: jpg, png, webp, gif; testo alternativo obbligatorio;
  - la password non viene mai stampata. Con --dry-run non scrive nulla.

Credenziali: le stesse di publish_post.py (config.yaml o WP_URL, WP_USER, WP_APP_PASSWORD).

Esempio:
  python scripts/upload_media.py campagne/2026-castagnata/immagini/locandina-ig.jpg \
      --alt "Locandina della Castagnata 2026: ..." --title "Castagnata 2026 (Instagram)" --dry-run
"""
import argparse
import mimetypes
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import requests  # noqa: E402
import publish_post as pp  # noqa: E402  (riuso config, auth e gestione errori)


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Carica un'immagine nei media di WordPress e stampa l'URL.")
    p.add_argument("image", help="file immagine (jpg/png/webp/gif)")
    p.add_argument("--alt", required=True, help="testo alternativo in italiano (obbligatorio)")
    p.add_argument("--title", help="titolo del media (default: nome file)")
    p.add_argument("--dry-run", action="store_true", help="controlla tutto senza caricare")
    args = p.parse_args()

    path = Path(args.image)
    if not path.is_file():
        pp.fail(f"File non trovato: {path}")
    mime = mimetypes.guess_type(path.name)[0]
    if mime not in pp.IMAGE_TYPES:
        pp.fail(f"Formato non supportato ({mime}). Usa jpg, png, webp o gif.")
    if not args.alt.strip():
        pp.fail("--alt non può essere vuoto.")
    filename = pp.safe_filename(path)
    slug = Path(filename).stem
    title = args.title or slug

    cfg = pp.load_config()
    if not cfg.get("wp_url"):
        pp.fail("wp_url non impostato.")
    pp.require_credentials(cfg)

    try:
        dup = requests.get(pp.api(cfg, "media"), params={"slug": slug, "_fields": "id,source_url"},
                           auth=pp.auth(cfg), timeout=pp.TIMEOUT)
        if dup.status_code != 200:
            pp.explain_http(dup, "Controllo duplicati media")
        if dup.json():
            pp.fail(f"Esiste già un media con nome '{slug}' (id {dup.json()[0]['id']}): {dup.json()[0]['source_url']}\n"
                    "Non lo sostituisco. Cambia nome al file se vuoi caricarne un altro.")

        print(f"File       : {filename} ({path.stat().st_size // 1024} KB, {mime})")
        print(f"Titolo     : {title}")
        print(f"Testo alt  : {args.alt.strip()}")
        if args.dry_run:
            print("Dry-run terminato. Nessun file caricato.")
            return

        with path.open("rb") as fh:
            r = requests.post(pp.api(cfg, "media"), data=fh, auth=pp.auth(cfg), timeout=120,
                              headers={"Content-Type": mime,
                                       "Content-Disposition": f'attachment; filename="{filename}"'})
        if r.status_code not in (200, 201):
            pp.explain_http(r, "Caricamento media")
        media = r.json()
        mid = media["id"]
        r = requests.post(pp.api(cfg, f"media/{mid}"), json={"alt_text": args.alt.strip(), "title": title},
                          auth=pp.auth(cfg), timeout=pp.TIMEOUT)
        if r.status_code != 200:
            print(f"ATTENZIONE: media caricato (id {mid}) ma testo alternativo/titolo non impostati "
                  f"(HTTP {r.status_code}). Impostali da WordPress.", file=sys.stderr)
        print(f"✔ Media caricato — ID {mid}")
        print(f"  URL       : {media['source_url']}")
        print(f"  Modifica  : {cfg['wp_url']}/wp-admin/post.php?post={mid}&action=edit")
    except requests.RequestException as exc:
        pp.fail(f"Errore di rete: {type(exc).__name__}. Controlla la connessione e riprova.")


if __name__ == "__main__":
    main()
