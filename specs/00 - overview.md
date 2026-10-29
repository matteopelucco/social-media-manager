# Specifiche della web app locale

## Obiettivo
Web app che gira in locale (127.0.0.1:3000), con interfaccia web e testi generati con DeepSeek, mantenendo i vincoli di sicurezza dello strumento attuale. Tappa verso Sheepper (vedi `docs/piano-webapp.md`). Epic: issue #1.

## File di specifica
| File | Contenuto | Issue |
|------|-----------|-------|
| `03 - protezione-app-locale.md` | Accesso consentito solo dal computer dell'utente: host, origin, header, file della radice | #3 |

## Convenzioni
- Requisiti con ID stabili (`REQ-...`); scenari in Given/When/Then.
- Ogni scenario indica la copertura: **Unit** (test Vitest su logica pura in `lib/`) o **Manuale** (verifica documentata).
