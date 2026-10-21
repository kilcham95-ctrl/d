"""Contrôle final et livraison d'un chapitre du livre audio.

1. retranscrit le chapitre entier (Scribe, MP3 96 kbps) et le compare mot à mot au manuscrit ;
2. écrit la fiche des voix (voix, effets, minutage de chaque réplique) ;
3. prépare le ZIP (MP3 192 kbps + fiche) et l'aperçu MP3 96 kbps mono à écouter dans le chat.
Dossier du chapitre : manuscrit_chN.txt, script_chN.json, voix.json, travail/, <nom>.mp3
Usage : livrer_chapitre.py <dossier> <N> "<titre du livre>" "<Chapitre … : titre>" <dossier_livraison> [--note "choix de lecture"]...
"""
import argparse
import difflib
import json
import os
import pathlib
import shutil
import subprocess
import zipfile

import livre_audio as L

NOMS = {"narrateur": "NARRATEUR", "diamant": "DIAMANT", "porcelaine": "PORCELAINE", "vieille": "LA VIEILLE",
        "villageois": "VILLAGEOIS", "villageoise": "VILLAGEOISE"}
JEU = {"[whispers]": " (chuchoté)", "[tired]": " (las)", "[hesitant]": " (hésitant)", "[calm]": " (posé)", "": ""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dossier")
    ap.add_argument("n", type=int)
    ap.add_argument("livre")
    ap.add_argument("chapitre")
    ap.add_argument("livraison")
    ap.add_argument("--note", action="append", default=[])
    a = ap.parse_args()
    key = os.environ["ELEVENLABS_API_KEY"]
    d = pathlib.Path(a.dossier)
    base = a.livre.replace(" ", "_")
    mp3 = d / f"{base}_ch{a.n}.mp3"
    tl = json.load(open(d / "travail" / "timeline.json"))
    bl = json.load(open(d / f"script_ch{a.n}.json"))["blocks"]
    v = json.load(open(d / "voix.json"))

    controle = d / "controle_96k.mp3"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(mp3), "-ac", "1", "-b:a", "96k", str(controle)], check=True)
    ref = L.norm_words(open(d / f"manuscrit_ch{a.n}.txt").read())
    hyp = L.norm_words(L.transcribe(key, controle))
    sm = difflib.SequenceMatcher(a=ref, b=hyp, autojunk=False)
    print(f"chapitre complet : {len(ref)} mots, écart {1 - sm.ratio():.3f}")
    print("  " + " ; ".join(f"{' '.join(ref[i1:i2])} -> {' '.join(hyp[j1:j2])}" for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"))

    out = [f"{a.livre} — {a.chapitre} — distribution des voix", "", "Voix (bibliothèque ElevenLabs, modèle eleven_v4) :"]
    for k in [k for k in NOMS if any(b["speaker"] == k for b in bl)]:
        out.append(f"  {NOMS[k]:12} {v[k]['nom']}" + ("   + effet de heaume dosé (ajouté en post-production)" if v[k].get("fx") else ""))
    if a.note:
        out += [""] + [f"Choix de lecture : {n}" for n in a.note]
    out += ["", "Minutage :"]
    for r, b in zip(tl, bl):
        m, s = divmod(r["debut"], 60)
        sans = " (sans heaume)" if b.get("fx") == "" and v[b["speaker"]].get("fx") else ""
        out.append(f"{int(m):02d}:{s:04.1f}  {NOMS[b['speaker']]:12}{JEU[b['tag']]}{sans}  {b['text']}")
    fiche = d / f"distribution_voix_ch{a.n}.txt"
    fiche.write_text("\n".join(out) + "\n")

    liv = pathlib.Path(a.livraison)
    liv.mkdir(parents=True, exist_ok=True)
    dossier_zip = f"{a.livre} - Chapitre {a.n}"
    with zipfile.ZipFile(liv / f"{base}_ch{a.n}.zip", "w") as z:
        z.write(mp3, f"{dossier_zip}/{mp3.name}")
        z.write(fiche, f"{dossier_zip}/{fiche.name}")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(mp3), "-ac", "1", "-b:a", "96k", str(liv / f"{base}_ch{a.n}_apercu.mp3")], check=True)
    premiers = {}
    for r, b in zip(tl, bl):
        premiers.setdefault(b["speaker"], r["debut"])
    print("première réplique :", {k: f"{int(t // 60)}:{int(t % 60):02d}" for k, t in premiers.items()})
    print("livraison :", liv)


if __name__ == "__main__":
    main()
