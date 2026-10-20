#!/usr/bin/env python3
"""Pubblica UN post alla volta sulla Pagina Facebook o su Instagram (Graph API di Meta).

Sicurezza (vincoli nel codice, non solo nelle opzioni):
  - senza --publish mostra solo l'anteprima (nessuna scrittura) e un CODICE ANTEPRIMA;
  - con --publish serve anche --approved-code uguale al codice dell'anteprima: se testo,
    immagine o canale cambiano dopo l'ok, il codice cambia e lo script rifiuta;
  - un solo canale e un solo post per esecuzione; mai programmazione, mai DELETE, mai modifica di post esistenti;
  - se per quel canale e quel testo risulta già una pubblicazione nel registro della campagna, rifiuta;
  - token e ID non vengono mai stampati per esteso; il token viaggia nell'header, mai nell'URL.

Credenziali: variabili FB_PAGE_ID, FB_PAGE_TOKEN, IG_USER_ID (e opzionale GRAPH_VERSION) oppure config.yaml
(chiavi fb_page_id, fb_page_token, ig_user_id, graph_version). Le variabili hanno la precedenza.

Esempi:
  python scripts/publish_social.py --check
  python scripts/publish_social.py --channel facebook --campaign 2026-castagnata \
      --from-md campagne/2026-castagnata/testi/post-social.md --section Facebook \
      --image campagne/2026-castagnata/immagini/locandina.png --alt "Locandina ..."
  python scripts/publish_social.py ... --publish --approved-code <codice mostrato dall'anteprima>
"""
import argparse
import hashlib
import json
import mimetypes
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True

import requests  # noqa: E402
from _common import ROOT, fail, is_real, load_config, mask, reconfigure_streams  # noqa: E402

TIMEOUT = 30
UPLOAD_TIMEOUT = 120
IG_CAPTION_MAX = 2200
IG_HASHTAG_MAX = 30
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
CHANNELS = ("facebook", "instagram")
# permessi che il token deve avere per pubblicare (verificati da --check con /debug_token)
REQUIRED_SCOPES = {"facebook": ("pages_manage_posts", "pages_read_engagement"),
                   "instagram": ("instagram_basic", "instagram_content_publish")}


def require(cfg, keys):
    missing = [k for k in keys if not is_real(cfg, k)]
    if missing:
        fail("Credenziali mancanti o ancora segnaposto: " + ", ".join(missing) +
             ". Compila config.yaml oppure imposta le variabili d'ambiente corrispondenti.")


# ---------------------------------------------------------------- helpers
def graph(cfg, path):
    return f"https://graph.facebook.com/{cfg['graph_version']}/{path}"


def headers(cfg):
    return {"Authorization": f"Bearer {cfg['fb_page_token']}"}


def explain_graph(resp, what):
    hint = {
        190: "token scaduto o revocato: genera un nuovo token della Pagina",
        102: "sessione scaduta: genera un nuovo token",
        10: "permesso mancante: l'app non ha il permesso richiesto per questa azione",
        200: "permesso mancante o ruolo insufficiente sulla Pagina",
        4: "limite di richieste raggiunto: riprova più tardi",
        17: "limite di richieste raggiunto: riprova più tardi",
        32: "limite di richieste raggiunto: riprova più tardi",
        368: "azione bloccata da Meta (possibile limitazione temporanea della Pagina)",
        9007: "il contenuto multimediale non è ancora pronto: riprova fra poco",
        36000: "formato o proporzioni dell'immagine non accettati da Instagram",
        2207026: "formato immagine non supportato da Instagram (serve JPEG)",
    }
    try:
        err = resp.json().get("error", {})
    except ValueError:
        err = {}
    code = err.get("code")
    sub = err.get("error_subcode")
    detail = f" [{code}{'/' + str(sub) if sub else ''}] {err.get('message', '')}".rstrip()
    reason = hint.get(sub) or hint.get(code) or "risposta inattesa"
    fail(f"{what}: HTTP {resp.status_code} — {reason}.{detail}\nMi fermo qui: non aggiro nessun blocco.")


def extract_section(md_path, section):
    """Primo blocco ``` sotto l'intestazione '## <section>...' di un file .md."""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    inside_heading, in_block, block = False, False, []
    for line in lines:
        if not in_block and line.startswith("#"):
            inside_heading = line.lstrip("# ").lower().startswith(section.lower())
            continue
        if inside_heading and line.strip().startswith("```"):
            if in_block:
                return "\n".join(block).strip()
            in_block = True
            continue
        if in_block:
            block.append(line)
    fail(f"Sezione '{section}' con blocco di testo non trovata in {md_path.name}.")


def approval_code(channel, text, image_ref, alt):
    digest = hashlib.sha256("\x1f".join([channel, text, image_ref or "", alt or ""]).encode("utf-8")).hexdigest()
    return digest[:8]


def log_path(campaign):
    return ROOT / "campagne" / campaign / "social-esito.json"


def read_log(campaign):
    path = log_path(campaign)
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            fail(f"{path.name} non è un JSON valido: controllalo prima di procedere.")
    return []


def write_log(campaign, entry):
    entries = read_log(campaign)
    entries.append(entry)
    log_path(campaign).write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- comandi
def cmd_check(cfg):
    print(f"Versione Graph API: {cfg['graph_version']}")
    require(cfg, ["fb_page_id", "fb_page_token"])
    for key in ("fb_page_id", "ig_user_id"):
        if is_real(cfg, key) and not cfg[key].isdigit():
            print(f"ATTENZIONE: {key} non è numerico. Gli ID di Meta sono numeri (es. 1784…): "
                  "un nome o uno username può far funzionare le letture ma non la pubblicazione.", file=sys.stderr)
    print(f"1/2 Pagina Facebook (GET, sola lettura) — id {mask(cfg['fb_page_id'])}")
    r = requests.get(graph(cfg, cfg["fb_page_id"]), params={"fields": "name"}, headers=headers(cfg), timeout=TIMEOUT)
    if r.status_code != 200:
        explain_graph(r, "Lettura Pagina")
    print(f"    OK — Pagina: {r.json().get('name', '?')}")
    if not is_real(cfg, "ig_user_id"):
        print("2/2 Instagram: ig_user_id non impostato (salto il controllo).")
        check_token(cfg)
        return
    print(f"2/2 Account Instagram (GET, sola lettura) — id {mask(cfg['ig_user_id'])}")
    if is_real(cfg, "fb_page_id") and cfg["ig_user_id"] == cfg["fb_page_id"]:
        fail("ig_user_id è uguale a fb_page_id: è l'ID della Pagina, non dell'account Instagram. "
             "Ricavalo con GET /<id-pagina>?fields=instagram_business_account (di solito inizia con 1784…).")
    # media_count esiste solo sugli account Instagram: una Pagina Facebook risponderebbe con errore
    r = requests.get(graph(cfg, cfg["ig_user_id"]), params={"fields": "username,media_count"},
                     headers=headers(cfg), timeout=TIMEOUT)
    if r.status_code != 200:
        explain_graph(r, "Lettura account Instagram (l'ID è davvero di un account Instagram?)")
    print(f"    OK — account: @{r.json().get('username', '?')}")
    check_token(cfg)


def check_token(cfg):
    """Legge tipo, permessi e scadenza del token (GET /debug_token, sola lettura). Solo avvisi, non blocca."""
    print("Token (GET /debug_token, sola lettura)")
    try:
        r = requests.get(graph(cfg, "debug_token"), params={"input_token": cfg["fb_page_token"]},
                         headers=headers(cfg), timeout=TIMEOUT)
        data = r.json().get("data") if r.status_code == 200 else None
    except (requests.RequestException, ValueError):
        data = None
    if not data:
        print("    non verificabile con questo token: i permessi di scrittura si vedranno alla prima pubblicazione.")
        return
    kind = data.get("type", "?")
    expires = data.get("expires_at", 0)
    if expires:
        days = (datetime.fromtimestamp(expires, timezone.utc) - datetime.now(timezone.utc)).days
        when = f"scade il {datetime.fromtimestamp(expires).strftime('%d/%m/%Y')} (tra {days} giorni)"
    else:
        days, when = None, "non scade"
    print(f"    tipo: {kind}, {when}")
    if kind != "PAGE":
        print("    ATTENZIONE: non è un token di Pagina: con un token utente la pubblicazione fallisce. "
              "Usa l'access_token del blocco della Pagina in me/accounts (vedi docs/setup-meta.md).", file=sys.stderr)
    if days is not None and days < 14:
        print(f"    ATTENZIONE: scade tra {days} giorni: rigenera il token (docs/setup-meta.md).", file=sys.stderr)
    scopes = set(data.get("scopes", []))
    wanted = list(REQUIRED_SCOPES["facebook"]) + (list(REQUIRED_SCOPES["instagram"]) if is_real(cfg, "ig_user_id") else [])
    missing = [s for s in wanted if s not in scopes]
    if missing:
        print("    ATTENZIONE: permessi mancanti nel token: " + ", ".join(missing) + " (vedi docs/setup-meta.md).", file=sys.stderr)
    else:
        print("    permessi di pubblicazione presenti (la prova definitiva resta la prima pubblicazione).")


def check_image_url(url):
    if not url.startswith("https://"):
        fail("--image-url deve essere un indirizzo https:// pubblico.")
    r = requests.get(url, stream=True, timeout=TIMEOUT)
    ctype = r.headers.get("Content-Type", "").split(";")[0].strip().lower()
    r.close()
    if r.status_code != 200:
        fail(f"L'immagine non è raggiungibile pubblicamente (HTTP {r.status_code}).")
    return ctype


def resolve_text(args):
    """Ritorna (testo, descrizione della fonte). Esplicito se indicato, altrimenti automatico dalla campagna."""
    channel = args.channel
    if args.text_file and args.from_md:
        fail("Usa --text-file oppure --from-md, non entrambi.")
    if args.text_file:
        return Path(args.text_file).read_text(encoding="utf-8").strip(), args.text_file
    if args.from_md:
        if not args.section:
            fail("--from-md richiede --section (es. Facebook, Instagram).")
        return extract_section(Path(args.from_md), args.section), f"{args.from_md} [{args.section}]"
    # automatico: testi/post-<canale>.md se esiste, altrimenti la sezione del canale in testi/post-social.md
    testi = ROOT / "campagne" / args.campaign / "testi"
    for name in (f"post-{channel}.md", "post-social.md"):
        path = testi / name
        if path.is_file():
            return extract_section(path, channel), f"campagne/{args.campaign}/testi/{name} [{channel.capitalize()}]"
    fail(f"Nessun testo trovato in campagne/{args.campaign}/testi/ (cercati post-{channel}.md e post-social.md). "
         "Indica --text-file oppure --from-md + --section.")


def brief_alt(campaign):
    """Testo alternativo scritto nel brief ('- Testo alternativo (italiano): ...'), se c'è."""
    brief = ROOT / "campagne" / campaign / "brief.md"
    if brief.is_file():
        match = re.search(r"^\s*-\s*Testo alternativo[^:]*:\s*(\S.*)$", brief.read_text(encoding="utf-8"), re.M)
        if match and not match.group(1).strip().startswith("["):
            return match.group(1).strip()
    return None


def cmd_post(args, cfg):
    channel = args.channel
    text, text_source = resolve_text(args)
    alt_source = "da --alt"
    if not (args.alt and args.alt.strip()) and (args.image or args.image_url):
        args.alt = brief_alt(args.campaign)
        alt_source = "dal brief.md"
    if not text:
        fail("Il testo è vuoto.")
    if re.search(r"\[[^\]]+\]", text):
        fail("Il testo contiene ancora segnaposto tra parentesi quadre ([...]): completalo prima.")

    image_path, image_url = None, None
    if args.image and args.image_url:
        fail("Usa --image (file locale, solo Facebook) oppure --image-url, non entrambi.")
    if args.image:
        if channel == "instagram":
            fail("Instagram non accetta file locali: carica l'immagine (JPG) sul sito e usa --image-url.")
        image_path = Path(args.image)
        if not image_path.is_file():
            fail(f"Immagine non trovata: {image_path}")
        mime = mimetypes.guess_type(image_path.name)[0]
        if mime not in IMAGE_TYPES:
            fail(f"Formato immagine non supportato ({mime}). Usa jpg, png o webp.")
    if channel == "instagram":
        if not args.image_url:
            fail("Instagram richiede un'immagine: passa --image-url (https pubblico, JPEG).")
        if len(text) > IG_CAPTION_MAX:
            fail(f"Il testo è lungo {len(text)} caratteri (massimo {IG_CAPTION_MAX} su Instagram).")
        hashtags = len(re.findall(r"#\w+", text))
        if hashtags > IG_HASHTAG_MAX:
            fail(f"{hashtags} hashtag: Instagram ne ammette al massimo {IG_HASHTAG_MAX}.")
    if args.image_url:
        image_url = args.image_url
        ctype = check_image_url(image_url)
        if channel == "instagram" and ctype != "image/jpeg":
            fail(f"L'immagine è {ctype or 'di tipo sconosciuto'}: Instagram accetta solo JPEG per il feed. "
                 "Converti la locandina in JPG, caricala sul sito e riprova.")
    if (image_path or image_url) and not (args.alt and args.alt.strip()):
        fail("Manca il testo alternativo in italiano (obbligatorio con l'immagine): "
             "scrivilo nel brief ('- Testo alternativo (italiano): ...') oppure passa --alt.")

    image_ref = image_url or (f"{image_path.name}:{image_path.stat().st_size}" if image_path else "")
    code = approval_code(channel, text, image_ref, args.alt)

    print("=" * 60)
    print(f"ANTEPRIMA — {channel.upper()}" + ("" if args.publish else "  (nessuna scrittura)"))
    print("=" * 60)
    print(f"Campagna   : {args.campaign}")
    print(f"Testo da   : {text_source}")
    print(f"Immagine   : {image_url or (image_path.name if image_path else 'nessuna (solo testo)')}")
    print(f"Testo alt  : {args.alt or '—'}" + (f"   ({alt_source})" if args.alt else ""))
    n_tags = len(re.findall(r"#\w+", text))
    print(f"Lunghezza  : {len(text)} caratteri, {n_tags} hashtag")
    print("-" * 60)
    print(text)
    print("=" * 60)
    print(f"CODICE ANTEPRIMA: {code}")

    if not args.publish:
        print("Anteprima terminata. Per pubblicare, dopo l'ok esplicito in chat, rilancia con "
              f"--publish --approved-code {code}")
        return
    if args.approved_code != code:
        fail("--approved-code assente o diverso dal codice dell'anteprima: il contenuto è cambiato "
             "oppure manca l'ok. Rifai l'anteprima e chiedi un nuovo ok.")
    for entry in read_log(args.campaign):
        if entry.get("channel") == channel and entry.get("code") == code:
            fail(f"Già pubblicato su {channel} il {entry.get('data')} (id {entry.get('post_id')}). Non ripubblico.")

    require(cfg, ["fb_page_id", "fb_page_token"] + (["ig_user_id"] if channel == "instagram" else []))
    post_id = publish_facebook(cfg, text, image_path, image_url, args.alt) if channel == "facebook" \
        else publish_instagram(cfg, text, image_url, args.alt)
    write_log(args.campaign, {"channel": channel, "code": code, "post_id": post_id,
                              "data": datetime.now().strftime("%Y-%m-%d %H:%M")})
    print(f"✔ Pubblicato su {channel} — ID {post_id}")
    print(f"  Registrato in campagne/{args.campaign}/social-esito.json")


def publish_facebook(cfg, text, image_path, image_url, alt):
    page = cfg["fb_page_id"]
    if image_path:
        mime = mimetypes.guess_type(image_path.name)[0]
        with image_path.open("rb") as fh:
            r = requests.post(graph(cfg, f"{page}/photos"), headers=headers(cfg), timeout=UPLOAD_TIMEOUT,
                              data={"caption": text, "published": "true", "alt_text_custom": alt.strip()},
                              files={"source": (image_path.name, fh, mime)})
    elif image_url:
        r = requests.post(graph(cfg, f"{page}/photos"), headers=headers(cfg), timeout=TIMEOUT,
                          data={"url": image_url, "caption": text, "published": "true", "alt_text_custom": alt.strip()})
    else:
        r = requests.post(graph(cfg, f"{page}/feed"), headers=headers(cfg), timeout=TIMEOUT,
                          data={"message": text, "published": "true"})
    if r.status_code != 200:
        explain_graph(r, "Pubblicazione su Facebook")
    body = r.json()
    return body.get("post_id") or body.get("id")


def publish_instagram(cfg, text, image_url, alt):
    ig = cfg["ig_user_id"]
    r = requests.post(graph(cfg, f"{ig}/media"), headers=headers(cfg), timeout=TIMEOUT,
                      data={"image_url": image_url, "caption": text, "alt_text": alt.strip()})
    if r.status_code != 200:
        explain_graph(r, "Creazione contenuto Instagram")
    container = r.json()["id"]
    for _ in range(12):  # fino a ~60 s
        s = requests.get(graph(cfg, container), params={"fields": "status_code"}, headers=headers(cfg), timeout=TIMEOUT)
        if s.status_code != 200:
            explain_graph(s, "Controllo stato contenuto")
        status = s.json().get("status_code")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            fail(f"Instagram ha rifiutato il contenuto (stato {status}). Nulla è stato pubblicato.")
        time.sleep(5)
    else:
        fail("Il contenuto non è pronto dopo 60 secondi. Nulla è stato pubblicato: riprova più tardi.")
    r = requests.post(graph(cfg, f"{ig}/media_publish"), headers=headers(cfg), timeout=TIMEOUT,
                      data={"creation_id": container})
    if r.status_code != 200:
        explain_graph(r, "Pubblicazione su Instagram")
    return r.json()["id"]


def main():
    reconfigure_streams()
    p = argparse.ArgumentParser(description="Pubblica un post su Facebook o Instagram (solo dopo ok esplicito).")
    p.add_argument("--check", action="store_true", help="verifica token, Pagina e account Instagram (sola lettura) ed esce")
    p.add_argument("--channel", choices=CHANNELS)
    p.add_argument("--campaign", help="cartella campagna, es. 2026-castagnata (per il registro delle pubblicazioni)")
    p.add_argument("--text-file", help="file con il solo testo del post")
    p.add_argument("--from-md", help="file .md con più sezioni (es. post-social.md)")
    p.add_argument("--section", help="intestazione da cui prendere il primo blocco ``` (es. Facebook, Instagram)")
    p.add_argument("--image", help="immagine locale (solo Facebook)")
    p.add_argument("--image-url", help="URL https pubblico dell'immagine (obbligatorio per Instagram, JPEG)")
    p.add_argument("--alt", help="testo alternativo in italiano (default: dal brief della campagna)")
    p.add_argument("--publish", action="store_true", help="pubblica davvero (senza: solo anteprima)")
    p.add_argument("--approved-code", help="codice mostrato dall'anteprima approvata")
    args = p.parse_args()

    cfg = load_config()
    try:
        if args.check:
            cmd_check(cfg)
            return
        if not args.channel or not args.campaign:
            p.error("--channel e --campaign sono obbligatori")
        if not (ROOT / "campagne" / args.campaign).is_dir():
            fail(f"Cartella campagna non trovata: campagne/{args.campaign}")
        cmd_post(args, cfg)
    except requests.RequestException as exc:
        fail(f"Errore di rete: {type(exc).__name__}. Controlla la connessione. "
             "Se l'errore è arrivato durante la pubblicazione, verifica sulla Pagina se il post è uscito prima di riprovare.")


if __name__ == "__main__":
    main()
