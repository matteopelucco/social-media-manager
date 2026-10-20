#!/usr/bin/env python3
"""Controlla che il progetto sia pronto all'uso: Python, librerie, config.yaml e (se non --offline) i collegamenti reali.

Pensato per chi inizia (cosa manca?) e per chi lo usa da tempo (il token sta per scadere?).
Sola lettura: non pubblica e non scrive nulla. Non stampa mai valori di credenziali, solo "presente"/"mancante".

Uso:
  python scripts/check_setup.py              # controlli locali + prova dei collegamenti (WordPress, Facebook, Instagram)
  python scripts/check_setup.py --offline    # solo controlli locali, senza rete
"""
import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from _common import GROUPS, ROOT, is_real, load_config, reconfigure_streams  # noqa: E402

MIN_PYTHON = (3, 8)
problems, warnings = [], []


def line(ok, text, hint=None, warn=False):
    mark = "OK  " if ok else ("ATT " if warn else "KO  ")
    print(f"  [{mark}] {text}")
    if not ok:
        (warnings if warn else problems).append(text)
        if hint:
            print(f"         → {hint}")


def check_python():
    print("1. Python e librerie")
    ver = sys.version_info
    line(ver >= MIN_PYTHON, f"Python {ver.major}.{ver.minor}.{ver.micro} (serve {MIN_PYTHON[0]}.{MIN_PYTHON[1]} o superiore)",
         "Installa Python da python.org")
    req = importlib.util.find_spec("requests") is not None
    line(req, "libreria requests (WordPress, Facebook, Instagram)",
         "python -m pip install --user -r requirements.txt")
    pil = importlib.util.find_spec("PIL") is not None
    line(pil, "libreria Pillow (solo per convertire immagini in JPEG per Instagram)",
         "python -m pip install --user -r requirements.txt", warn=True)
    return req


def check_config(cfg):
    print("2. Configurazione (config.yaml o variabili d'ambiente)")
    has_file = (ROOT / "config.yaml").is_file()
    line(has_file, "config.yaml presente",
         "copia config.sample.yaml in config.yaml e compila i valori (vedi docs/)", warn=True)
    ready = {}
    for group, keys in GROUPS.items():
        missing = [k for k in keys if not is_real(cfg, k)]
        ready[group] = not missing
        line(not missing, f"{group}: " + ("chiavi presenti" if not missing else "mancano " + ", ".join(missing)),
             {"wordpress": "docs/setup-wordpress.md", "facebook": "docs/setup-meta.md",
              "instagram": "docs/setup-meta.md"}[group], warn=True)
    for key in ("fb_page_id", "ig_user_id"):
        if is_real(cfg, key) and not cfg[key].isdigit():
            line(False, f"{key} non è numerico (gli ID di Meta sono numeri)", "docs/setup-meta.md", warn=True)
    if is_real(cfg, "fb_page_id") and cfg.get("ig_user_id") == cfg.get("fb_page_id"):
        line(False, "ig_user_id è uguale a fb_page_id (è l'ID della Pagina, non di Instagram)", "docs/setup-meta.md")
    return ready


def run_check(script, label):
    result = subprocess.run([sys.executable, "-B", str(Path(__file__).parent / script), "--check"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = result.returncode == 0
    line(ok, f"{label}")
    for out in (result.stdout, result.stderr):
        for raw in out.strip().splitlines():
            if raw.strip():
                print(f"         {raw.strip()}")
    return ok


def main():
    reconfigure_streams()
    p = argparse.ArgumentParser(description="Controlla che il progetto sia pronto all'uso (sola lettura).")
    p.add_argument("--offline", action="store_true", help="solo controlli locali, senza rete")
    args = p.parse_args()

    requests_ok = check_python()
    print()
    ready = check_config(load_config())
    print()
    if args.offline:
        print("3. Collegamenti: saltati (--offline)")
    elif not requests_ok:
        print("3. Collegamenti: saltati (manca la libreria requests)")
    else:
        print("3. Collegamenti (sola lettura)")
        if ready["wordpress"]:
            run_check("publish_post.py", "WordPress (REST API, utente, permessi)")
        if ready["facebook"]:
            run_check("publish_social.py", "Facebook e Instagram (Pagina, account, token)")
        if not ready["wordpress"] and not ready["facebook"]:
            print("  nessun canale configurato: niente da provare")
    print()
    if problems:
        print(f"RISULTATO: {len(problems)} problema/i da risolvere" +
              (f", {len(warnings)} avviso/i" if warnings else "") + ".")
        sys.exit(1)
    print("RISULTATO: tutto a posto" + (f" ({len(warnings)} avviso/i: i canali non configurati restano inutilizzabili)." if warnings else "."))


if __name__ == "__main__":
    main()
