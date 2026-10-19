"""Retire la bouffée parasite qu'eleven_v4 laisse parfois tout à la fin d'un segment
(la phrase finit proprement, puis ~40 ms+ de silence, puis le début d'une syllabe ou un clic).
Usage : coupe_queue.py fichier.mp3 [...]   (une copie .avant_coupe.mp3 est conservée)
"""
import shutil
import subprocess
import sys

import numpy as np

SR = 44100


def main(paths):
    for p in paths:
        x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                         capture_output=True, check=True).stdout, dtype=np.float32).copy()
        hop = int(0.005 * SR)
        n = len(x) // hop
        db = 10 * np.log10((x[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
        db -= db.max()
        quiet = db < -33
        i, run = n - 1, 0
        while i > 0 and n - i < 60:          # on ne cherche que dans les 300 dernières ms
            run = run + 1 if quiet[i] else 0
            if run >= 8:
                break
            i -= 1
        if run < 8 or i + run >= n - 1:
            print(f"{p} : pas de bouffée parasite détectée, inchangé")
            continue
        cut = (i + run) * hop - int(0.03 * SR)
        shutil.copy(p, p.replace(".mp3", ".avant_coupe.mp3"))
        y = x[:cut].copy()
        f = int(0.01 * SR)
        y[-f:] *= np.linspace(1, 0, f)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-c:a", "libmp3lame", "-b:a", "192k", p], input=y.tobytes(), check=True)
        print(f"{p} : coupé à {cut / SR:.3f}s, {(len(x) - cut) / SR * 1000:.0f} ms retirés")


if __name__ == "__main__":
    main(sys.argv[1:])
