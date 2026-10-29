#!/usr/bin/env bash
# Creates (or updates) the labels the agents use as a state machine. Idempotent.
# Requires an authenticated `gh`, run from inside the repository.
set -euo pipefail

upsert() {
  gh label create "$1" --color "$2" --description "$3" --force >/dev/null
  echo "  ok $1"
}

echo "== status =="
upsert "status:triage"      "ededed" "Appena aperta, in attesa di triage"
upsert "status:needs-info"  "d93f0b" "Ambigua: servono chiarimenti"
upsert "status:ready"       "0e8a16" "Pronta da implementare"
upsert "status:in-progress" "1d76db" "Un agente ci sta lavorando"
upsert "status:review"      "fbca04" "PR aperta, in attesa di review"
upsert "status:blocked"     "b60205" "Bloccata da dipendenza o decisione umana"
upsert "status:done"        "5319e7" "Mergiata e chiusa"

echo "== type =="
upsert "type:bug"      "d73a4a" "Difetto"
upsert "type:feature"  "a2eeef" "Nuova funzionalità"
upsert "type:chore"    "cfd3d7" "Manutenzione, refactor, dipendenze, documenti"
upsert "type:security" "b60205" "Tocca sicurezza, autenticazione o permessi"

echo "== autonomy (ADR-0004) =="
upsert "ai-driven"         "0e8a16" "Eseguibile e mergiabile in autonomia dall'agente"
upsert "human-in-the-loop" "d93f0b" "Serve l'umano: la PR resta aperta per la sua review"

echo "Fatto. Le label area:* dipendono dal progetto: creale a mano."
