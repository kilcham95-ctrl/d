"""Livre audio à plusieurs voix (ElevenLabs eleven_v4) à partir d'un script découpé par réplique.

Script (JSON) : {"blocks": [{"para", "speaker", "text", "tts_text", "tag", "pause_after"}, ...]}
Voix (JSON)   : {"narrateur": {"voice_id": "...", "stability": 0.7, "pan": 0}, ...}

1. synthèse de chaque bloc (cache par contenu), le tag de jeu ([whispers]…) en tête du texte, sans être lu ;
   le texte voisin est passé en previous_text / next_text pour garder l'intonation de la phrase ;
2. contrôle : chaque prise est retranscrite (Scribe) et comparée au texte ; fins coupées et bouffées parasites signalées ;
3. montage : silences rognés, niveau homogène par voix (les chuchotements gardent leur écart naturel),
   pauses du script, léger placement stéréo, normalisation -18 LUFS, crête vraie -3 dBTP.

Usage : livre_audio.py <script.json> <voix.json> <dossier_travail> <sortie.mp3> [--only id,id] [--seed id=N] [--no-qa]
La clé API vient de ELEVENLABS_API_KEY (jamais écrite sur disque par ce script).
"""
import argparse
import difflib
import hashlib
import json
import os
import pathlib
import re
import subprocess
import unicodedata
import urllib.request

import numpy as np

SR = 44100
API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_192"
STT = "https://api.elevenlabs.io/v1/speech-to-text"
TARGET_LUFS = -18.0
VOICE_LUFS = -20.0      # niveau de travail de chaque voix avant normalisation finale
WHISPER_DB = -6.0       # écart des chuchotements


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, **kw)


def decode(path):
    raw = run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def lufs(x):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", "ebur128", "-f", "null", "-"],
                       input=x.astype(np.float32).tobytes(), capture_output=True)
    return float(p.stderr.decode().split("Summary:")[-1].split("I:")[1].split("LUFS")[0])


def trim(x, rel_db=-45, pad=0.04):
    hop = int(0.005 * SR)
    n = len(x) // hop
    db = 10 * np.log10((x[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    loud = np.where(db > db.max() + rel_db)[0]
    # îlots de son séparés d'au moins 0,25 s ; un îlot très court et faible isolé au début ou à la fin
    # est un clic laissé par eleven_v4, pas de la parole
    runs = np.split(loud, np.where(np.diff(loud) > 50)[0] + 1)
    def parasite(r, gap):
        return len(r) < 24 and (db[r].max() < db.max() - 15 or gap >= 100)
    while len(runs) > 1 and parasite(runs[-1], runs[-1][0] - runs[-2][-1]):
        runs.pop()
    while len(runs) > 1 and parasite(runs[0], runs[1][0] - runs[0][-1]):
        runs.pop(0)
    a = max(0, runs[0][0] * hop - int(pad * SR))
    b = min(len(x), (runs[-1][-1] + 1) * hop + int(pad * SR))
    return x[a:b]


def norm_words(t):
    t = unicodedata.normalize("NFD", t.lower().replace("’", "'"))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-z0-9]+", t)


def synth(key, voice, payload):
    req = urllib.request.Request(API.format(voice=voice), data=json.dumps(payload).encode(),
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read(), int(r.headers.get("character-cost") or 0)


def transcribe(key, path):
    out = subprocess.run(["curl", "-sS", "--max-time", "180", "-X", "POST", STT, "-H", f"xi-api-key: {key}",
                          "-F", "model_id=scribe_v2", "-F", "language_code=fr", "-F", f"file=@{path}"],
                         capture_output=True, text=True).stdout
    return json.loads(out)["text"]


def tail_issue(x):
    """'coupée' si la parole va jusqu'au bord ; 'bouffée' si un bruit isolé suit un vrai silence en toute fin."""
    hop = int(0.005 * SR)
    n = len(x) // hop
    db = 10 * np.log10((x[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    db -= db.max()
    loud = np.where(db > -20)[0]
    if len(loud) and (n - 1 - loud[-1]) * 5 < 40:
        return "coupée"
    i, k = n - 1, 0
    while i > 0 and db[i] < -50:            # silence numérique final
        i -= 1
    while i > 0 and db[i] > -33 and k < 25:  # bruit court tout au bout
        i, k = i - 1, k + 1
    q = 0
    while i > 0 and db[i] <= -33:
        i, q = i - 1, q + 1
    if 0 < k < 25 and q >= 8 and n - i < 80:
        return "bouffée"
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("voices")
    ap.add_argument("work")
    ap.add_argument("out")
    ap.add_argument("--only", default="")
    ap.add_argument("--seed", default="")
    ap.add_argument("--no-qa", action="store_true")
    a = ap.parse_args()
    key = os.environ["ELEVENLABS_API_KEY"]
    blocks = json.load(open(a.script))["blocks"]
    voices = json.load(open(a.voices))
    seeds = {k: int(v) for k, v in (kv.split("=") for kv in a.seed.split(",") if kv)}
    work = pathlib.Path(a.work)
    (work / "prises").mkdir(parents=True, exist_ok=True)
    manifest_p = work / "manifest.json"
    manifest = json.load(open(manifest_p)) if manifest_p.exists() else {}
    for i, b in enumerate(blocks):
        b["id"] = f"b{i + 1:03d}"

    # 1. synthèse
    cost = 0
    for i, b in enumerate(blocks):
        v = voices[b["speaker"]]
        text = b["tts_text"].rstrip()
        if text[-1] in ",;:":                 # réplique coupée par une incise : eleven_v4 avale la fin d'une phrase en suspens
            text = text[:-1].rstrip() + "."
        payload = {"text": (b["tag"] + " " if b["tag"] else "") + text, "model_id": "eleven_v4", "language_code": "fr",
                   "voice_settings": {"stability": v.get("stability", 0.6), "similarity_boost": v.get("similarity", 0.8)}}
        if i > 0:
            payload["previous_text"] = blocks[i - 1]["tts_text"]
        if i + 1 < len(blocks):
            payload["next_text"] = blocks[i + 1]["tts_text"]
        if b["id"] in seeds:
            payload["seed"] = seeds[b["id"]]
        h = hashlib.sha1(json.dumps([v["voice_id"], payload], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        path = work / "prises" / f"{b['id']}.mp3"
        if manifest.get(b["id"]) == h and path.exists():
            continue
        if a.only and b["id"] not in a.only.split(","):
            if path.exists():
                continue
        audio, c = synth(key, v["voice_id"], payload)
        path.write_bytes(audio)
        manifest[b["id"]] = h
        cost += c
        json.dump(manifest, open(manifest_p, "w"), indent=0)
    print(f"crédits utilisés cette exécution : {cost}")

    # 2. contrôle
    qa_p = work / "qa.json"
    qa = json.load(open(qa_p)) if qa_p.exists() else {}
    for b in blocks:
        path = work / "prises" / f"{b['id']}.mp3"
        x = decode(path)
        b["fin"] = tail_issue(x)
        if a.no_qa:
            continue
        if qa.get(b["id"], {}).get("hash") != manifest.get(b["id"]):
            heard = transcribe(key, path)
            ref, hyp = norm_words(b["text"]), norm_words(heard)
            sm = difflib.SequenceMatcher(a=ref, b=hyp, autojunk=False)
            qa[b["id"]] = {"hash": manifest.get(b["id"]), "entendu": heard, "ecart": round(1 - sm.ratio(), 3),
                           "diff": " ; ".join(f"{' '.join(ref[i1:i2])} -> {' '.join(hyp[j1:j2])}"
                                              for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal")}
            json.dump(qa, open(qa_p, "w"), ensure_ascii=False, indent=1)
    if not a.no_qa:
        bad = [b for b in blocks if qa[b["id"]]["ecart"] > 0]
        print(f"contrôle : {len(blocks) - len(bad)}/{len(blocks)} prises identiques au texte")
        for b in bad:
            print(f"  {b['id']} [{b['speaker']}] {qa[b['id']]['diff']}")
    flagged = [f"{b['id']}:{b['fin']}" for b in blocks if b["fin"]]
    print("fins à vérifier :", " ".join(flagged) if flagged else "aucune")

    # 3. montage
    takes = {b["id"]: trim(decode(work / "prises" / f"{b['id']}.mp3")) for b in blocks}
    gain = {}
    for spk in {b["speaker"] for b in blocks}:
        ref = [takes[b["id"]] for b in blocks if b["speaker"] == spk and b["tag"] != "[whispers]"]
        if not ref:
            continue
        gain[spk] = 10 ** ((VOICE_LUFS - lufs(np.concatenate(ref))) / 20)
    pieces, t, timeline = [], 0.0, []
    for b in blocks:
        if b["tag"] == "[whispers]":          # chaque chuchotement : 6 dB sous la parole, toujours intelligible
            x = takes[b["id"]] * 10 ** ((VOICE_LUFS + WHISPER_DB - lufs(takes[b["id"]])) / 20)
        else:
            x = takes[b["id"]] * gain[b["speaker"]]
            if len(x) > 0.5 * SR and lufs(x) > VOICE_LUFS + 1.5:   # une courte réplique ne doit pas sauter au-dessus du récit
                x = x * 10 ** ((VOICE_LUFS + 1.5 - lufs(x)) / 20)
        pan = voices[b["speaker"]].get("pan", 0.0)
        l, r = np.sqrt((1 - pan) / 2) * np.sqrt(2), np.sqrt((1 + pan) / 2) * np.sqrt(2)
        st = np.stack([x * l, x * r], 1)
        pieces.append(st)
        timeline.append({"id": b["id"], "speaker": b["speaker"], "debut": round(t, 2), "fin": round(t + len(x) / SR, 2), "text": b["text"]})
        t += len(x) / SR
        sil = np.zeros((int(b["pause_after"] * SR), 2), np.float32)
        pieces.append(sil)
        t += len(sil) / SR
    lead = np.zeros((int(0.5 * SR), 2), np.float32)
    mix = np.concatenate([lead] + pieces + [np.zeros((int(1.5 * SR), 2), np.float32)])
    for row in timeline:
        row["debut"] += 0.5
        row["fin"] += 0.5
    raw = work / "montage.wav"
    run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_f32le", str(raw)],
        input=mix.astype(np.float32).tobytes())
    I = float(subprocess.run(["ffmpeg", "-hide_banner", "-i", str(raw), "-af", "ebur128", "-f", "null", "-"], capture_output=True)
              .stderr.decode().split("Summary:")[-1].split("I:")[1].split("LUFS")[0])
    final = work / "final.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-af",
         f"volume={TARGET_LUFS - I:.2f}dB,alimiter=limit=0.708:attack=3:release=80:level=disabled", "-c:a", "pcm_s24le", str(final)])
    run(["ffmpeg", "-v", "error", "-y", "-i", str(final), "-c:a", "libmp3lame", "-b:a", "192k", "-ar", str(SR), a.out])
    json.dump(timeline, open(work / "timeline.json", "w"), ensure_ascii=False, indent=1)
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True)
    s = p.stderr.decode().split("Summary:")[-1]
    print(f"durée {len(mix) / SR / 60:.1f} min | {s.split('I:')[1].split('LUFS')[0].strip()} LUFS | crête {s.split('Peak:')[1].split('dBFS')[0].strip()} dBTP")


if __name__ == "__main__":
    main()
