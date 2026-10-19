"""Découpe la transcription Scribe (mots horodatés + locuteurs) en phrases pour la voice-over."""
import json
import re
import sys

LAG_TURN = 0.5      # la VF démarre 0,5 s après le début de la prise de parole anglaise
LAG_SEG = 0.15      # décalage pour les phrases suivantes d'une même prise de parole
GAP = 0.12          # respiration minimale entre deux phrases VF
CHARS_PER_SEC = 14.5
MAX_SEG = 11.0
MIN_SEG = 1.4


def turns_from_words(words):
    turns, cur = [], None
    for w in words:
        if w["type"] != "word":
            continue
        if cur is None or w["speaker_id"] != cur["speaker"]:
            cur = {"speaker": w["speaker_id"], "words": []}
            turns.append(cur)
        cur["words"].append(w)
    return turns


def split_turn(words):
    segs, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        pause = (nxt["start"] - w["end"]) if nxt else 0
        if nxt is None or re.search(r"[.?!]$", w["text"]) or pause > 0.9:
            segs.append(cur)
            cur = []
    # coupe les phrases trop longues sur une virgule proche du milieu
    out = []
    for s in segs:
        stack = [s]
        while stack:
            s = stack.pop(0)
            dur = s[-1]["end"] - s[0]["start"]
            cands = [i for i, w in enumerate(s[:-1]) if w["text"].endswith((",", "-")) and 0.3 < (w["end"] - s[0]["start"]) / dur < 0.7]
            if dur > MAX_SEG and cands:
                mid = s[0]["start"] + dur / 2
                k = min(cands, key=lambda i: abs(s[i]["end"] - mid))
                stack[:0] = [s[: k + 1], s[k + 1:]]
            else:
                out.append(s)
    # fusionne les fragments trop courts avec la phrase précédente
    merged = []
    for s in out:
        if merged and (s[-1]["end"] - s[0]["start"]) < MIN_SEG:
            merged[-1] = merged[-1] + s
        else:
            merged.append(s)
    if len(merged) > 1 and (merged[0][-1]["end"] - merged[0][0]["start"]) < MIN_SEG:
        merged[1] = merged[0] + merged[1]
        merged.pop(0)
    return merged


def main(src, dst):
    data = json.load(open(src))
    segs = []
    for t_idx, turn in enumerate(turns_from_words(data["words"])):
        for k, ws in enumerate(split_turn(turn["words"])):
            segs.append({
                "id": f"s{len(segs) + 1:02d}",
                "turn": t_idx + 1,
                "speaker": "journaliste" if turn["speaker"] == "speaker_0" else "eddie_irvine",
                "first_in_turn": k == 0,
                "start": round(ws[0]["start"], 2),
                "end": round(ws[-1]["end"], 2),
                "en": " ".join(w["text"] for w in ws),
            })
    for i, s in enumerate(segs):
        s["vo_start"] = round(s["start"] + (LAG_TURN if s["first_in_turn"] else LAG_SEG), 2)
    for i, s in enumerate(segs):
        nxt = segs[i + 1]["vo_start"] if i + 1 < len(segs) else s["end"] + 2.0
        s["window"] = round(nxt - s["vo_start"] - GAP, 2)
        s["char_budget"] = int(s["window"] * CHARS_PER_SEC)
    json.dump(segs, open(dst, "w"), ensure_ascii=False, indent=1)
    for s in segs:
        print(f'{s["id"]} t{s["turn"]} {s["speaker"][:5]} {s["start"]:7.2f}-{s["end"]:7.2f} win={s["window"]:5.2f}s budget={s["char_budget"]:4d} | {s["en"]}')


if __name__ == "__main__":
    main(*sys.argv[1:3])
