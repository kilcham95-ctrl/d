"""Contrôle qualité : retranscrit chaque segment VF (ElevenLabs Scribe) et le compare au texte attendu.

Signale les segments où la synthèse a sauté, ajouté ou déformé des mots (taux d'erreur par mot),
et vérifie la présence des noms propres. Usage : qa_vo.py <translation_fr.json> <tts_dir> <report.json>
"""
import json
import os
import re
import subprocess
import sys
import unicodedata

NAMES = ["Michael", "Ferrari", "Scuderia", "Jean Todt", "Brawn", "Ross", "Rory", "Silverstone",
         "Aston Martin", "Lawrence", "Adrian", "Eddie", "F1"]


def norm(t):
    from num2words import num2words   # Scribe écrit les nombres en chiffres, le texte TTS en lettres
    t = re.sub(r"\d+", lambda m: " " + num2words(int(m.group()), lang="fr") + " ", t)
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^a-z0-9' -]", " ", t).replace("'", " ").replace("-", " ")
    return t.split()


def wer(ref, hyp):
    d = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        prev, d[0] = d[0], i
        for j, h in enumerate(hyp, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (r != h))
    return d[-1] / max(1, len(ref))


def stt(path, key):
    out = subprocess.run(["curl", "-sS", "--max-time", "120", "-X", "POST", "https://api.elevenlabs.io/v1/speech-to-text",
                          "-H", f"xi-api-key: {key}", "-F", "model_id=scribe_v2", "-F", "language_code=fr",
                          "-F", f"file=@{path}"], capture_output=True, check=True).stdout
    return json.loads(out)["text"]


def main(tr_path, tts_dir, report_path):
    key = os.environ["ELEVENLABS_API_KEY"]
    rows = []
    for s in json.load(open(tr_path)):
        heard = stt(os.path.join(tts_dir, f"{s['id']}.mp3"), key)
        w = wer(norm(s["fr_tts"]), norm(heard))
        missing = [n for n in NAMES if n.lower() in s["fr"].lower() and n.lower() not in heard.lower()]
        rows.append({"id": s["id"], "wer": round(w, 3), "attendu": s["fr_tts"], "entendu": heard, "noms_absents": missing})
        flag = "  <-- À VÉRIFIER" if w > 0.15 or missing else ""
        print(f"{s['id']} WER={w:.2f}{' noms:' + ','.join(missing) if missing else ''}{flag}\n   attendu : {s['fr_tts']}\n   entendu : {heard}")
    json.dump(rows, open(report_path, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:4])
