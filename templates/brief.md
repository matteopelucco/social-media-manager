---
campagna: AAAA-nome
stato: bozza            # bozza | approvato | pubblicato
approvato_da:           # es. Matteo / Lucia — compilare solo dopo l'ok esplicito
---

# Brief — [Nome evento]

## Dati confermati (gli UNICI usabili nei testi)
- Evento:
- Data:
- Ora:
- Luogo:
- Hashtag:
- Costi / prenotazioni / contatti:   <!-- solo se forniti; altrimenti "non previsti nel brief" -->

## Asset
- Locandina:
- Foto:
- Immagine Instagram (JPEG 4:5, da `scripts/to_jpeg.py`; poi caricata con `scripts/upload_media.py`): file `immagini/...-ig.jpg`, URL pubblico
- Logo: `brand/logo/logo-rosso.png`

## Obiettivo e pubblico
- Obiettivo:
- Pubblico principale:

## Dati mancanti da chiedere
-

## Dati per WordPress
- Titolo (max 4 parole):
- Slug:
- Estratto (3-4 parole):
- Categoria: avvisi        <!-- eventi: avvisi / slider solo se deve andare nel carosello -->
- Tag:
- Immagine in evidenza:
- Testo alternativo (italiano):   <!-- lo usano anche i post Facebook/Instagram: publish_social.py lo legge da qui -->

## Canali e testi
| Canale | File | Stato | Approvato da |
|---|---|---|---|
| Sito | testi/articolo-blog.html | bozza | |
| Facebook | testi/post-social.md (sezione Facebook) | bozza | |
| Instagram | testi/post-social.md (sezione Instagram) | bozza | |
| WhatsApp famiglie | testi/whatsapp.md | bozza | |
| Luino Notizie | ../../luino-notizie/AAAA-nome.md | bozza | |

## Esito
Vedi `esito.md` (link ai contenuti pubblicati, ID bozza WordPress, risultati).
