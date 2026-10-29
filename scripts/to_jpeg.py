#!/usr/bin/env python3
"""Converte un'immagine (PNG/WebP/GIF/JPEG...) in JPEG adatto a Instagram.

Pensato come strumento per gli agenti e per publish_social.py: Instagram accetta solo JPEG per il feed.

Cosa fa:
  - appiattisce la trasparenza su sfondo bianco e converte in RGB;
  - toglie i metadati (EXIF, GPS): niente dati di posizione o dispositivo nelle immagini pubblicate;
  - se il lato lungo supera --max-side (default 1440), ridimensiona mantenendo le proporzioni;
  - con --pad-to (4:5, 1:1, 1.91:1) aggiunge bordo bianco per arrivare a quelle proporzioni, SENZA ritagliare
    (una locandina con testo non deve perdere i bordi);
  - avvisa se le proporzioni sono fuori dal range di Instagram (da 4:5 a 1.91:1) o il file supera 8 MB.

Sicurezza: non modifica né sovrascrive mai l'originale né un file esistente (salvo --force sul solo file di
destinazione, mai uguale all'originale). Di default scrive accanto all'originale con estensione .jpg
(es. locandina.png -> locandina.jpg).

Richiede Pillow:  python -m pip install --user Pillow

Esempi:
  python scripts/to_jpeg.py campagne/2026-castagnata/immagini/locandina.png
  python scripts/to_jpeg.py locandina.png --pad-to 4:5 --out campagne/2026-castagnata/immagini/locandina-ig.jpg
"""
import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True

try:
    from PIL import Image, ImageOps
except ImportError:
    print("ERRORE: manca Pillow. Installa con:  python -m pip install --user Pillow", file=sys.stderr)
    sys.exit(1)

MAX_BYTES = 8 * 1024 * 1024  # limite Instagram per le immagini
RATIO_MIN, RATIO_MAX = 4 / 5, 1.91  # larghezza/altezza ammesse nel feed
PRESETS = {"4:5": 4 / 5, "1:1": 1.0, "1.91:1": 1.91}


def fail(message, code=1):
    print(f"ERRORE: {message}", file=sys.stderr)
    sys.exit(code)


def flatten(im):
    """Porta l'immagine in RGB; trasparenza su bianco."""
    im = ImageOps.exif_transpose(im)  # rispetta l'orientamento, poi i metadati vengono scartati
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        rgba = im.convert("RGBA")
        base = Image.new("RGB", rgba.size, (255, 255, 255))
        base.paste(rgba, mask=rgba.getchannel("A"))
        return base
    return im.convert("RGB")


def pad_to_ratio(im, ratio):
    w, h = im.size
    if abs(w / h - ratio) < 0.005:
        return im
    if w / h > ratio:  # troppo larga: aggiungo altezza
        new_w, new_h = w, round(w / ratio)
    else:  # troppo alta: aggiungo larghezza
        new_w, new_h = round(h * ratio), h
    canvas = Image.new("RGB", (new_w, new_h), (255, 255, 255))
    canvas.paste(im, ((new_w - w) // 2, (new_h - h) // 2))
    return canvas


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Converte un'immagine in JPEG per Instagram (senza toccare l'originale).")
    p.add_argument("input", help="immagine di partenza")
    p.add_argument("--out", help="file di destinazione (default: stesso nome dell'originale con estensione .jpg)")
    p.add_argument("--quality", type=int, default=90, help="qualità JPEG 60-100 (default 90)")
    p.add_argument("--max-side", type=int, default=1440, help="lato lungo massimo in pixel (default 1440; 0 = non ridimensionare)")
    p.add_argument("--pad-to", choices=sorted(PRESETS), help="aggiunge bordo bianco fino a queste proporzioni (nessun ritaglio)")
    p.add_argument("--force", action="store_true", help="sovrascrive il file di destinazione se esiste già")
    args = p.parse_args()

    src = Path(args.input)
    if not src.is_file():
        fail(f"File non trovato: {src}")
    dst = Path(args.out) if args.out else src.with_suffix(".jpg")
    if dst.suffix.lower() not in (".jpg", ".jpeg"):
        fail("Il file di destinazione deve terminare in .jpg o .jpeg.")
    if dst.resolve() == src.resolve():
        fail("Destinazione uguale all'originale: non sovrascrivo gli originali. Indica un altro --out.")
    if dst.exists() and not args.force:
        fail(f"{dst.name} esiste già: non lo sovrascrivo (usa --force solo se è un file generato da qui).")
    if not 60 <= args.quality <= 100:
        fail("--quality deve essere tra 60 e 100.")
    if not dst.parent.is_dir():
        fail(f"Cartella di destinazione inesistente: {dst.parent}")

    try:
        with Image.open(src) as opened:
            opened.load()
            im = flatten(opened)
    except Exception as exc:  # Pillow solleva vari tipi per file corrotti
        fail(f"Impossibile leggere l'immagine ({type(exc).__name__}).")

    orig_size = im.size
    if args.pad_to:
        im = pad_to_ratio(im, PRESETS[args.pad_to])
    if args.max_side and max(im.size) > args.max_side:
        im.thumbnail((args.max_side, args.max_side), Image.LANCZOS)

    im.save(dst, "JPEG", quality=args.quality, optimize=True)  # nessun exif passato: metadati scartati
    size = dst.stat().st_size
    ratio = im.size[0] / im.size[1]

    print(f"✔ Creato {dst}")
    print(f"  Originale : {src.name}, {orig_size[0]}×{orig_size[1]}")
    print(f"  JPEG      : {im.size[0]}×{im.size[1]}, {size // 1024} KB, qualità {args.quality}")
    if not RATIO_MIN - 0.005 <= ratio <= RATIO_MAX + 0.005:
        print(f"  ⚠ Proporzioni {ratio:.2f}:1 fuori dal range del feed Instagram (da 0.80 a 1.91): "
              "usa --pad-to 4:5 (o 1:1) per aggiungere bordo senza ritagliare.")
    if size > MAX_BYTES:
        print("  ⚠ File sopra 8 MB: abbassa --quality o --max-side.")
    print("  Metadati rimossi. Prossimo passo: caricare il JPG sul sito (media WordPress) e usare l'URL con --image-url.")


if __name__ == "__main__":
    main()
