"""Funzioni condivise dagli script del progetto (configurazione, errori, utilità).

Non si lancia da solo. Ogni script imposta `sys.dont_write_bytecode = True` PRIMA di importarlo,
così su Drive non nascono cartelle __pycache__.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER_PREFIX = "INSERISCI_"

# chiave in config.yaml -> variabile d'ambiente (le variabili hanno la precedenza)
ENV_MAP = {
    "wp_url": "WP_URL",
    "wp_user": "WP_USER",
    "wp_app_password": "WP_APP_PASSWORD",
    "fb_page_id": "FB_PAGE_ID",
    "fb_page_token": "FB_PAGE_TOKEN",
    "ig_user_id": "IG_USER_ID",
    "graph_version": "GRAPH_VERSION",
    "deepseek_api_key": "DEEPSEEK_API_KEY",
    "deepseek_model": "DEEPSEEK_MODEL",
    "deepseek_base_url": "DEEPSEEK_BASE_URL",
}
GROUPS = {
    "wordpress": ("wp_url", "wp_user", "wp_app_password"),
    "facebook": ("fb_page_id", "fb_page_token"),
    "instagram": ("fb_page_token", "ig_user_id"),
}


def fail(message, code=1):
    print(f"ERRORE: {message}", file=sys.stderr)
    sys.exit(code)


def read_flat_yaml(path):
    """Legge un YAML piatto 'chiave: valore' (senza librerie esterne)."""
    data = {}
    if not path.is_file():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value[:1] in ("'", '"') and value[-1:] == value[:1] and len(value) >= 2:
            value = value[1:-1]
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
        data[key.strip()] = value
    return data


def load_config():
    """config.yaml + variabili d'ambiente (precedenza alle variabili). Non stampa nulla."""
    cfg = read_flat_yaml(ROOT / "config.yaml")
    for key, env in ENV_MAP.items():
        if os.environ.get(env):
            cfg[key] = os.environ[env]
    cfg["wp_url"] = cfg.get("wp_url", "").rstrip("/")
    cfg.setdefault("graph_version", "v23.0")  # da verificare nel tempo: Meta ritira le versioni vecchie
    return cfg


def is_real(cfg, key):
    """True se la chiave c'è e non è un segnaposto INSERISCI_..."""
    value = cfg.get(key, "")
    return bool(value) and not value.startswith(PLACEHOLDER_PREFIX)


def mask(value):
    return f"…{value[-4:]}" if value and len(value) > 8 else "…"


def reconfigure_streams():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
