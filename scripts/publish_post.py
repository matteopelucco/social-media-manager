#!/usr/bin/env python3
"""Crea una BOZZA di articolo su WordPress (asilosartorio.it) tramite REST API.

Sicurezza (vincoli nel codice, non solo nelle opzioni):
  - lo stato può essere solo "draft" o "pending": "publish", "future" e "private" sono rifiutati;
  - non viene mai inviata una data (nessuna programmazione);
  - niente DELETE, niente modifiche a post/media/termini esistenti;
  - la password non viene mai stampata.

Credenziali: variabili d'ambiente WP_URL, WP_USER, WP_APP_PASSWORD oppure config.yaml
(chiavi wp_url, wp_user, wp_app_password). Le variabili hanno la precedenza.

Esempi:
  python scripts/publish_post.py --check
  python scripts/publish_post.py --title "Castagnata 2026" --excerpt "Domenica 25 ottobre" --content-file campagne/2026-castagnata/testi/articolo-blog.html \
      --image campagne/2026-castagnata/immagini/locandina.png --alt "Locandina ..." --category avvisi --tags "castagnata,evento" --dry-run
"""
import argparse
import html
import mimetypes
import re
import sys
import unicodedata
from pathlib import Path

sys.dont_write_bytecode = True

import requests  # noqa: E402
from _common import fail, is_real, load_config, reconfigure_streams  # noqa: E402,F401

ALLOWED_STATUSES = ("draft", "pending")
TITLE_MAX_WORDS = 4     # titolo e riassunto brevissimi: servono al carosello e alle anteprime
EXCERPT_MAX_WORDS = 4
TIMEOUT = 30
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


# ----------------------------------------------------------------- config
def has_credentials(cfg):
    return all(is_real(cfg, key) for key in ("wp_url", "wp_user", "wp_app_password"))


def require_credentials(cfg):
    if not has_credentials(cfg):
        fail("Credenziali mancanti o ancora segnaposto: compila config.yaml "
             "(wp_user, wp_app_password) oppure imposta WP_USER e WP_APP_PASSWORD.")
    if not cfg["wp_url"].startswith("https://"):
        fail("wp_url deve iniziare con https:// (le credenziali non viaggiano in chiaro).")


# ---------------------------------------------------------------- helpers
def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", text)


def strip_tags(markup):
    text = re.sub(r"<!--.*?-->", " ", markup, flags=re.S)
    text = re.sub(r"<(script|style).*?</\1>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def safe_filename(path):
    stem = slugify(path.stem) or "immagine"
    return f"{stem}{path.suffix.lower()}"


def api(cfg, path):
    return f"{cfg['wp_url']}/wp-json/wp/v2/{path}"


def auth(cfg):
    return (cfg["wp_user"], cfg["wp_app_password"])


def explain_http(resp, what):
    code = resp.status_code
    hint = {
        401: "autenticazione rifiutata: controlla utente e Application Password",
        403: "permesso negato (ruolo dell'utente o plugin di sicurezza/firewall che blocca la REST API)",
        404: "endpoint non trovato (REST API disattivata o permalink non attivi?)",
        429: "troppe richieste: riprova più tardi",
        503: "sito non disponibile al momento: riprova più tardi",
    }.get(code, "risposta inattesa")
    try:
        body = resp.json()
        detail = f" [{body.get('code', '')}] {body.get('message', '')}".rstrip()
    except ValueError:
        detail = ""
    fail(f"{what}: HTTP {code} — {hint}.{detail}\nMi fermo qui: non aggiro nessun blocco.")


# --------------------------------------------------------- lookup termini
def find_category(cfg, slug):
    resp = requests.get(api(cfg, "categories"), params={"slug": slug, "_fields": "id,name,slug"}, timeout=TIMEOUT)
    if resp.status_code != 200:
        explain_http(resp, "Lettura categorie")
    items = resp.json()
    if not items:
        fail(f"Categoria '{slug}' non trovata sul sito. Nessuna categoria viene creata dallo script.")
    return items[0]["id"], items[0]["name"]


def find_tags(cfg, names, create):
    """Ritorna (lista id esistenti, lista nomi mancanti)."""
    ids, missing = [], []
    for name in names:
        resp = requests.get(api(cfg, "tags"), params={"search": name, "per_page": 20, "_fields": "id,name,slug"}, timeout=TIMEOUT)
        if resp.status_code != 200:
            explain_http(resp, "Lettura tag")
        wanted, wanted_slug = name.strip().lower(), slugify(name)
        match = next((t for t in resp.json() if html.unescape(t["name"]).lower() == wanted or t["slug"] == wanted_slug), None)
        if match:
            ids.append(match["id"])
        else:
            missing.append(name)
    return ids, missing


# ---------------------------------------------------------------- comandi
def cmd_check(cfg):
    base = cfg["wp_url"]
    if not base:
        fail("wp_url non impostato.")
    print(f"1/3 Raggiungibilità REST API: {base}/wp-json/")
    resp = requests.get(f"{base}/wp-json/", timeout=TIMEOUT)
    if resp.status_code != 200:
        explain_http(resp, "REST API")
    print(f"    OK — sito: {html.unescape(resp.json().get('name', '?'))}")
    if not has_credentials(cfg):
        fail("2/3 Autenticazione: credenziali ancora segnaposto in config.yaml. Compilale e rilancia --check.")
    require_credentials(cfg)
    print("2/3 Autenticazione (GET /users/me, sola lettura)")
    resp = requests.get(api(cfg, "users/me"), params={"context": "edit", "_fields": "id,name,roles,capabilities"},
                        auth=auth(cfg), timeout=TIMEOUT)
    if resp.status_code != 200:
        explain_http(resp, "Autenticazione")
    me = resp.json()
    caps = me.get("capabilities", {})
    print(f"    OK — utente: {me.get('name')} (id {me.get('id')}), ruoli: {', '.join(me.get('roles', []))}")
    print("3/3 Permessi")
    print(f"    può creare/modificare articoli (edit_posts): {'sì' if caps.get('edit_posts') else 'NO'}")
    print(f"    può caricare file (upload_files):             {'sì' if caps.get('upload_files') else 'NO'}")
    print("    (lo script non imposta mai 'publish', a prescindere dai permessi dell'utente)")
    if not caps.get("edit_posts") or not caps.get("upload_files"):
        fail("L'utente non ha tutti i permessi necessari (edit_posts + upload_files).")


def cmd_post(args, cfg):
    if args.status not in ALLOWED_STATUSES:
        fail(f"Stato '{args.status}' non consentito: lo script crea solo bozze ({', '.join(ALLOWED_STATUSES)}).")
    if not cfg.get("wp_url"):
        fail("wp_url non impostato.")

    content_path = Path(args.content_file)
    if not content_path.is_file():
        fail(f"File contenuto non trovato: {content_path}")
    content = content_path.read_text(encoding="utf-8")
    plain = strip_tags(content)
    if not plain:
        fail("Il contenuto è vuoto.")
    if "[" in plain and re.search(r"\[[^\]]+\]", plain):
        fail("Il contenuto contiene ancora segnaposto tra parentesi quadre ([...]): completalo prima.")
    words = len(plain.split())

    image_path = None
    if args.image:
        image_path = Path(args.image)
        if not image_path.is_file():
            fail(f"Immagine non trovata: {image_path}")
        mime = mimetypes.guess_type(image_path.name)[0]
        if mime not in IMAGE_TYPES:
            fail(f"Formato immagine non supportato ({mime}). Usa jpg, png, webp o gif.")
        if not args.alt or not args.alt.strip():
            fail("--alt (testo alternativo in italiano) è obbligatorio quando usi --image.")

    title_words = len(args.title.split())
    if title_words > TITLE_MAX_WORDS:
        fail(f"Il titolo ha {title_words} parole (massimo {TITLE_MAX_WORDS}): accorcialo. Es. \"Castagnata Sociale 2026\".")
    excerpt = (args.excerpt or "").strip()
    if not excerpt:
        fail(f"--excerpt è obbligatorio: il riassunto è di 3-{EXCERPT_MAX_WORDS} parole (dal brief).")
    excerpt_words = len(excerpt.split())
    if excerpt_words > EXCERPT_MAX_WORDS:
        fail(f"L'estratto ha {excerpt_words} parole (massimo {EXCERPT_MAX_WORDS}): accorcialo.")
    slug = slugify(args.slug or args.title)
    if not slug:
        fail("Impossibile ricavare uno slug dal titolo.")

    cat_slugs = [args.category or cfg.get("categoria_default", "avvisi")]
    if args.slider:
        cat_slugs.append(cfg.get("categoria_slider", "slider"))
    categories = [(find_category(cfg, s), s) for s in dict.fromkeys(cat_slugs)]
    tag_names = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    tag_ids, missing_tags = find_tags(cfg, tag_names, args.create_tags)
    if missing_tags and not args.create_tags:
        fail("Tag inesistenti sul sito: " + ", ".join(missing_tags) +
             ". Correggi i nomi oppure usa --create-tags per crearli esplicitamente.")

    print("=" * 60)
    print("ANTEPRIMA" + (" (DRY-RUN: nessuna scrittura sul sito)" if args.dry_run else ""))
    print("=" * 60)
    print(f"Titolo     : {args.title} ({title_words} parole)")
    print(f"Slug       : {slug}")
    print(f"Stato      : {args.status}   (data/programmazione: mai impostata)")
    print(f"Categorie  : " + ", ".join(f"{s} → {name} (id {cid})" for (cid, name), s in categories))
    print(f"Tag        : " + (", ".join(tag_names) or "—") + (f"   [DA CREARE: {', '.join(missing_tags)}]" if missing_tags else ""))
    print(f"Estratto   : {excerpt} ({excerpt_words} parole)")
    if image_path:
        print(f"Immagine   : {image_path.name} ({image_path.stat().st_size // 1024} KB) → in evidenza")
        print(f"Testo alt  : {args.alt}")
    else:
        print("Immagine   : nessuna")
    print(f"Contenuto  : {words} parole" + ("" if 100 <= words <= 150 else "   ⚠ fuori dall'intervallo 100-150"))
    print("-" * 60)
    print(content.strip())
    print("=" * 60)

    if args.dry_run:
        print("Dry-run terminato. Nessuna richiesta di scrittura inviata.")
        return

    require_credentials(cfg)
    dup = requests.get(api(cfg, "posts"), params={"slug": slug, "status": "any", "_fields": "id,status,link"},
                       auth=auth(cfg), timeout=TIMEOUT)
    if dup.status_code != 200:
        explain_http(dup, "Controllo duplicati")
    if dup.json():
        fail(f"Esiste già un articolo con slug '{slug}' (id {dup.json()[0]['id']}, stato {dup.json()[0]['status']}). "
             "Non lo modifico: cambia titolo o --slug.")

    tag_ids = list(tag_ids)
    if missing_tags:
        for name in missing_tags:
            r = requests.post(api(cfg, "tags"), json={"name": name}, auth=auth(cfg), timeout=TIMEOUT)
            if r.status_code not in (200, 201):
                explain_http(r, f"Creazione tag '{name}'")
            tag_ids.append(r.json()["id"])

    media_id = None
    if image_path:
        mime = mimetypes.guess_type(image_path.name)[0]
        with image_path.open("rb") as fh:
            r = requests.post(
                api(cfg, "media"), data=fh, auth=auth(cfg), timeout=120,
                headers={"Content-Type": mime,
                         "Content-Disposition": f'attachment; filename="{safe_filename(image_path)}"'})
        if r.status_code not in (200, 201):
            explain_http(r, "Caricamento immagine")
        media_id = r.json()["id"]
        r = requests.post(api(cfg, f"media/{media_id}"), auth=auth(cfg), timeout=TIMEOUT,
                          json={"alt_text": args.alt.strip(), "title": args.title})
        if r.status_code != 200:
            print(f"ATTENZIONE: immagine caricata (id {media_id}) ma testo alternativo non impostato "
                  f"(HTTP {r.status_code}). Impostalo da WordPress.", file=sys.stderr)

    payload = {"title": args.title, "content": content, "excerpt": excerpt, "slug": slug,
               "status": args.status, "categories": [cid for (cid, _), _s in categories]}
    if tag_ids:
        payload["tags"] = tag_ids
    if media_id:
        payload["featured_media"] = media_id
    assert payload["status"] in ALLOWED_STATUSES and "date" not in payload and "date_gmt" not in payload

    r = requests.post(api(cfg, "posts"), json=payload, auth=auth(cfg), timeout=TIMEOUT)
    if r.status_code not in (200, 201):
        if media_id:
            print(f"NOTA: l'immagine è già stata caricata (media id {media_id}); lo script non elimina nulla.", file=sys.stderr)
        explain_http(r, "Creazione bozza")
    post = r.json()
    if post.get("status") not in ALLOWED_STATUSES:
        fail(f"Il sito ha restituito stato inatteso '{post.get('status')}' per l'articolo {post.get('id')}: controllalo subito in WordPress.")

    pid = post["id"]
    print(f"✔ Bozza creata — ID {pid}, stato {post['status']}")
    print(f"  Anteprima : {cfg['wp_url']}/?p={pid}&preview=true   (serve essere loggati)")
    print(f"  Modifica  : {cfg['wp_url']}/wp-admin/post.php?post={pid}&action=edit")
    if media_id:
        print(f"  Media ID  : {media_id}")


def main():
    reconfigure_streams()
    p = argparse.ArgumentParser(description="Crea una BOZZA di articolo su WordPress (mai pubblicazione).")
    p.add_argument("--check", action="store_true", help="verifica REST API e autenticazione (sola lettura) ed esce")
    p.add_argument("--title", help=f"titolo breve, max {TITLE_MAX_WORDS} parole")
    p.add_argument("--content-file", help="file HTML con il contenuto")
    p.add_argument("--image", help="immagine in evidenza (jpg/png/webp/gif)")
    p.add_argument("--alt", help="testo alternativo dell'immagine, in italiano (obbligatorio con --image)")
    p.add_argument("--category", help="slug categoria (default: categoria_default di config.yaml, 'avvisi')")
    p.add_argument("--slider", action="store_true", help="aggiunge anche la categoria 'slider' (carosello home)")
    p.add_argument("--tags", help="tag separati da virgola (devono già esistere)")
    p.add_argument("--create-tags", action="store_true", help="crea i tag mancanti (altrimenti errore)")
    p.add_argument("--excerpt", help=f"estratto/riassunto, 3-{EXCERPT_MAX_WORDS} parole (obbligatorio)")
    p.add_argument("--slug", help="slug (default: dal titolo)")
    p.add_argument("--status", default="draft", help="draft (default) o pending; publish/future non sono ammessi")
    p.add_argument("--dry-run", action="store_true", help="mostra l'anteprima senza scrivere sul sito")
    args = p.parse_args()

    cfg = load_config()
    if args.check:
        cmd_check(cfg)
        return
    if not args.title or not args.content_file:
        p.error("--title e --content-file sono obbligatori")
    try:
        cmd_post(args, cfg)
    except requests.RequestException as exc:
        fail(f"Errore di rete: {type(exc).__name__}. Controlla la connessione e riprova.")


if __name__ == "__main__":
    main()
