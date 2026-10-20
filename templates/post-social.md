# Template post social

> Compila SOLO con dati presenti nel brief. Se manca qualcosa, chiedi. Tutto resta in BOZZA finché non c'è l'ok esplicito in chat.

## Facebook
```
[Gancio: 1 riga che fa venire voglia di leggere]

[2-4 righe: cosa, quando, dove, perché venire. Diamo del tu.]

📅 [data e ora]
📍 [luogo]

[invito all'azione: condividi / tagga / scrivici]

[hashtag]
```
- Immagine: locandina (o foto). Link al sito nel primo commento o nel testo, se c'è un articolo.

## Instagram (feed)
```
[Gancio nelle prime 125 caratteri: il resto viene tagliato con "altro"]

[2-4 righe, andando a capo. Diamo del tu.]

📅 [data e ora]
📍 [luogo]

[invito all'azione]

.
.
[hashtag]
```
- I link nel testo non sono cliccabili: scrivi "link in bio" solo se il link in bio è davvero aggiornato.
- Testo alternativo dell'immagine: lo prende `publish_social.py` dal brief ("Testo alternativo (italiano)").
- Immagine: JPEG 4:5 con URL pubblico (vedi `to_jpeg.py` e `upload_media.py`).

## Instagram Stories (facoltativo)
- Formato verticale 9:16; testo brevissimo (data, ora, luogo). Una sola idea per storia.

## Note di pubblicazione
- Canale: `/pubblica-social` (Facebook e Instagram, un canale per volta, con ok esplicito) oppure Metricool/post diretto a mano.
- Le sezioni "## Facebook" e "## Instagram" di questo file sono la fonte dei testi: ogni testo definitivo sta in UN solo file (`post-social.md`, oppure `post-facebook.md` / `post-instagram.md` se serve un adattamento; in quel caso, nell'altro file, indica dove sta).
- Giorno/ora proposti: [da definire con approvazione]
- Esito (link al post): [compilare dopo la pubblicazione, in `esito.md`]
