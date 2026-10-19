#!/usr/bin/env bash
# Piste anglaise remixée : nivellement par mot (micro d'Eddie trop bas), EQ de clarté,
# débruitage léger, compression douce, puis gain linéaire vers -16 LUFS + limiteur.
# Usage : clean_en.sh <source audio> <transcript scribe json> <out wav> <workdir>
set -euo pipefail
SRC=$1; TR=$2; OUT=$3; WD=$4
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$WD"
ffmpeg -v error -y -i "$SRC" -ac 1 -ar 48000 -c:a pcm_f32le "$WD/orig_mono.wav"
python3 "$HERE/level_en.py" "$WD/orig_mono.wav" "$TR" "$WD/en_leveled.wav" "$WD/en_word_levels.json"
ffmpeg -v error -y -i "$WD/en_leveled.wav" -af "highpass=f=70:poles=2,equalizer=f=300:t=q:w=1.0:g=-2,equalizer=f=3500:t=q:w=1.2:g=3,afftdn=nr=10:nf=-58:tn=1,acompressor=threshold=-22dB:ratio=2.5:attack=8:release=150:knee=4:makeup=1" -c:a pcm_f32le "$WD/en_chain.wav"
I=$(ffmpeg -hide_banner -i "$WD/en_chain.wav" -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
G=$(python3 -c "print(round(-16.0 - ($I), 2))")
ffmpeg -v error -y -i "$WD/en_chain.wav" -af "volume=${G}dB,alimiter=limit=0.79:attack=3:release=60:level=disabled,aresample=48000" -c:a pcm_s24le "$OUT"
ffmpeg -hide_banner -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|LRA|Peak):" | tail -3
