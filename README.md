# Interview Eddie Irvine — voice-over française

## Fichiers à écouter (`output/`)

| Fichier | Contenu |
|---|---|
| `interview_eddie_irvine_VF_voiceover.mp3` | **Version finale** : voix française par-dessus l'anglais, qui reste audible très bas |
| `interview_eddie_irvine_EN_remixee.mp3` | Interview anglaise seule, remixée (micro d'Eddie remonté, voix équilibrées) |
| `interview_eddie_irvine_voix_FR_seule.mp3` | Voix française seule (pour un remontage) |
| `interview_eddie_irvine_VF.srt` / `_EN.srt` | Sous-titres français (calés sur la VF) et anglais |

## Choix

- **Traduction** au plus près de l'anglais. On enlève seulement les scories (euh, répétitions, bégaiements).
  - Noms propres et marques non traduits : Michael, Ferrari, Scuderia, Jean Todt, Brawn, Ross, Rory, Silverstone, Aston Martin, Lawrence, Adrian, Eddie.
  - « Formula 1 » est rendu par « la F1 ».
  - Les pays sont à la française : Allemagne, Royaume-Uni.
  - Le texte complet est dans `data/translation_fr.json`.
- **Voix ElevenLabs** (`eleven_multilingual_v2`, débit 0,92, stabilité 0,7), sobres et posées :
  - George pour Eddie Irvine ;
  - Chris, plus grave, pour le journaliste.
- **Calage** : chaque phrase française démarre 0,15 à 0,5 s après la phrase anglaise. Une prise de parole qui déborde est légèrement accélérée (×1,10 maximum, hauteur conservée).
- **Anglais** :
  - Nivelé mot par mot : la voix d'Eddie variait de 15 dB et était 2 à 5 dB sous celle du journaliste.
  - Légère EQ de clarté, débruitage doux, compression.
  - Sous la VF, l'anglais est 18 dB plus bas ; dans les silences, 13 dB plus bas.
- **Niveau final** : −16 LUFS, crête < −1,5 dBTP.

## Contrôles

- Chaque segment français a été retranscrit (ElevenLabs Scribe) et comparé au texte : les mots sont identiques, aux homophones près.
- Le mix complet, retranscrit en français, donne 1,7 % d'écart, uniquement des homophones (Todt → « Tod », Eddie → « Eddy »).

## Refaire / modifier

La clé API est lue dans `ELEVENLABS_API_KEY` et n'est jamais écrite dans le dépôt.

```bash
python3 voiceover/segment.py data/transcript_en_scribe.json data/segments.json
voiceover/clean_en.sh <interview.mp3> data/transcript_en_scribe.json work/en_clean.wav work/en
ELEVENLABS_API_KEY=... python3 voiceover/tts.py data/translation_fr.json data/tts_fr --seed s04=7,s24=7,s43=7 --speed s36=1.06   # cache : ne régénère que ce qui change
python3 voiceover/mix.py data/segments.json data/translation_fr.json data/tts_fr work/en_clean.wav output work/mix
ELEVENLABS_API_KEY=... python3 voiceover/qa_vo.py data/translation_fr.json data/tts_fr work/qa.json
```

Les segments de voix déjà générés sont dans `data/tts_fr/`. Pour changer le niveau de l'anglais, modifiez `DUCK_DB` et `GAP_DB` dans `voiceover/mix.py` puis relancez le mix : aucun crédit ElevenLabs n'est consommé.
