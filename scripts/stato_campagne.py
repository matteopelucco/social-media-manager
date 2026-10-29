#!/usr/bin/env python3
"""Riepilogo delle campagne: per ognuna stato, data evento, stato dei canali e file mancanti.

Sola lettura, nessuna rete. Per chi usa il progetto ogni giorno: "a che punto siamo?".

Uso:
  python scripts/stato_campagne.py            # tutte le campagne
  python scripts/stato_campagne.py 2026-castagnata
"""
import argparse
import re
import sys

sys.dont_write_bytecode = True

from _common import ROOT, reconfigure_streams  # noqa: E402

EXPECTED = ("brief.md", "checklist.md", "esito.md")


def frontmatter(text):
    data = {}
    match = re.match(r"^---\n(.*?)\n---", text, re.S)
    if match:
        for raw in match.group(1).splitlines():
            if ":" in raw:
                key, _, value = raw.partition(":")
                data[key.strip()] = re.split(r"\s+#", value, maxsplit=1)[0].strip()
    return data


def channels(text):
    """Righe della tabella '## Canali e testi' del brief: (canale, stato, approvato da)."""
    rows = []
    section = re.search(r"## Canali e testi\n(.*?)(?:\n## |\Z)", text, re.S)
    if not section:
        return rows
    for raw in section.group(1).splitlines():
        cells = [c.strip() for c in raw.strip().strip("|").split("|")]
        if len(cells) >= 4 and cells[0] not in ("Canale", "---") and not set(cells[0]) <= {"-"}:
            rows.append((cells[0], cells[2], cells[3]))
    return rows


def main():
    reconfigure_streams()
    p = argparse.ArgumentParser(description="Riepilogo delle campagne (sola lettura).")
    p.add_argument("campagna", nargs="?", help="cartella campagna (default: tutte)")
    args = p.parse_args()

    base = ROOT / "campagne"
    folders = [base / args.campagna] if args.campagna else sorted(d for d in base.iterdir() if d.is_dir())
    if not folders or (args.campagna and not folders[0].is_dir()):
        print("Nessuna campagna trovata in campagne/.")
        sys.exit(1)
    for folder in folders:
        brief_path = folder / "brief.md"
        print("=" * 60)
        print(folder.name)
        if not brief_path.is_file():
            print("  manca brief.md")
            continue
        text = brief_path.read_text(encoding="utf-8")
        fm = frontmatter(text)
        date = re.search(r"^\s*-\s*Data:\s*(.+)$", text, re.M)
        print(f"  Stato brief : {fm.get('stato', '?')}" + (f"   (approvato da {fm['approvato_da']})" if fm.get("approvato_da") else ""))
        if date:
            print(f"  Data evento : {date.group(1).strip()}")
        for name, state, who in channels(text):
            print(f"  - {name:<16} {state}" + (f"  [{who}]" if who else ""))
        missing = [f for f in EXPECTED if not (folder / f).is_file()]
        if missing:
            print("  File mancanti: " + ", ".join(missing))
        section = re.search(r"## Dati mancanti da chiedere\n(.*?)(?:\n## |\Z)", text, re.S)
        open_items = [l for l in (section.group(1).splitlines() if section else []) if re.match(r"^\s*-\s+\S", l)]
        if open_items:
            print(f"  Dati mancanti nel brief: {len(open_items)} voce/i da chiarire.")
    print("=" * 60)


if __name__ == "__main__":
    main()
