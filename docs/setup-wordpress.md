# Guida: collegare WordPress (asilosartorio.it)

Serve una volta per cominciare. Tempo: 5 minuti.

**Alla fine avrai in `config.yaml`:** `wp_url`, `wp_user`, `wp_app_password`.

## 1. L'utente
- Meglio un **utente dedicato** (es. "Asilo Sartorio"), non il profilo personale di nessuno, così si può revocare senza toccare altro.
- Ruolo minimo: **Autore** (crea bozze e carica immagini). Con "Editor" funziona uguale: lo script non pubblica mai, a prescindere dai permessi.

## 2. La Application Password
1. Accedi a WordPress con quell'utente: **Utenti → Profilo**.
2. In fondo alla pagina, sezione **Application Passwords** (Password applicazione): dai un nome (es. "Marketing Claude") e premi **Aggiungi**.
3. Copia la password che compare **subito**: non si rivede. Ha spazi tra i gruppi di caratteri: vanno bene così.
4. Nel file `config.yaml`:
   ```
   wp_url: https://www.asilosartorio.it
   wp_user: nome-utente-wordpress
   wp_app_password: xxxx xxxx xxxx xxxx xxxx xxxx
   ```
   È una password **solo per le API**, diversa da quella con cui si fa il login.

## 3. Verifica
`python scripts/check_setup.py` (oppure `python scripts/publish_post.py --check`): deve dire che il sito risponde, che l'utente è autenticato e che può creare articoli e caricare file.

## 4. Cosa deve già esistere sul sito
- La categoria `avvisi` (e `slider` per il carosello della home): lo script **non crea categorie**.
- I tag: quelli mancanti si creano solo con `--create-tags` e dopo il tuo ok.

## 5. Problemi tipici
| Sintomo | Cosa fare |
|---|---|
| HTTP 401 | utente o password errati o revocati: genera una nuova Application Password |
| HTTP 403 | ruolo insufficiente o plugin di sicurezza/firewall che blocca la REST API: lo script si ferma e non aggira |
| HTTP 404 sulla REST API | permalink non attivi o API disattivata |
| Caricamento immagine rifiutato | probabile limite di dimensione del sito: riduci l'immagine |

## 6. Revoca
Se la password finisce dove non deve: **Utenti → Profilo → Application Passwords → Revoca**, poi creane una nuova.
