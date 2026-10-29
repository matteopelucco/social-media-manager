# ADR 0002 — Web app locale in Next.js con dati su filesystem

- **Stato:** Accettata
- **Data:** 2026-10-29
- **Decisione di:** Matteo Pelucco

## Contesto
Lo strumento attuale è un insieme di script Python usati da Claude Code. Il piano ([piano-webapp.md](../piano-webapp.md)) lo porta a una web app, Sheepper, che oggi serve a un solo operatore sul suo computer e domani a più associazioni (multi-tenant, Next.js + Supabase + Vercel). Serve uno stack che funzioni subito in locale senza servizi esterni e che non obblighi a riscrivere tutto al passaggio sul cloud.

## Decisione
- **Next.js 16** (App Router, TypeScript `strict`, Tailwind 4, ESLint con config flat, Vitest) alla radice del repository, avviato in locale e in ascolto solo su `127.0.0.1:3000`.
- **Dati su filesystem** (le cartelle di campagna esistenti) **dietro un'interfaccia** di accesso ai dati: la logica non conosce il filesystem, così il passaggio a Supabase sostituisce solo l'implementazione.
- **DeepSeek** come provider AI, chiamato con `fetch` dal server (nessun SDK aggiuntivo); le chiavi restano in configurazione locale, mai nel codice.
- Gli script Python restano lo strumento operativo finché la web app non ha la stessa funzionalità.

## Alternative valutate
1. **Python con FastAPI + HTMX:** riuso diretto degli script, ma stack diverso da quello di arrivo (Next.js + Supabase + Vercel); la UI andrebbe riscritta.
2. **Ibrido Next.js + servizio Python:** riuso degli script, ma due runtime da installare, avviare e mantenere per un solo operatore; più superficie di errore.

## Conseguenze
- Serve Node 22+ oltre a Python (finché esistono gli script).
- Verifica e CI includono `typecheck`, `lint`, test e `build`; il controllo di sintassi Python resta finché gli script esistono.
- Il filesystem vale solo in locale: su Vercel non è utilizzabile, quindi l'interfaccia dati è un vincolo di progetto, non un dettaglio.
- Il pacchetto `squad-nextjs-supabase` del framework (ADR 0001) potrà essere abilitato quando arriverà Supabase.
