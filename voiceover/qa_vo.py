"""Contrôle qualité : retranscrit chaque segment VF (ElevenLabs Scribe) et le compare au texte attendu.

Signale les segments où la synthèse a sauté, ajouté ou déformé des mots (taux d'erreur par mot),
et vérifie la présence des noms propres. Usage : qa_vo.py <translation_fr.json> <tts_dir> <report.json> [--concat]
--concat : un seul appel Scribe sur tous les segments mis bout à bout (bien moins de crédits),
           les mots reconnus sont réattribués à chaque segment grâce aux horodatages.
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


def stt_concat(segs, tts_dir, key, workdir):
    """Colle les segments avec 1 s de silence, transcrit une fois, renvoie {id: texte entendu}."""
    import numpy as np
    sr, gap = 24000, 1.0
    parts, spans, t = [], {}, 0.0
    for s in segs:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(tts_dir, f"{s['id']}.mp3"), "-ac", "1",
                              "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
        x = np.frombuffer(raw, dtype=np.float32)
        spans[s["id"]] = (t, t + len(x) / sr)
        parts += [x, np.zeros(int(gap * sr), dtype=np.float32)]
        t += len(x) / sr + gap
    wav = os.path.join(workdir, "qa_concat.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", "-c:a", "libmp3lame",
                    "-b:a", "64k", wav.replace(".wav", ".mp3")], input=np.concatenate(parts).tobytes(), check=True)
    out = subprocess.run(["curl", "-sS", "--max-time", "600", "-X", "POST", "https://api.elevenlabs.io/v1/speech-to-text",
                          "-H", f"xi-api-key: {key}", "-F", "model_id=scribe_v2", "-F", "language_code=fr",
                          "-F", "timestamps_granularity=word", "-F", f"file=@{wav.replace('.wav', '.mp3')}"],
                         capture_output=True, check=True).stdout
    words = [w for w in json.loads(out)["words"] if w["type"] == "word"]
    heard = {}
    for sid, (a, b) in spans.items():
        heard[sid] = " ".join(w["text"] for w in words if a - 0.3 <= (w["start"] + w["end"]) / 2 <= b + 0.3)
    return heard


def main(tr_path, tts_dir, report_path, concat=False):
    key = os.environ["ELEVENLABS_API_KEY"]
    rows = []
    segs = [s for s in json.load(open(tr_path)) if s["fr_tts"].strip()]
    batch = stt_concat(segs, tts_dir, key, os.path.dirname(os.path.abspath(report_path))) if concat else None
    for s in segs:
        heard = batch[s["id"]] if concat else stt(os.path.join(tts_dir, f"{s['id']}.mp3"), key)
        w = wer(norm(s["fr_tts"]), norm(heard))
        missing = [n for n in NAMES if n.lower() in s["fr"].lower() and n.lower() not in heard.lower()]
        rows.append({"id": s["id"], "wer": round(w, 3), "attendu": s["fr_tts"], "entendu": heard, "noms_absents": missing})
        flag = "  <-- À VÉRIFIER" if w > 0.15 or missing else ""
        print(f"{s['id']} WER={w:.2f}{' noms:' + ','.join(missing) if missing else ''}{flag}\n   attendu : {s['fr_tts']}\n   entendu : {heard}")
    json.dump(rows, open(report_path, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:4], concat="--concat" in sys.argv)
