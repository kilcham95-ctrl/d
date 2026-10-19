"""Découpe une émission bilingue : les phrases anglaises deviennent des segments à doubler,
les phrases françaises deviennent des zones à laisser intactes (original à pleine voix).

Langue d'une phrase : mots-outils français/anglais, accents, et l'hésitation transcrite
(Scribe écrit « euh » en français, « uh/um » en anglais). Les phrases indécidables (« Yeah »,
un nom propre seul) prennent la langue de leurs voisines.
Usage : segment_mixte.py <transcript.json> <segments.json> <zones_fr.json> --speakers speaker_0=journaliste,speaker_1=giorgio,...
"""
import argparse
import json
import re

from segment import split_turn, LAG_TURN, LAG_SEG, GAP, CHARS_PER_SEC

# mots-outils propres à chaque langue (les mots communs aux deux, comme « car », « on », « a », sont exclus)
FR = set("le la les un une des du de et est que qui pour pas ne je tu il elle nous vous ils ce cette ces avec dans sur "
         "au aux mais ou donc très c'est j'ai qu'il d'un d'une y en son sa ses mon ma mes notre votre leur était être "
         "avoir fait bien aussi comme plus tout tous voilà alors parce puisque oui non merci vrai va vais passer anglais "
         "français bonjour salut chez".split())
EN = set("the an and is are was were that which who for not i you he she we they it this these with in at but or so "
         "because very have has had be been do did my your our their what when where how there here of to from just like "
         "really yeah okay".split())


def lang_of(text):
    t = text.lower()
    words = re.findall(r"[a-zàâçéèêëîïôûùüÿœ']+", t)
    f = sum(w in FR for w in words) + 2 * len(re.findall(r"[àâçéèêëîïôûùœ]", t)) + words.count("euh")
    e = sum(w in EN for w in words) + (words.count("uh") + words.count("um"))
    if f + e < 2:
        return "fr" if f else None          # « chez Ferrari. » : un seul indice, mais français
    return "fr" if f > e else "en"


def sentences(words):
    out, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        if (nxt is None or nxt["speaker_id"] != w["speaker_id"] or nxt["start"] - w["end"] > 0.7
                or re.search(r"[.?!]$", w["text"])):
            out.append(cur)
            cur = []
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript")
    ap.add_argument("segments")
    ap.add_argument("zones")
    ap.add_argument("--speakers", required=True)
    ap.add_argument("--lag-turn", type=float, default=0.8)
    ap.add_argument("--lag-seg", type=float, default=0.4)
    ap.add_argument("--host", default="speaker_0", help="présentateur (seul à parler français hors salutations)")
    ap.add_argument("--keep-en", default="", help="plages t0-t1 de phrases anglaises à laisser en VO, ex. 754.5-757.3")
    a = ap.parse_args()
    names = dict(kv.split("=") for kv in a.speakers.split(","))
    words = [w for w in json.load(open(a.transcript))["words"] if w["type"] == "word"]
    sents = [{"words": s, "speaker": s[0]["speaker_id"], "start": s[0]["start"], "end": s[-1]["end"],
              "text": " ".join(w["text"] for w in s)} for s in sentences(words)]
    for s in sents:
        s["lang"] = lang_of(s["text"])
    # phrases indécidables : langue de la voisine la plus proche (même intervenant d'abord)
    for i, s in enumerate(sents):
        if s["lang"]:
            continue
        if s["speaker"] != a.host:          # un invité sans indice parle anglais
            s["lang"] = "en"
            continue
        cands = [(max(o["start"] - s["end"], s["start"] - o["end"]), o["lang"]) for o in sents[max(0, i - 3):i + 4]
                 if o["lang"] and o["speaker"] == a.host and max(o["start"] - s["end"], s["start"] - o["end"]) < 3]
        s["lang"] = min(cands)[1] if cands else "en"
    # courte réplique anglaise (« Yeah, yeah ») au milieu d'un passage français : elle en fait partie
    for i in range(1, len(sents) - 1):
        p, s, n = sents[i - 1], sents[i], sents[i + 1]
        if (s["lang"] == "en" and len(s["words"]) <= 3 and p["lang"] == n["lang"] == "fr"
                and s["start"] - p["end"] < 2 and n["start"] - s["end"] < 2):
            s["lang"] = "fr"
    keep = [tuple(map(float, r.split("-"))) for r in a.keep_en.split(",") if r]
    for s in sents:                          # anglais laissé en VO : traité comme une zone intouchable
        if any(k0 - 0.05 <= s["start"] and s["end"] <= k1 + 0.05 for k0, k1 in keep):
            s["lang"] = "fr"
    zones = []
    for s in sents:
        if s["lang"] == "fr":
            if zones and s["start"] - zones[-1][1] < 1.0:
                zones[-1][1] = s["end"]
            else:
                zones.append([s["start"], s["end"]])
    # prises de parole anglaises : même intervenant, sans passage français entre deux phrases
    turns, cur = [], None
    for s in sents:
        if s["lang"] != "en":
            cur = None
            continue
        if cur is None or cur["speaker"] != s["speaker"]:
            cur = {"speaker": s["speaker"], "words": []}
            turns.append(cur)
        cur["words"] += s["words"]
    segs = []
    for t_idx, turn in enumerate(turns):
        for k, ws in enumerate(split_turn(turn["words"])):
            segs.append({"id": f"s{len(segs) + 1:03d}", "turn": t_idx + 1,
                         "speaker": names.get(turn["speaker"], turn["speaker"]), "first_in_turn": k == 0,
                         "start": round(ws[0]["start"], 2), "end": round(ws[-1]["end"], 2),
                         "en": " ".join(w["text"] for w in ws)})
    for s in segs:
        s["vo_start"] = round(s["start"] + (a.lag_turn if s["first_in_turn"] else a.lag_seg), 2)
    for i, s in enumerate(segs):
        nxt = segs[i + 1]["vo_start"] if i + 1 < len(segs) else s["end"] + 2.0
        fr_next = min([z[0] for z in zones if z[0] >= s["start"]] or [1e9])
        s["window"] = round(min(nxt, fr_next - 0.3) - s["vo_start"] - GAP, 2)
        s["char_budget"] = max(0, int(s["window"] * CHARS_PER_SEC))
    json.dump(segs, open(a.segments, "w"), ensure_ascii=False, indent=1)
    json.dump([[round(z0, 2), round(z1, 2)] for z0, z1 in zones], open(a.zones, "w"))
    for s in sents:
        print(f'{"FR " if s["lang"] == "fr" else "   "}[{s["start"]:6.1f}] {names.get(s["speaker"], s["speaker"])[:5]} {s["lang"]}: {s["text"][:110]}')
    print(f"{len(segs)} segments anglais, {len(zones)} zones françaises, {sum(z1 - z0 for z0, z1 in zones):.0f} s de français")


if __name__ == "__main__":
    main()
