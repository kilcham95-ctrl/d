"""Génère la voix française segment par segment avec l'API ElevenLabs.

- clé lue dans la variable d'environnement ELEVENLABS_API_KEY (jamais écrite dans le dépôt)
- cache : un segment n'est régénéré que si son texte, sa voix ou ses réglages changent
- previous_text / next_text : continuité de prosodie à l'intérieur d'une prise de parole
Usage : tts.py <translation_fr.json> <outdir> [--only s01,s02] [--speed s05=1.08,...]
"""
import argparse
import hashlib
import json
import os
import pathlib
import time
import urllib.error
import urllib.request

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"
MODEL = "eleven_multilingual_v2"
VOICES = {
    "eddie_irvine": "JBFqnCBsd6RMkjVDRZzb",   # George — posé, chaleureux, français standard vérifié
    "journaliste": "iP95p4xoKVk53GoZ742B",    # Chris — plus grave, distinct de George
}
SETTINGS = {"stability": 0.7, "similarity_boost": 0.8, "style": 0.0, "use_speaker_boost": True, "speed": 1.0}
SEED = 1996


def synth(key, voice, payload):
    req = urllib.request.Request(API.format(voice=voice), data=json.dumps(payload).encode(),
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code in (429, 500, 502, 503) and attempt < 4:
                time.sleep(2 ** (attempt + 1))
                continue
            raise SystemExit(f"HTTP {e.code}: {body}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("translation")
    ap.add_argument("outdir")
    ap.add_argument("--only", default="")
    ap.add_argument("--speed", default="")
    ap.add_argument("--voice-journaliste", default=VOICES["journaliste"])
    a = ap.parse_args()
    key = os.environ["ELEVENLABS_API_KEY"]
    voices = dict(VOICES, journaliste=a.voice_journaliste)
    speeds = dict(kv.split("=") for kv in a.speed.split(",") if kv)
    only = set(x for x in a.only.split(",") if x)
    segs = json.load(open(a.translation))
    out = pathlib.Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "manifest.json"
    manifest = json.load(open(manifest_path)) if manifest_path.exists() else {}
    billed = 0
    for i, s in enumerate(segs):
        if only and s["id"] not in only:
            continue
        same = lambda j: 0 <= j < len(segs) and segs[j]["turn"] == s["turn"]
        settings = dict(SETTINGS, speed=float(speeds.get(s["id"], SETTINGS["speed"])))
        payload = {
            "text": s["fr_tts"],
            "model_id": MODEL,
            "voice_settings": settings,
            "seed": SEED,
            "previous_text": segs[i - 1]["fr_tts"] if same(i - 1) else None,
            "next_text": segs[i + 1]["fr_tts"] if same(i + 1) else None,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        voice = voices[s["speaker"]]
        h = hashlib.sha1(json.dumps([voice, payload], sort_keys=True).encode()).hexdigest()[:12]
        f = out / f"{s['id']}.mp3"
        if f.exists() and manifest.get(s["id"], {}).get("hash") == h:
            continue
        audio, headers = synth(key, voice, payload)
        f.write_bytes(audio)
        cost = headers.get("character-cost") or headers.get("x-character-count") or str(len(s["fr_tts"]))
        billed += int(cost)
        manifest[s["id"]] = {"hash": h, "voice": voice, "speed": settings["speed"], "text": s["fr_tts"], "cost": int(cost)}
        json.dump(manifest, open(manifest_path, "w"), ensure_ascii=False, indent=1)
        print(f"{s['id']} {s['speaker'][:5]} speed={settings['speed']} cost={cost} | {s['fr_tts']}")
    print(f"caractères facturés cette exécution : {billed}")


if __name__ == "__main__":
    main()
