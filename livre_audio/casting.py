"""Casting des voix du livre audio (bibliothèque ElevenLabs, voix françaises natives).

chercher    : liste les voix de la bibliothèque vérifiées UNIQUEMENT en français (fr-FR, sans accent régional),
              triées par popularité.
              casting.py chercher --genre male --ages middle_aged,old [--min-clones 3000] [--mots deep,calm]
auditionner : fait lire la même réplique à chaque voix (eleven_v4, stability 0.6) et mesure hauteur (F0), variation
              de hauteur (jeu retenu), bruit de fond, ressemblance au narrateur et retranscription.
              casting.py auditionner --texte "…" --voix id1,id2 --dossier D [--genre male] [--reference ID_NARRATEUR]
essais      : assemble un fichier d'essais : pour chaque voix, une annonce du narrateur (« Voix un : Martin. ») puis sa réplique.
              casting.py essais --dossier D --voix id1:Martin,id2:Guillaume --sortie essais.mp3 [--narrateur ID]
Repères : homme mûr F0 ≈ 100-120 Hz (au-dessus de 140 Hz la voix sonne jeune) ; bruit de fond sous -65 dB ;
ressemblance au narrateur ≤ 0.70. Dépendances : pip install praat-parselmouth resemblyzer.
"""
import argparse
import json
import os
import pathlib
import subprocess
import urllib.parse
import urllib.request

import numpy as np

import livre_audio as L

NARRATEUR = "5l4ttmr4SKNgi0HnOelT"      # Paul K
ACCENTS_EXCLUS = {"african", "canadian", "quebec", "belgian", "swiss", "meridional"}
NOMBRES = ["un", "deux", "trois", "quatre", "cinq", "six"]


def key():
    k = os.environ.get("ELEVENLABS_API_KEY", "")
    if not k:
        raise SystemExit("ELEVENLABS_API_KEY manquante")
    return k


def fr_seulement(v):
    langs = {x.get("language") for x in v.get("verified_languages", [])}
    return langs == {"fr"} and (v.get("locale") or "").startswith("fr-FR") and (v.get("accent") or "") not in ACCENTS_EXCLUS


def chercher(a):
    voix = {}
    for age in a.ages.split(","):
        for page in range(10):
            q = {"page_size": 100, "page": page, "language": "fr", "gender": a.genre, "age": age}
            if a.recherche:
                q["search"] = a.recherche
            req = urllib.request.Request("https://api.elevenlabs.io/v1/shared-voices?" + urllib.parse.urlencode(q),
                                         headers={"xi-api-key": key()})
            d = json.load(urllib.request.urlopen(req, timeout=60))
            for v in d.get("voices", []):
                voix.setdefault(v["voice_id"], v)
            if not d.get("has_more"):
                break
    mots = [m.lower() for m in a.mots.split(",") if m]
    garde = [v for v in voix.values() if fr_seulement(v) and (v.get("cloned_by_count") or 0) >= a.min_clones
             and all(m in ((v.get("description") or "") + " " + (v.get("descriptive") or "") + " " + v["name"]).lower() for m in mots)]
    for v in sorted(garde, key=lambda v: -(v.get("cloned_by_count") or 0)):
        print(f'{v["voice_id"]} | {v["name"][:32]:32} | {v.get("age", "")[:6]:6} | {(v.get("descriptive") or "")[:10]:10} | '
              f'{(v.get("category") or "")[:12]:12} | {v.get("cloned_by_count") or 0:7} clones | {(v.get("description") or "").replace(chr(10), " ")[:100]}')
    print(f"{len(garde)} voix uniquement françaises sur {len(voix)}")


def prise(vid, texte, out, stability=0.6):
    if out.exists():
        return 0
    payload = {"text": texte, "model_id": "eleven_v4", "language_code": "fr", "voice_settings": {"stability": stability, "similarity_boost": 0.8}}
    audio, c = L.synth(key(), vid, payload)
    out.write_bytes(audio)
    return c


def mesures(path, homme):
    import parselmouth
    fmin, fmax = (60, 300) if homme else (100, 500)
    wav = path.with_suffix(".wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-ac", "1", "-ar", "22050", str(wav)], check=True)
    snd = parselmouth.Sound(str(wav)).convert_to_mono()
    f0 = snd.to_pitch(time_step=0.01, pitch_floor=fmin, pitch_ceiling=fmax).selected_array["frequency"]
    f0 = f0[f0 > 0]
    x = snd.values[0]
    hop = 441
    n = len(x) // hop
    db = 10 * np.log10((x[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    return {"f0": float(np.median(f0)), "variation": float(np.std(12 * np.log2(f0 / np.median(f0)))),
            "fond": float(np.percentile(db, 5)), "duree": snd.duration, "wav": wav}


def auditionner(a):
    from resemblyzer import VoiceEncoder, preprocess_wav
    d = pathlib.Path(a.dossier)
    d.mkdir(parents=True, exist_ok=True)
    cout = prise(a.reference, a.texte, d / "_reference.mp3", 0.65)
    enc = VoiceEncoder(verbose=False)
    ref = enc.embed_utterance(preprocess_wav(str(mesures(d / "_reference.mp3", True)["wav"])))
    for vid in a.voix.split(","):
        mp3 = d / f"{vid}.mp3"
        cout += prise(vid, a.texte, mp3)
        m = mesures(mp3, a.genre == "male")
        sim = float(np.dot(ref, enc.embed_utterance(preprocess_wav(str(m["wav"])))))
        entendu = L.transcribe(key(), mp3)
        ok = L.norm_words(entendu) == L.norm_words(a.texte)
        print(f"{vid} | F0 {m['f0']:4.0f} Hz | variation {m['variation']:.2f} dt | fond {m['fond']:4.0f} dB | "
              f"ressemblance narrateur {sim:.2f} | débit {len(a.texte) / m['duree']:4.1f} car/s | {'texte exact' if ok else entendu}")
    print(f"crédits : {cout}")


def essais(a):
    d = pathlib.Path(a.dossier)
    cout, parts = 0, []
    norm = lambda y: y * 10 ** ((-20 - L.lufs(y)) / 20)
    sil = lambda s: np.zeros(int(s * L.SR), np.float32)
    for i, item in enumerate(a.voix.split(",")):
        vid, nom = item.split(":", 1)
        annonce = d / f"_annonce_{i + 1}_{vid}.mp3"
        cout += prise(a.narrateur, f"Voix {NOMBRES[i]} : {nom}.", annonce, 0.7)
        parts += [norm(L.trim(L.decode(annonce))), sil(0.7), norm(L.trim(L.decode(d / f"{vid}.mp3"))), sil(1.4)]
    y = np.concatenate(parts)
    y = np.stack([y, y], 1) / np.abs(y).max() * 0.68
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(L.SR), "-ac", "2", "-i", "-", "-c:a", "libmp3lame",
                    "-b:a", "128k", a.sortie], input=y.astype(np.float32).tobytes(), check=True)
    print(f"{a.sortie} : {len(y) / L.SR:.0f} s, crédits {cout}")


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    c = sp.add_parser("chercher")
    c.add_argument("--genre", default="male")
    c.add_argument("--ages", default="middle_aged,old")
    c.add_argument("--min-clones", type=int, default=3000)
    c.add_argument("--mots", default="")
    c.add_argument("--recherche", default="")
    u = sp.add_parser("auditionner")
    u.add_argument("--texte", required=True)
    u.add_argument("--voix", required=True)
    u.add_argument("--dossier", required=True)
    u.add_argument("--genre", default="male")
    u.add_argument("--reference", default=NARRATEUR)
    e = sp.add_parser("essais")
    e.add_argument("--dossier", required=True)
    e.add_argument("--voix", required=True)
    e.add_argument("--sortie", required=True)
    e.add_argument("--narrateur", default=NARRATEUR)
    a = ap.parse_args()
    {"chercher": chercher, "auditionner": auditionner, "essais": essais}[a.cmd](a)


if __name__ == "__main__":
    main()
