"""Pose la voix française sur la piste anglaise remixée, avec l'anglais très bas en dessous.

1. décode et rogne les silences de chaque segment VF, harmonise le niveau des deux voix
2. place chaque segment (départ = début de la phrase anglaise + léger décalage, sans chevauchement)
   et accélère légèrement (rubberband, hauteur conservée) une prise de parole qui déborderait
3. duck : l'anglais descend sous la VF et ne remonte un peu que dans les vrais silences
4. mix final normalisé à -16 LUFS, crête vraie ≤ -1,5 dBTP ; export MP3 + SRT
Usage : mix.py <segments.json> <translation_fr.json> <tts_dir> <en_clean.wav> <outdir> <workdir>
              [--name interview_eddie_irvine] [--keep-from SECONDES]
--keep-from : à partir de ce temps l'original est déjà en français, il repasse à pleine voix.
"""
import json
import pathlib
import subprocess
import sys

import numpy as np

SR = 48000
GAP_SAME = 0.15          # respiration entre deux phrases d'une même voix
GAP_SWITCH = 0.35        # entre deux voix
TURN_MARGIN = 0.25       # la VF d'une prise de parole doit finir avant le départ prévu de la suivante
MAX_TEMPO = 1.10
VO_LUFS = -16.0
DUCK_DB = -17.0          # anglais sous la VF
GAP_DB = -9.0            # anglais dans les silences de la VF (reste bas)
BRIDGE = 1.0             # silence de VF plus court que ça : l'anglais reste baissé
PRE = 0.25               # l'anglais commence à descendre 0,25 s avant la VF
ATTACK, RELEASE = 0.25, 0.6


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, **kw)


def decode(path, tempo=None):
    af = ["-af", f"rubberband=tempo={tempo:.4f}:pitchq=quality"] if tempo and abs(tempo - 1) > 1e-3 else []
    raw = run(["ffmpeg", "-v", "error", "-i", str(path), *af, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def trim(x, thresh_db=-42, pad=0.03):
    hop = 240
    n = len(x) // hop
    db = 10 * np.log10((x[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    on = np.where(db > db.max() + thresh_db)[0]
    a = max(0, on[0] * hop - int(pad * SR))
    b = min(len(x), (on[-1] + 1) * hop + int(pad * SR))
    y = x[a:b].copy()
    f = int(0.008 * SR)
    y[:f] *= np.linspace(0, 1, f)
    y[-f:] *= np.linspace(1, 0, f)
    return y


def lufs(x):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-af", "ebur128", "-f", "null", "-"], input=x.astype(np.float32).tobytes(), capture_output=True)
    line = [l for l in p.stderr.decode().splitlines() if l.strip().startswith("I:")][-1]
    return float(line.split()[1])


def place(items, segs_by_id):
    """items: liste ordonnée de dicts {id, turn, speaker, want, dur}. Renvoie les positions de départ."""
    pos, prev_end, prev_spk = {}, -1.0, None
    for it in items:
        gap = GAP_SAME if it["speaker"] == prev_spk else GAP_SWITCH
        start = max(it["want"], prev_end + gap)
        pos[it["id"]] = start
        prev_end, prev_spk = start + it["dur"], it["speaker"]
    return pos


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main(seg_path, tr_path, tts_dir, en_path, outdir, workdir, name="interview_eddie_irvine", keep_from=None):
    tr = {s["id"]: s for s in json.load(open(tr_path))}
    # un segment sans texte français = interjection laissée en anglais
    segs = [s for s in json.load(open(seg_path)) if tr[s["id"]]["fr_tts"].strip()]
    out = pathlib.Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    wd = pathlib.Path(workdir)
    wd.mkdir(parents=True, exist_ok=True)

    raw = {s["id"]: trim(decode(pathlib.Path(tts_dir) / f"{s['id']}.mp3")) for s in segs}
    # niveau homogène par voix
    voice_gain = {}
    for spk in {s["speaker"] for s in segs}:
        cat = np.concatenate([raw[s["id"]] for s in segs if s["speaker"] == spk])
        voice_gain[spk] = 10 ** ((VO_LUFS - lufs(cat)) / 20)
    tempo = {s["id"]: 1.0 for s in segs}
    audio = {k: v * voice_gain[next(s["speaker"] for s in segs if s["id"] == k)] for k, v in raw.items()}

    turns = sorted({s["turn"] for s in segs})
    first_want = {t: next(s["vo_start"] for s in segs if s["turn"] == t) for t in turns}
    base_dur = {k: len(v) / SR for k, v in audio.items()}

    def simulate(r_by_turn):
        items = [{"id": s["id"], "turn": s["turn"], "speaker": s["speaker"], "want": s["vo_start"],
                  "dur": base_dur[s["id"]] / r_by_turn.get(s["turn"], 1.0)} for s in segs]
        return place(items, None), {it["id"]: it["dur"] for it in items}

    # tempo minimal par prise de parole pour finir avant le départ prévu de la suivante (recherche dichotomique)
    r_turn = {}
    for k, t in enumerate(turns[:-1]):
        ids = [s["id"] for s in segs if s["turn"] == t]
        limit = first_want[turns[k + 1]] - TURN_MARGIN
        if all(x["window"] < 1.0 for x in segs if x["turn"] == t):
            continue    # politesses finales très courtes : on les laisse déborder plutôt que de les accélérer

        def end_at(r):
            p, d = simulate({**r_turn, t: r})
            return p[ids[-1]] + d[ids[-1]]
        if end_at(1.0) <= limit:
            continue
        lo, hi = 1.0, MAX_TEMPO
        if end_at(hi) > limit:
            r_turn[t] = hi
            continue
        for _ in range(20):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if end_at(mid) > limit else (lo, mid)
        r_turn[t] = round(hi + 0.003, 3)
    for s in segs:
        r = r_turn.get(s["turn"], 1.0)
        tempo[s["id"]] = r
        if r != 1.0:
            audio[s["id"]] = trim(decode(pathlib.Path(tts_dir) / f"{s['id']}.mp3", r)) * voice_gain[s["speaker"]]
    items = [{"id": s["id"], "turn": s["turn"], "speaker": s["speaker"], "want": s["vo_start"],
              "dur": len(audio[s["id"]]) / SR} for s in segs]
    pos = place(items, None)

    total = max(segs[-1]["end"] + 1.0, max(pos[s["id"]] + len(audio[s["id"]]) / SR for s in segs) + 0.8)
    n = int(total * SR)
    vo = np.zeros(n, dtype=np.float32)
    report = []
    for s in segs:
        a = int(pos[s["id"]] * SR)
        vo[a:a + len(audio[s["id"]])] += audio[s["id"]]
        report.append({"id": s["id"], "speaker": s["speaker"], "en_start": s["start"], "en_end": s["end"],
                       "vo_start": round(pos[s["id"]], 2), "vo_end": round(pos[s["id"]] + len(audio[s["id"]]) / SR, 2),
                       "decalage_s": round(pos[s["id"]] - s["start"], 2), "tempo": round(tempo[s["id"]], 3),
                       "fr": tr[s["id"]]["fr"], "en": s["en"]})

    # enveloppe de ducking de l'anglais
    spans = sorted((r["vo_start"], r["vo_end"]) for r in report)
    merged = [list(spans[0])]
    for a, b in spans[1:]:
        if a - merged[-1][1] < BRIDGE:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    t = np.arange(n) / SR
    kt, kg = [0.0], [GAP_DB]
    for a, b in merged:
        kt += [max(0.0, a - PRE - ATTACK), max(0.0, a - PRE), b, b + RELEASE]
        kg += [GAP_DB, DUCK_DB, DUCK_DB, GAP_DB]
    kt.append(total)
    kg.append(GAP_DB)
    order = np.argsort(kt, kind="stable")
    duck_db = np.interp(t, np.array(kt)[order], np.array(kg)[order])
    if keep_from is not None:
        duck_db = np.where(t >= keep_from, 0.0, duck_db)
        duck_db = np.where((t > keep_from - 0.5) & (t < keep_from),
                           np.interp(t, [keep_from - 0.5, keep_from], [GAP_DB, 0.0]), duck_db)

    en = decode(en_path)
    en = np.pad(en, (0, max(0, n - len(en))))[:n]
    en_ducked = en * 10 ** (duck_db / 20)
    mix = vo + en_ducked

    def write_wav(path, x):
        run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
             "-c:a", "pcm_f32le", str(path)], input=x.astype(np.float32).tobytes())

    write_wav(wd / "mix_raw.wav", mix)
    write_wav(wd / "vo_only.wav", vo)
    I = lufs(mix)
    g = -16.0 - I
    final = wd / "mix_final.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(wd / "mix_raw.wav"), "-af",
         f"volume={g:.2f}dB,alimiter=limit=0.79:attack=3:release=60:level=disabled,aresample=48000",
         "-ac", "2", "-c:a", "pcm_s24le", str(final)])
    # correction mesurée sur le fichier stéréo final (l'upmix mono -> stéréo décale légèrement la mesure)
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(final), "-af", "ebur128", "-f", "null", "-"], capture_output=True)
    corr = -16.0 - float([l for l in p.stderr.decode().splitlines() if l.strip().startswith("I:")][-1].split()[1])
    fixed = wd / "mix_final_16lufs.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(final), "-af",
         f"volume={corr:.2f}dB,alimiter=limit=0.79:attack=3:release=60:level=disabled", "-c:a", "pcm_s24le", str(fixed)])
    final = fixed
    run(["ffmpeg", "-v", "error", "-y", "-i", str(final), "-c:a", "libmp3lame", "-b:a", "256k",
         "-metadata", f"title={name} — voice-over VF", str(out / f"{name}_VF_voiceover.mp3")])
    run(["ffmpeg", "-v", "error", "-y", "-i", str(wd / "vo_only.wav"), "-af",
         f"volume={g:.2f}dB,alimiter=limit=0.79:level=disabled", "-c:a", "libmp3lame", "-b:a", "192k",
         str(out / f"{name}_voix_FR_seule.mp3")])
    run(["ffmpeg", "-v", "error", "-y", "-i", str(en_path), "-ac", "2", "-c:a", "libmp3lame", "-b:a", "256k",
         "-metadata", f"title={name} — anglais remixé", str(out / f"{name}_EN_remixee.mp3")])

    with open(out / f"{name}_VF.srt", "w") as f:
        for k, r in enumerate(report, 1):
            f.write(f"{k}\n{srt_time(r['vo_start'])} --> {srt_time(r['vo_end'])}\n{r['fr']}\n\n")
    with open(out / f"{name}_EN.srt", "w") as f:
        for k, r in enumerate(report, 1):
            f.write(f"{k}\n{srt_time(r['en_start'])} --> {srt_time(r['en_end'])}\n{r['en']}\n\n")
    json.dump(report, open(wd / "placement.json", "w"), ensure_ascii=False, indent=1)

    for r in report:
        flag = "  <-- retard" if r["decalage_s"] > 3 else ""
        print(f'{r["id"]} {r["speaker"][:5]} EN {r["en_start"]:6.2f}-{r["en_end"]:6.2f}  VF {r["vo_start"]:6.2f}-{r["vo_end"]:6.2f}'
              f'  décalage {r["decalage_s"]:+5.2f}s tempo {r["tempo"]:.3f}{flag}')
    print(f"durée finale {total:.2f}s, loudness mix avant normalisation {I:.1f} LUFS")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    for a in ("segments", "translation", "tts_dir", "en_clean", "outdir", "workdir"):
        ap.add_argument(a)
    ap.add_argument("--name", default="interview_eddie_irvine")
    ap.add_argument("--keep-from", type=float, default=None)
    a = ap.parse_args()
    main(a.segments, a.translation, a.tts_dir, a.en_clean, a.outdir, a.workdir, a.name, a.keep_from)
