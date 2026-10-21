"""Valide le découpage produit par decoupage_chapitre.js et écrit le script du chapitre.

Contrôle indépendant : pour chaque paragraphe du manuscrit, les blocs joints par une espace doivent redonner
le paragraphe au caractère près (seul le tiret de dialogue initial « — » est retiré).
--sans-effet P0-P1:voix : annule l'effet de la voix (heaume…) pour ses blocs des paragraphes P0 à P1 inclus
(ex. masque retiré). Plusieurs plages possibles, séparées par des virgules.
Usage : preparer_script.py <manuscrit.txt> <sortie du workflow (.output) ou script.json> <script_chN.json> [--sans-effet 5-22:diamant]
"""
import argparse
import json
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manuscrit")
    ap.add_argument("entree")
    ap.add_argument("sortie")
    ap.add_argument("--sans-effet", default="")
    a = ap.parse_args()
    d = json.load(open(a.entree))
    if "result" in d:                                  # fichier de sortie du workflow
        d = d["result"]["final"]
    blocks = d["blocks"]
    paras = [l for l in open(a.manuscrit).read().split("\n") if l.strip()]
    bad = [i for i, p in enumerate(paras)
           if " ".join(b["text"] for b in blocks if b["para"] == i) != (p[2:] if p.startswith("— ") else p)]
    if bad:
        sys.exit(f"texte non conforme aux paragraphes {bad} : ne pas produire")
    for spec in filter(None, a.sans_effet.split(",")):
        rng, voix = spec.split(":")
        p0, p1 = map(int, rng.split("-"))
        for b in blocks:
            if b["speaker"] == voix and p0 <= b["para"] <= p1:
                b["fx"] = ""
    json.dump({"blocks": blocks, "notes": d.get("notes", "")}, open(a.sortie, "w"), ensure_ascii=False, indent=1)
    count = {}
    for b in blocks:
        count[b["speaker"]] = count.get(b["speaker"], 0) + 1
    print(f"OK : {len(paras)} paragraphes, {len(blocks)} blocs {count}, {sum(1 for b in blocks if b.get('fx') == '')} sans effet")
    print("tts_text ≠ text :", [(i + 1, b["tts_text"]) for i, b in enumerate(blocks) if b["tts_text"] != b["text"]])
    for i, b in enumerate(blocks):
        if b["speaker"] != "narrateur":
            print(f'  b{i + 1:03d} §{b["para"]:<3} {b["speaker"]:11} {b["tag"]:11} {"sans effet" if b.get("fx") == "" else "":10} {b["text"][:70]}')


if __name__ == "__main__":
    main()
