#!/usr/bin/env bash
# Fin de chaîne d'une interview : voix eleven_v4 (Guillaume / Louis), contrôle par retranscription,
# détection des fins coupées, mixage (français toujours après l'anglais), contrôle du mix complet.
# Usage : fin_de_chaine.sh <data/dossier> <output/dossier> <nom> <en_clean.wav> <workdir> [graines ex. s03=7,s45=11]
set -euo pipefail
D=$1; OUT=$2; NAME=$3; EN=$4; WD=$5; SEEDS=${6:-}
HERE=$(cd "$(dirname "$0")" && pwd)
: "${ELEVENLABS_API_KEY:?ELEVENLABS_API_KEY manquante}"
mkdir -p "$WD"
python3 "$HERE/tts.py" "$D/translation_fr.json" "$D/tts_fr" --model eleven_v4 --format mp3_44100_192 --tag "[calm]" \
  --voice-invite Qrl71rx6Yg8RvyPYRGCQ --voice-journaliste jGGIwkfv43kUFffPXEEO ${SEEDS:+--seed $SEEDS} \
  ${VOICE_MAP:+--voice-map $VOICE_MAP} | tail -1
python3 "$HERE/qa_vo.py" "$D/translation_fr.json" "$D/tts_fr" "$WD/qa.json" --concat > /dev/null
python3 - "$D" "$WD" "$HERE" <<'PY'
import json, statistics, sys, glob, numpy as np
d, wd, here = sys.argv[1:4]
sys.path.insert(0, here); import mix
r = json.load(open(f'{wd}/qa.json'))
print(f"QA segments : {len(r)}, écart moyen {statistics.mean(x['wer'] for x in r):.3f}, parfaits {sum(1 for x in r if x['wer']==0)}")
for x in r:
    if x['wer'] > 0.08 or x['noms_absents']:
        print(f"  {x['id']} WER {x['wer']} {x['noms_absents']} | attendu : {x['attendu']} | entendu : {x['entendu']}")
ab = []
for f in sorted(glob.glob(f'{d}/tts_fr/*.mp3')):
    x = mix.decode(f); hop = 240; n = len(x) // hop
    db = 10 * np.log10((x[:n*hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    loud = np.where(db > db.max() - 20)[0]
    if (n - 1 - loud[-1]) * 5 < 60: ab.append(f.split('/')[-1][:-4])
print('fins coupées :', ' '.join(ab) if ab else 'aucune')
PY
ZARG=""; [ -f "$D/zones_fr.json" ] && ZARG="--zones-fr $D/zones_fr.json"
python3 "$HERE/mix.py" "$D/segments.json" "$D/translation_fr.json" "$D/tts_fr" "$EN" "$OUT" "$WD/mix" --name "$NAME" --pre -0.25 $ZARG > "$WD/mix_log.txt"
cp "$WD/mix/placement.json" "$D/placement.json"
python3 - "$WD" <<'PY'
import json, sys
pl = json.load(open(f'{sys.argv[1]}/mix/placement.json'))
print('VF avant l\'anglais :', [r['id'] for r in pl if r['vo_start'] - r['en_start'] < 0.39] or 'aucune',
      '| retard max %.2f s' % max(r['decalage_s'] for r in pl),
      '| chevauchements :', [(a['id'], b['id']) for a, b in zip(pl, pl[1:]) if b['vo_start'] < a['vo_end'] - 1e-3] or 'aucun')
PY
ffmpeg -hide_banner -i "$OUT/${NAME}_VF_voiceover.mp3" -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):" | tail -2 | tr -s ' ' | tr '\n' ' '; echo
ffmpeg -hide_banner -loglevel error -y -i "$OUT/${NAME}_VF_voiceover.mp3" -ac 1 -c:a libmp3lame -b:a 96k "$WD/final_96k.mp3"
curl -sS --max-time 900 -X POST https://api.elevenlabs.io/v1/speech-to-text -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -F model_id=scribe_v2 -F language_code=fr -F file=@"$WD/final_96k.mp3" -o "$WD/stt_final.json"
python3 - "$D" "$WD" "$HERE" <<'PY'
import json, sys, difflib
d, wd, here = sys.argv[1:4]; sys.path.insert(0, here); import qa_vo
import os
st = json.load(open(f'{wd}/stt_final.json')); t = {s['id']: s for s in json.load(open(f'{d}/translation_fr.json'))}
items = [(r['vo_start'], t[r['id']]['fr_tts']) for r in json.load(open(f'{wd}/mix/placement.json'))]
if os.path.exists(f'{d}/zones_fr.json'):   # le français d'origine fait partie de ce qu'on doit entendre
    zones = json.load(open(f'{d}/zones_fr.json'))
    tr = json.load(open(f'{d}/transcript_scribe.json'))
    items += [(w['start'], w['text']) for w in tr['words'] if w['type'] == 'word'
              and any(z0 - 0.05 <= w['start'] <= z1 + 0.05 for z0, z1 in zones)]
ref = qa_vo.norm(' '.join(x for _, x in sorted(items))); hyp = qa_vo.norm(st['text'])
sm = difflib.SequenceMatcher(a=ref, b=hyp, autojunk=False)
print(f"mix complet : {st['language_code']} {st['language_probability']:.2f}, écart {qa_vo.wer(ref, hyp):.3f} |",
      ' ; '.join(f"{' '.join(ref[a1:a2])} -> {' '.join(hyp[b1:b2])}" for op, a1, a2, b1, b2 in sm.get_opcodes() if op != 'equal'))
PY
