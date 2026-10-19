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

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format={fmt}"
MODEL = "eleven_multilingual_v2"
GUEST_VOICE = "JBFqnCBsd6RMkjVDRZzb"       # George — posé, chaleureux, français standard vérifié (l'invité)
JOURNALIST_VOICE = "iP95p4xoKVk53GoZ742B"  # Chris — plus grave, distinct de George
SETTINGS = {"stability": 0.7, "similarity_boost": 0.8, "style": 0.0, "use_speaker_boost": True, "speed": 0.92}
SEED = 1996


def synth(key, voice, payload, fmt="mp3_44100_128"):
    req = urllib.request.Request(API.format(voice=voice, fmt=fmt), data=json.dumps(payload).encode(),
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
    ap.add_argument("--seed", default="", help="graine par segment pour une nouvelle prise, ex. s04=7")
    ap.add_argument("--voice-journaliste", default=JOURNALIST_VOICE)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--format", default="mp3_44100_128", help="mp3_44100_192 sur les offres Creator et plus")
    ap.add_argument("--tag", default="", help="consigne de ton en tête de texte pour v3/v4, ex. [calm]")
    a = ap.parse_args()
    key = os.environ["ELEVENLABS_API_KEY"]
    voice_of = lambda spk: a.voice_journaliste if spk == "journaliste" else GUEST_VOICE
    speeds = dict(kv.split("=") for kv in a.speed.split(",") if kv)
    seeds = {k: int(v) for k, v in (kv.split("=") for kv in a.seed.split(",") if kv)}
    only = set(x for x in a.only.split(",") if x)
    segs = json.load(open(a.translation))
    out = pathlib.Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "manifest.json"
    manifest = json.load(open(manifest_path)) if manifest_path.exists() else {}
    billed = 0
    for i, s in enumerate(segs):
        if (only and s["id"] not in only) or not s["fr_tts"].strip():
            continue    # segment vide = interjection laissée en anglais
        same = lambda j: 0 <= j < len(segs) and segs[j]["turn"] == s["turn"] and segs[j]["fr_tts"].strip()
        settings = dict(SETTINGS, speed=float(speeds.get(s["id"], SETTINGS["speed"])))
        payload = {
            "text": s["fr_tts"],
            "model_id": a.model,
            "voice_settings": settings,
            "seed": seeds.get(s["id"], SEED),
            # les répliques très courtes sont instables seules : on leur donne toujours le contexte précédent
            "previous_text": segs[i - 1]["fr_tts"] if same(i - 1) or (i > 0 and len(s["fr_tts"]) < 15 and segs[i - 1]["fr_tts"].strip()) else None,
            "next_text": segs[i + 1]["fr_tts"] if same(i + 1) else None,
        }
        if a.model.endswith("v2_5"):
            payload["language_code"] = "fr"     # les modèles v2.5 acceptent de forcer la langue
        if a.model == "eleven_v4":
            # v4 : plus de réglage de vitesse ; ton guidé par une consigne entre crochets (non prononcée)
            payload["voice_settings"] = {"stability": 0.9, "similarity_boost": 0.8}
            payload["language_code"] = "fr"
            if a.tag:
                payload["text"] = f"{a.tag} {payload['text']}"
        if a.model == "eleven_v3":
            # v3 : stabilité 1.0 (« robuste », la plus sobre) ; pas de vitesse ni de contexte précédent/suivant
            payload["voice_settings"] = {"stability": 1.0, "similarity_boost": 0.8}
            payload.pop("previous_text", None)
            payload.pop("next_text", None)
        payload = {k: v for k, v in payload.items() if v is not None}
        voice = voice_of(s["speaker"])
        key_parts = [voice, payload] + ([a.format] if a.format != "mp3_44100_128" else [])
        h = hashlib.sha1(json.dumps(key_parts, sort_keys=True).encode()).hexdigest()[:12]
        f = out / f"{s['id']}.mp3"
        if f.exists() and manifest.get(s["id"], {}).get("hash") == h:
            continue
        audio, headers = synth(key, voice, payload, a.format)
        f.write_bytes(audio)
        cost = headers.get("character-cost") or headers.get("x-character-count") or str(len(s["fr_tts"]))
        billed += int(cost)
        manifest[s["id"]] = {"hash": h, "voice": voice, "speed": settings["speed"], "text": s["fr_tts"], "cost": int(cost)}
        json.dump(manifest, open(manifest_path, "w"), ensure_ascii=False, indent=1)
        print(f"{s['id']} {s['speaker'][:5]} speed={settings['speed']} cost={cost} | {s['fr_tts']}")
    print(f"caractères facturés cette exécution : {billed}")


if __name__ == "__main__":
    main()
