# ADR 0003 — Modello di minaccia dell'app locale

- **Stato:** Accettata
- **Data:** 2026-10-29
- **Decisione di:** Matteo Pelucco

## Contesto
L'app Sheepper gira sul computer dell'operatore e può leggere segreti (`config.yaml`) e pubblicare sui canali. Un sito web aperto nello stesso browser potrebbe tentare di raggiungerla. Specifica: [specs/03 - protezione-app-locale.md](../../specs/03%20-%20protezione-app-locale.md).

## Decisione
- Ascolto solo su `127.0.0.1:3000` (dev e start).
- `proxy.ts` ammette solo gli `Host` `localhost:3000`, `127.0.0.1:3000`, `[::1]:3000`; sui metodi non sicuri l'`Origin` deve coincidere con `http://<Host>`. Altrimenti 403 con messaggio generico.
- Ogni risposta porta `Cache-Control: no-store`, `X-Frame-Options: DENY` e una CSP; nessun header CORS.
- Nessuna route serve file della radice del progetto.
- Logica pura in `lib/security/`, coperta da test.
- **CSP in produzione (da confermare):** nonce per richiesta con `'strict-dynamic'` per gli script, senza `'unsafe-inline'` né `'unsafe-eval'`; `'unsafe-inline'` solo per gli stili. Le pagine sono dinamiche (`connection()`). In dev si aggiunge `'unsafe-eval'` agli script.

## Cosa protegge
- **DNS rebinding:** un nome esterno che punta a 127.0.0.1 ha un `Host` non ammesso.
- **CSRF da pagine esterne:** le richieste non sicure con `Origin` assente o diverso sono rifiutate.
- **Clickjacking:** `X-Frame-Options: DENY` e `frame-ancestors 'none'`.
- **Caching dei dati:** `no-store`.
- **File di configurazione:** `config.yaml` e `.env*` non sono raggiungibili via HTTP.

## Cosa non protegge
- Altri utenti o malware sullo stesso computer: chi può aprire `127.0.0.1:3000` o leggere i file è fuori dal modello.
- Non c'è login: chi raggiunge l'app è l'operatore.
- Non c'è HTTPS locale: il traffico è `http` sul loopback.

## Conseguenze
- Un `Host` senza porta o con altra porta è rifiutato (porta fissa a 3000).
- Pagine dinamiche per il nonce: nessun rendering statico, accettabile in locale.
- Alternativa scartata per la CSP: `'unsafe-inline'` anche per gli script (più semplice, ma annulla la protezione da XSS).
