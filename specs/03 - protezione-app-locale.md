# Protezione dell'app locale (issue #3)

L'app può leggere segreti e pubblicare: deve essere raggiungibile solo dal computer dell'utente e non da pagine web esterne.

## Requisiti
- **REQ-PROT-01** L'app ascolta solo su `127.0.0.1:3000` (dev e start), mai su `0.0.0.0`.
- **REQ-PROT-02** Una richiesta è ammessa solo se l'header `Host` è `localhost:3000`, `127.0.0.1:3000` o `[::1]:3000` (senza distinzione tra maiuscole e minuscole). Altrimenti 403.
- **REQ-PROT-03** Sui metodi non sicuri (tutti tranne GET e HEAD) l'header `Origin` deve essere presente ed essere uguale a `http://<Host della richiesta>`. Altrimenti 403.
- **REQ-PROT-04** Ogni risposta porta gli header di sicurezza: `Cache-Control: no-store`, CSP, `X-Frame-Options: DENY`; mai `Access-Control-Allow-Origin`.
- **REQ-PROT-05** Nessun file della radice del progetto è servito via HTTP.

## Convenzione di copertura
**Unit** = test Vitest su logica pura in `lib/security/`. Nomi indicativi: `isHostAllowed(host)`, `isRequestAllowed({ host, origin, method })`, `securityHeaders({ isDev, nonce })`. **Manuale** = verifica documentata nella PR.

## Verificato nella documentazione di Next 16 (`node_modules/next/dist/docs/01-app/`)
- **Nome e posizione:** il middleware si chiama Proxy: file `proxy.ts` nella radice, allo stesso livello di `app/`; ne è ammesso uno solo per progetto (`01-getting-started/16-proxy.md`).
- **Firma:** `export function proxy(request: NextRequest)` (oppure export di default); può essere `async`.
- **Runtime:** Node.js di default; l'opzione `runtime` non è ammessa in `proxy.ts` (darebbe errore). Quindi `crypto` e `Buffer` sono disponibili.
- **Matcher:** senza `matcher` il proxy gira su tutto, anche `_next/static`, `public/` e immagini. Decisione: **nessuna esclusione** per il controllo di Host e Origin (così anche gli asset sono protetti); per la CSP con nonce la guida consiglia di escludere prefetch e statici, ma l'esclusione non è necessaria qui e si evita per semplicità. `_next/data` è comunque sempre coperto.
- **Rifiutare con 403:** il proxy può rispondere direttamente, per esempio `Response.json({ ... }, { status: 401 })`. Qui si usa lo stesso schema con status 403 e messaggio generico.
- **Header:** in `proxy.ts` si impostano con `response.headers.set(...)` su `NextResponse.next()`. Con `headers()` in `next.config.ts` gli header sono statici e non possono contenere un nonce per richiesta.
- **Server Functions:** sono POST sulla route della pagina; il proxy le copre solo se il matcher copre quella route. Con nessuna esclusione sono coperte.
- **Dev:** `allowedDevOrigins` riguarda solo origini aggiuntive per il server di sviluppo; non va configurato (nessuna origine extra).

## Decisioni
- **Host senza porta: rifiutato.** Un browser che apre l'app sulla porta 3000 invia sempre `Host: <nome>:3000`; un Host senza porta significa porta 80/443, quindi non è la nostra app. La documentazione non prevede alcuna eccezione. Rifiutare è la regola più stretta e non costa nulla all'utente.
- **GET e HEAD ammessi con qualsiasi Origin:** una lettura cross-origin non è esposta alla pagina esterna perché non c'è CORS; protegge il controllo sull'Host. `OPTIONS` conta come metodo non sicuro.
- **CSP in produzione: DA CONFERMARE NELLA PR.** Regola più stretta compatibile con Next: nonce per richiesta generato in `proxy.ts` con `'strict-dynamic'`, senza `'unsafe-inline'` né `'unsafe-eval'` per gli script; richiede rendering dinamico delle pagine (`connection()`), accettabile in un'app locale. Se gli stili con nonce creassero problemi, ripiego ammesso solo per `style-src`: `'unsafe-inline'`, da dichiarare nella PR. `upgrade-insecure-requests` dell'esempio della guida NON si usa: l'app è solo `http` locale e romperebbe il caricamento degli asset.
- **CSP in dev:** `'unsafe-eval'` negli script (la guida lo richiede per React in sviluppo); stili con `'unsafe-inline'` ammessi solo in dev.

## Scenari: Host

## Scenario: Host locale con nome localhost
Given una richiesta GET con Host `localhost:3000`
When la richiesta viene valutata
Then è ammessa.
Copertura: Unit. (REQ-PROT-02)

## Scenario: Host locale con IPv4
Given una richiesta GET con Host `127.0.0.1:3000`
When viene valutata
Then è ammessa.
Copertura: Unit. (REQ-PROT-02)

## Scenario: Host locale con IPv6
Given una richiesta GET con Host `[::1]:3000`
When viene valutata
Then è ammessa.
Copertura: Unit. (REQ-PROT-02)

## Scenario: Host con maiuscole
Given una richiesta GET con Host `LocalHost:3000`
When viene valutata
Then è ammessa.
Copertura: Unit. (REQ-PROT-02)

## Scenario: Host esterno
Given una richiesta GET con Host `evil.example`
When viene valutata
Then è rifiutata con 403.
Copertura: Unit. (REQ-PROT-02)

## Scenario: DNS rebinding con prefisso locale
Given una richiesta GET con Host `127.0.0.1.evil.example:3000`
When viene valutata
Then è rifiutata con 403 (il confronto è sul nome intero, non sul prefisso).
Copertura: Unit. (REQ-PROT-02)

## Scenario: DNS rebinding con suffisso locale
Given una richiesta GET con Host `localhost.evil.example:3000`
When viene valutata
Then è rifiutata con 403.
Copertura: Unit. (REQ-PROT-02)

## Scenario: IP di rete locale
Given una richiesta GET con Host `192.168.1.20:3000`
When viene valutata
Then è rifiutata con 403.
Copertura: Unit. (REQ-PROT-02)

## Scenario: Host assente
Given una richiesta senza header Host (o vuoto)
When viene valutata
Then è rifiutata con 403.
Copertura: Unit. (REQ-PROT-02)

## Scenario: Porta diversa
Given una richiesta GET con Host `localhost:4000`
When viene valutata
Then è rifiutata con 403.
Copertura: Unit. (REQ-PROT-02)

## Scenario: Host locale senza porta
Given una richiesta GET con Host `localhost` (senza porta)
When viene valutata
Then è rifiutata con 403 (vedi Decisioni).
Copertura: Unit. (REQ-PROT-02)

## Scenari: Origin e metodi

## Scenario: Metodo sicuro senza Origin
Given una richiesta GET (o HEAD) con Host `127.0.0.1:3000` e nessun Origin
When viene valutata
Then è ammessa (normale navigazione).
Copertura: Unit. (REQ-PROT-03)

## Scenario: Metodo sicuro con Origin esterno
Given una richiesta GET con Host `127.0.0.1:3000` e Origin `https://evil.example`
When viene valutata
Then è ammessa (la risposta non porta CORS, quindi la pagina esterna non può leggerla).
Copertura: Unit. (REQ-PROT-03)

## Scenario: Metodo non sicuro con Origin uguale
Given una richiesta POST con Host `127.0.0.1:3000` e Origin `http://127.0.0.1:3000`
When viene valutata
Then è ammessa.
Copertura: Unit. (REQ-PROT-03)

## Scenario: Metodo non sicuro con Origin diverso
Given una richiesta POST (o PUT, PATCH, DELETE) con Host `127.0.0.1:3000` e Origin `https://evil.example`
When viene valutata
Then è rifiutata con 403.
Copertura: Unit. (REQ-PROT-03)

## Scenario: Origin locale ma di un altro host
Given una richiesta POST con Host `127.0.0.1:3000` e Origin `http://localhost:3000`
When viene valutata
Then è rifiutata con 403 (deve coincidere con l'Host della richiesta).
Copertura: Unit. (REQ-PROT-03)

## Scenario: Metodo non sicuro senza Origin
Given una richiesta POST con Host valido e nessun Origin
When viene valutata
Then è rifiutata con 403.
Copertura: Unit. (REQ-PROT-03)

## Scenario: Metodo non sicuro con Origin null
Given una richiesta POST con Host valido e Origin `null`
When viene valutata
Then è rifiutata con 403.
Copertura: Unit. (REQ-PROT-03)

## Scenario: Metodo non sicuro con Host non valido
Given una richiesta POST con Host `evil.example` e Origin `http://evil.example`
When viene valutata
Then è rifiutata con 403 (origin uguale all'host non basta).
Copertura: Unit. (REQ-PROT-02, REQ-PROT-03)

## Scenario: OPTIONS e metodo in minuscolo
Given una richiesta `OPTIONS` (preflight) con Origin assente o esterno, oppure un metodo scritto in minuscolo
When viene valutata
Then OPTIONS è trattato come non sicuro (rifiutata); il metodo è normalizzato in maiuscolo prima del confronto.
Copertura: Unit. (REQ-PROT-03)

## Scenari: header di risposta

## Scenario: Cache disattivata
Given l'insieme degli header di sicurezza
When lo si legge
Then `Cache-Control` vale `no-store`.
Copertura: Unit. (REQ-PROT-04)

## Scenario: Niente incorniciamento
Given l'insieme degli header di sicurezza
When lo si legge
Then `X-Frame-Options` vale `DENY` e la CSP contiene `frame-ancestors 'none'`.
Copertura: Unit. (REQ-PROT-04)

## Scenario: CSP in produzione
Given gli header per la produzione con nonce `abc123`
When si legge la CSP
Then contiene `default-src 'self'`, `script-src 'self' 'nonce-abc123' 'strict-dynamic'`, `object-src 'none'`, `base-uri 'self'`, `form-action 'self'`, `frame-ancestors 'none'`; non contiene `'unsafe-eval'`, non contiene `'unsafe-inline'` in `script-src`, non contiene `upgrade-insecure-requests`.
Copertura: Unit. (REQ-PROT-04; scelta da confermare nella PR)

## Scenario: CSP in sviluppo
Given gli header per lo sviluppo
When si legge la CSP
Then `script-src` ammette anche `'unsafe-eval'` e il resto resta come in produzione.
Copertura: Unit (flag dev/produzione). Che l'app si carichi senza errori CSP in console, in dev e dopo `npm run build` + `npm run start`: Manuale. (REQ-PROT-04)

## Scenario: Nonce diverso a ogni richiesta
Given due richieste successive
When il proxy genera gli header
Then i nonce sono diversi e il nonce compare nella CSP.
Copertura: Unit per la funzione che genera il nonce (valori distinti, base64 non vuoto); Manuale per l'applicazione ai tag generati da Next. (REQ-PROT-04)

## Scenario: Nessun CORS aperto
Given l'insieme degli header di sicurezza
When lo si legge
Then non contiene `Access-Control-Allow-Origin` (né altri `Access-Control-*`).
Copertura: Unit. (REQ-PROT-04)

## Scenario: Rifiuto con header di sicurezza
Given una richiesta rifiutata dal proxy
When viene emessa la risposta 403
Then porta gli stessi header di sicurezza e un messaggio generico, senza dettagli sul motivo.
Copertura: Manuale (`proxy.ts` è un involucro sottile sulla logica pura). (REQ-PROT-04)

## Scenari: ascolto e file

## Scenario: Ascolto solo su localhost
Given l'app avviata con `npm run dev` o `npm run start`
When si controlla l'indirizzo di ascolto
Then è `127.0.0.1:3000`; un'altra macchina della rete non raggiunge la porta.
Copertura: Manuale (gli script di `package.json` hanno già `-H 127.0.0.1`; verifica con `netstat` e dalla rete locale). (REQ-PROT-01)

## Scenario: File della radice non serviti
Given l'app avviata e file fittizi `config.yaml`, `.env`, `.env.local` nella radice
When si richiede via HTTP `/config.yaml`, `/.env`, `/.env.local`, `/package.json`, `/../config.yaml` e le stesse con percorso codificato (`%2e%2e`)
Then ogni richiesta risponde 404 (o 403) e il contenuto non compare mai.
Copertura: Manuale con file fittizi. In unit solo un controllo statico: `public/` (se esiste) non contiene file sensibili. (REQ-PROT-05)

## Casi limite
- Host con spazi o più valori separati da virgola: rifiutato.
- Origin con schema `https://` e stesso host e porta: rifiutato (l'app è solo `http`).

## Fuori ambito
- Login, password, sessioni, utenti multipli e ruoli.
- HTTPS locale e certificati.
- Protezione da altri processi o utenti sullo stesso computer (un solo utente; vedi ADR 0003).
- Rate limiting, token CSRF, audit log.
- Porta configurabile (fissa a 3000).
- Test E2E automatici.

## Punti aperti
1. CSP di produzione (nonce e `strict-dynamic`, rendering dinamico): da confermare nella PR.
2. Il test statico su `public/` ha senso solo se la cartella esiste; altrimenti resta la verifica manuale.
