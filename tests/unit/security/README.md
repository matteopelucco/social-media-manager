# Test di sicurezza (issue #3, specifica `specs/03 - protezione-app-locale.md`)

I test automatici in questa cartella coprono gli scenari marcati "Unit" (REQ-PROT-02, 03, 04).
Gli scenari sotto sono **manuali**: si verificano e si documentano nella PR.

Il controllo statico su `public/` non e scritto: la cartella non esiste (punto aperto 2 della specifica).

## REQ-PROT-01 Ascolto solo su localhost
1. Avvia `npm run dev` (poi, separatamente, `npm run build` + `npm run start`).
2. Da PowerShell: `netstat -ano | findstr :3000`. Atteso: solo `127.0.0.1:3000` in LISTENING, mai `0.0.0.0:3000` o `[::]:3000`.
3. Da un altro dispositivo della rete locale apri `http://<IP del PC>:3000`: non deve rispondere.

## REQ-PROT-04 Rifiuto con header di sicurezza
1. Con l'app avviata: `curl -i -H "Host: evil.example" http://127.0.0.1:3000/`.
2. Atteso: 403, messaggio generico senza il motivo, con `Cache-Control: no-store`, CSP e `X-Frame-Options: DENY`, nessun `Access-Control-*`.
3. Ripeti con `curl -i -X POST http://127.0.0.1:3000/` (senza Origin): stesso esito.

## REQ-PROT-04 CSP: l'app si carica senza errori
1. In dev e dopo `npm run build` + `npm run start`, apri `http://localhost:3000` con la console del browser aperta.
2. Atteso: nessun errore "Content Security Policy" e pagina funzionante.

## REQ-PROT-04 Nonce applicato ai tag generati da Next
1. Con `npm run start`, ricarica la pagina due volte e guarda l'HTML (view-source).
2. Atteso: i tag `<script>` hanno `nonce="..."` uguale a quello nella CSP della risposta, e diverso tra le due richieste.

## REQ-PROT-05 File della radice non serviti
1. Crea file fittizi `config.yaml`, `.env`, `.env.local` nella radice (contenuto finto) e avvia l'app.
2. Con `curl -i --path-as-is` richiedi: `/config.yaml`, `/.env`, `/.env.local`, `/package.json`, `/../config.yaml`, `/%2e%2e/config.yaml`, `/%2e%2e/%2e%2e/.env`.
3. Atteso: ogni risposta 404 (o 403), contenuto mai visibile. Rimuovi i file fittizi.
