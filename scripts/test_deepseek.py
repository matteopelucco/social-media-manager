#!/usr/bin/env python3
"""Prova la connessione all'API di DeepSeek: invia un prompt semplice e stampa la risposta.

Sola prova: una sola richiesta POST a /chat/completions, nessun file scritto, nessun altro servizio toccato.
Il prompt esce verso un servizio esterno: usa solo testo di prova, mai dati personali di famiglie o bambini.
La chiave non viene mai stampata.

Credenziali: config.yaml (deepseek_api_key; opzionali deepseek_model, deepseek_base_url)
oppure variabili d'ambiente DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL (hanno la precedenza).

Esempi:
  python scripts/test_deepseek.py
  python scripts/test_deepseek.py --prompt "Scrivi una frase di benvenuto per un asilo, in italiano"
"""
import argparse
import sys

sys.dont_write_bytecode = True

import requests  # noqa: E402
from _common import fail, is_real, load_config, mask, reconfigure_streams  # noqa: E402

DEFAULT_PROMPT = "Rispondi in italiano con una sola frase breve: la connessione funziona?"
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_BASE_URL = "https://api.deepseek.com"
TIMEOUT = 60

HTTP_HINTS = {
    400: "richiesta non valida (controlla il nome del modello in deepseek_model)",
    401: "chiave rifiutata: controlla deepseek_api_key",
    402: "credito esaurito sull'account DeepSeek",
    422: "parametri non validi (controlla il nome del modello in deepseek_model)",
    429: "troppe richieste: riprova tra poco",
    500: "errore del servizio DeepSeek: riprova più tardi",
    503: "servizio DeepSeek sovraccarico o non disponibile: riprova più tardi",
}


def main():
    reconfigure_streams()
    p = argparse.ArgumentParser(description="Prova la connessione all'API di DeepSeek con un prompt semplice.")
    p.add_argument("--prompt", default=DEFAULT_PROMPT, help="testo da inviare (solo testo di prova)")
    p.add_argument("--model", help=f"modello (default: deepseek_model di config.yaml, altrimenti {DEFAULT_MODEL})")
    args = p.parse_args()

    cfg = load_config()
    if not is_real(cfg, "deepseek_api_key"):
        fail("Chiave mancante o ancora segnaposto: compila deepseek_api_key in config.yaml "
             "oppure imposta DEEPSEEK_API_KEY.")
    base_url = (cfg.get("deepseek_base_url") or DEFAULT_BASE_URL).rstrip("/")
    if not base_url.startswith("https://"):
        fail("deepseek_base_url deve iniziare con https:// (la chiave non viaggia in chiaro).")
    model = args.model or cfg.get("deepseek_model") or DEFAULT_MODEL

    print(f"Servizio : {base_url}")
    print(f"Modello  : {model}")
    print(f"Chiave   : {mask(cfg['deepseek_api_key'])}")
    print(f"Prompt   : {args.prompt}")
    print("-" * 60)

    try:
        resp = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {cfg['deepseek_api_key']}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": args.prompt}], "stream": False},
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        fail(f"Errore di rete: {type(exc).__name__}. Controlla la connessione e riprova.")

    if resp.status_code != 200:
        detail = ""
        try:
            detail = f" [{resp.json().get('error', {}).get('message', '')}]".replace(" []", "")
        except ValueError:
            pass
        fail(f"HTTP {resp.status_code} — {HTTP_HINTS.get(resp.status_code, 'risposta inattesa')}.{detail}")

    try:
        data = resp.json()
        answer = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError):
        fail("Risposta in un formato inatteso: il servizio ha risposto 200 ma senza testo utilizzabile.")

    print(answer.strip())
    print("-" * 60)
    usage = data.get("usage") or {}
    print(f"✔ Connessione OK — modello {data.get('model', model)}, "
          f"token: {usage.get('prompt_tokens', '?')} in / {usage.get('completion_tokens', '?')} out")


if __name__ == "__main__":
    main()
