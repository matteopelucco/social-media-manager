# Guida: collegare Facebook e Instagram (Meta)

Serve una volta per cominciare e di nuovo quando il token scade o viene revocato. Tempo: circa 30 minuti la prima volta.
I nomi dei menu di Meta cambiano spesso: se una voce non coincide, cerca quella equivalente.

**Alla fine avrai tre valori per `config.yaml`:** `fb_page_id`, `fb_page_token`, `ig_user_id`.

> **Mai** incollare token, app secret o screenshot con token in chat, mail o documenti. Chi li vede può pubblicare al posto nostro.

## 0. Prima di iniziare
1. Un profilo Facebook personale che è **amministratore della Pagina** dell'asilo (Pagina → Impostazioni → Accesso alla Pagina).
2. L'account Instagram dell'asilo deve essere **professionale** (Business o Creator): app Instagram → Impostazioni → Tipo di account. Se l'app ti propone "Passa all'account personale" o "Passa a creator", è già Business: lascialo così.
3. L'account Instagram deve essere **collegato alla Pagina Facebook**: app Instagram → Modifica profilo → **Pagina** → Collega. Essere nello stesso Centro gestione account del tuo profilo personale **non basta**: l'API guarda il collegamento con la Pagina.

## 1. Creare l'app (una volta sola)
1. Vai su **developers.facebook.com**, accedi con il profilo amministratore e registrati come sviluppatore.
2. **Le mie app → Crea app.** Nome libero (es. "Asilo Sartorio Social"), tua email.
3. Nei **Casi d'uso** aggiungi quello per **gestire la Pagina** e quello per **Instagram** (contenuti).
4. In **Autorizzazioni e funzionalità** assicurati di avere:
   `pages_show_list`, `pages_read_engagement`, **`pages_manage_posts`**, `instagram_basic`, **`instagram_content_publish`**, `business_management`.
   Se `pages_manage_posts` non compare più avanti nell'Explorer, è perché manca qui.
5. Lascia l'app in modalità **Sviluppo**: per la Pagina di cui sei amministratore non serve la revisione di Meta. Non premere "Pubblica app".

## 2. Generare il token (la parte delicata)
Ordine importante: il token della Pagina deve nascere da un token **utente** di lunga durata, così **non scade**.

1. **Graph API Explorer** (developers.facebook.com/tools/explorer): scegli la tua app e "Token utente".
2. Seleziona i permessi del punto 1.4 e premi **Generate Access Token**. Nella finestra di Facebook **spunta la Pagina dell'asilo e l'account Instagram** (se compare la scelta di modificare l'accesso, usala).
3. **Token Debugger** (developers.facebook.com/tools/debug/accesstoken): incolla il token utente e premi **"Estendi token d'accesso"**. Copia il nuovo token (dura circa 60 giorni).
4. Torna nell'Explorer, incolla il token **esteso** nel campo del token e chiama:
   `me/accounts?fields=name,access_token,instagram_business_account`
5. Nel blocco **"Asilo Infantile 'Domenico Sartorio'"** leggi:
   - `id` → **`fb_page_id`** (un numero lungo);
   - `access_token` → **`fb_page_token`**;
   - `instagram_business_account` → `id` → **`ig_user_id`** (inizia con `17841…`, ed è **diverso** da `fb_page_id`).
6. Incolla nel Debugger il token della Pagina: **Tipo = Page**, **Scadenza = Never** (mai) e tra le autorizzazioni `pages_manage_posts` e `instagram_content_publish`.
7. Scrivi i tre valori in `config.yaml` (modello: `config.sample.yaml`). Poi: `python scripts/check_setup.py`.

> **Attenzione all'ordine.** Il pulsante "Estendi" compare solo per i token **utente** di breve durata. Nel passo 4 incolla il token esteso **a mano** nel campo dell'Explorer e **non** premere di nuovo "Generate Access Token", che lo sostituirebbe con uno breve. Se estendi direttamente un token **di Pagina**, ottieni un token di 60 giorni, non permanente: funziona, ma va rinnovato. `publish_social.py --check` mostra sempre la scadenza e avvisa quando mancano meno di 14 giorni.

## 3. Quando il token smette di funzionare
Tre cause comuni: scadenza (token di 60 giorni), revoca (cambio password Facebook, rimozione dell'app da "Integrazioni aziendali", perdita del ruolo di amministratore), cambio di permessi dell'app. In tutti i casi si ripete la sezione 2. Rimuovere l'app da Integrazioni aziendali **revoca tutti i token** dell'app: serve per invalidare un token finito dove non doveva, ma poi vanno rigenerati.

## 4. Problemi tipici

| Sintomo | Causa | Cosa fare |
|---|---|---|
| `me/accounts` non mostra la Pagina | il token non include la Pagina | rigenera il token e spunta la Pagina nella finestra; se serve rimuovi l'app da Integrazioni aziendali e riparti |
| `instagram_business_account` assente | Instagram non è professionale o non è collegato alla Pagina | sezione 0, punti 2 e 3; a volte serve anche `business_management` |
| `pages_manage_posts` non compare nell'Explorer | non è abilitato nei casi d'uso dell'app | sezione 1, punto 4; ricarica l'Explorer |
| errore 190 / 463 ("session invalidated") | token revocato o scaduto | sezione 3 |
| errore 200 ("publish_actions not available") in pubblicazione | token senza `pages_manage_posts`, o token utente al posto del token di Pagina | controlla il token nel Debugger (Tipo = Page, permessi) |
| `--check` avvisa "ID non numerico" o "ig_user_id uguale a fb_page_id" | in `config.yaml` c'è un nome o l'ID della Pagina al posto dell'ID Instagram | sezione 2, punto 5 |
| Instagram rifiuta l'immagine | non è JPEG o le proporzioni sono fuori range | `scripts/to_jpeg.py <immagine> --pad-to 4:5`, poi `scripts/upload_media.py` |

## 5. Buone pratiche
- Un secondo amministratore sulla Pagina e su Instagram: se tu cambi o lasci il ruolo, l'asilo non perde l'accesso.
- Segna nel calendario la scadenza del token (`--check` la mostra) e rigeneralo un paio di settimane prima.
- Il token sta solo in `config.yaml` o nelle variabili d'ambiente, mai nel codice né nei log.
