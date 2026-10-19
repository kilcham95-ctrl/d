"""Nivelle la piste anglaise (le micro d'Eddie Irvine est plus bas et très irrégulier).

Pour chaque mot (horodatage Scribe), on mesure le niveau de parole ; on lisse ces niveaux sur
~1 s à l'intérieur d'une même prise de parole (jamais à cheval sur deux locuteurs), puis on applique
le gain nécessaire pour ramener la voix vers une cible commune. Le gain est tenu pendant les pauses
pour ne pas remonter le bruit de fond. Entrée/sortie : WAV mono float 48 kHz.
"""
import json
import subprocess
import sys

import numpy as np

SR = 48000
TARGET_DBFS = -24.0     # niveau visé avant compression / loudnorm
MAX_GAIN_DB = 28.0
MIN_GAIN_DB = float(__import__("os").environ.get("LEVEL_MIN_GAIN_DB", "0"))   # < 0 : autorise aussi à baisser les passages trop forts
SIGMA = 0.9             # lissage temporel des niveaux (s)
SMOOTH = 0.12           # lissage final de la courbe de gain (s)


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def save(path, x):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_f32le", path], input=x.astype(np.float32).tobytes(), check=True)


def word_energy(x, w):
    seg = x[int(w["start"] * SR):max(int(w["end"] * SR), int(w["start"] * SR) + 480)]
    hop = 480
    n = len(seg) // hop
    if n == 0:
        return None
    e = (seg[: n * hop].reshape(n, hop) ** 2).mean(1)
    return float(np.sort(e)[n // 2:].mean())   # moitié la plus énergique = voyelles


def main(src, transcript, dst, report):
    x = load(src)
    words = [w for w in json.load(open(transcript))["words"] if w["type"] == "word"]
    turns, cur = [], None
    for w in words:
        e = word_energy(x, w)
        if e is None:
            continue
        item = {"t": (w["start"] + w["end"]) / 2, "start": w["start"], "end": w["end"], "e": e,
                "dur": w["end"] - w["start"], "speaker": w["speaker_id"]}
        if cur is None or cur[-1]["speaker"] != item["speaker"]:
            cur = []
            turns.append(cur)
        cur.append(item)
    knots_t, knots_g, rows = [], [], []
    for turn in turns:
        t = np.array([w["t"] for w in turn])
        e = np.array([w["e"] for w in turn])
        d = np.array([max(w["dur"], 0.05) for w in turn])
        for i, w in enumerate(turn):
            k = np.exp(-0.5 * ((t - t[i]) / SIGMA) ** 2) * d
            lvl = 10 * np.log10((k * e).sum() / k.sum() + 1e-12)
            g = float(np.clip(TARGET_DBFS - lvl, MIN_GAIN_DB, MAX_GAIN_DB))
            knots_t += [w["start"], w["end"]]
            knots_g += [g, g]
            rows.append({"t": round(w["t"], 2), "speaker": w["speaker"], "level_dbfs": round(lvl, 1), "gain_db": round(g, 1)})
    knots_t = [0.0] + knots_t + [len(x) / SR]
    knots_g = [knots_g[0]] + knots_g + [knots_g[-1]]
    order = np.argsort(knots_t, kind="stable")
    g_db = np.interp(np.arange(len(x)) / SR, np.array(knots_t)[order], np.array(knots_g)[order])
    n = int(SMOOTH * SR)
    g_db = np.convolve(np.pad(g_db, (n, n), mode="edge"), np.ones(2 * n + 1) / (2 * n + 1), mode="same")[n:-n]
    save(dst, x * 10 ** (g_db / 20))
    json.dump(rows, open(report, "w"), indent=0)
    for sp in ("speaker_0", "speaker_1"):
        g = np.array([r["gain_db"] for r in rows if r["speaker"] == sp])
        l = np.array([r["level_dbfs"] for r in rows if r["speaker"] == sp])
        print(f"{sp}: niveau lissé {l.min():.1f}..{l.max():.1f} dBFS (médiane {np.median(l):.1f}), gain {g.min():.1f}..{g.max():.1f} dB")


if __name__ == "__main__":
    main(*sys.argv[1:5])
