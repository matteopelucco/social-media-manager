# ADR 0001 — Adozione del framework my-ai-squad

- **Stato:** Accettata
- **Data:** 2026-10-29
- **Decisione di:** Matteo Pelucco

## Contesto
Il progetto (strumento Python per la comunicazione dell'asilo, che evolve nella web app Sheepper) è sviluppato con Claude Code. Il framework personale [my-ai-squad](https://github.com/matteopelucco/my-ai-squad) fornisce agenti, skill, guardrail, CI e convenzioni già collaudati in altri progetti (Girasole, Communio).

## Decisione
Adottare my-ai-squad v0.4.0 su un progetto esistente, in una PR (ADR-0010 del framework):
- plugin `squad-core` abilitato in `.claude/settings.json`; `AGENTS.md` come base e `CLAUDE.md` che lo importa (già così);
- file del template: `.claude/squad.json`, template di issue e PR, workflow `ci.yml` (gate `verifica`), `squad-triage`, `squad-close-issue`, ruleset di `main`, script `setup-labels`, `setup-project`, `apply-ruleset`, `classify-changes`;
- **stack: nessuno** per ora (solo nucleo). Quando nascerà il codice Next.js + Supabase + Vercel di Sheepper si abiliterà il pacchetto `squad-nextjs-supabase`;
- **`mergeMode: human`**: il merge è sempre dell'utente.

## Scostamenti dal template
1. **Comando di verifica:** nessun `typecheck`/`lint`/test esistono ancora; la verifica è un controllo di sintassi di `scripts/*.py`. Da sostituire con test veri (pytest sulla logica pura) quando ci sono.
2. **`ci.yml`:** aggiunto `actions/setup-python` (la verifica è in Python; il runner non garantisce `python`).
3. **`.claude/settings.json`:** aggiunta la regola `deny` su `Read(./config.yaml)`, in coerenza con la regola di progetto "non leggere né stampare `config.yaml`".
4. **`.gitattributes`:** `*.sh`, `*.yml`, `*.yaml` con fine riga LF, perché lo sviluppo avviene su Windows e gli script girano su Linux.
5. **`.copier-answers.yml` non aggiunto:** il comando `copier copy gh:matteopelucco/my-ai-squad` della guida all'adozione copia l'intero repository del framework invece del solo template (il `copier.yml` sta in `template/`, non alla radice). Il template è stato generato dal clone locale, quindi `_src_path` non punta a un indirizzo valido e `copier update` non è utilizzabile finché il framework non lo corregge.
6. Agenti e comandi specifici del dominio (`marketing-strategist`, `social-publisher`, `/nuova-campagna`, …) restano in `.claude/`: non esiste un equivalente nel nucleo.

## Conseguenze
- Gli aggiornamenti dei plugin arrivano da soli; quelli dei file di progetto vanno riportati a mano finché il punto 5 non è risolto.
- Dopo il merge servono azioni manuali dell'utente: label e Project (`scripts/setup-labels.sh`, `scripts/setup-project.sh`), ruleset di `main` (`scripts/apply-ruleset.sh`, richiede admin), un segreto tra `CLAUDE_CODE_OAUTH_TOKEN` e `ANTHROPIC_API_KEY` per il triage automatico.
