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

---

# Interview Mika Salo — voice-over française

Les fichiers sont dans `output/mika_salo/` et suivent la même structure que pour Eddie Irvine.

## Rendu final

- **Modèle et voix** : `eleven_v3`, le modèle ElevenLabs le plus récent, en stabilité « robuste » (la plus sobre), à 192 kb/s. Voix : George pour Mika Salo, Chris pour le journaliste.
- **Pourquoi v3** : sur le test comparatif, c'est le seul modèle qui prononce correctement « Ross Brawn ou Jean Todt » avec la voix du journaliste. Une première version faite avec Turbo est remplacée.
- **Interjections** : « Yes », « Mm », « Aye yai yai », « Excuse me » et le « Bye-bye. Thank you. » final restent en anglais, sans voix off.
- **Fin du fichier** (à partir de 478,5 s) : elle est déjà en français. Ce sont les prises du présentateur qui annoncent l'interview de Luca Badoer. Elles sont gardées à pleine voix (`--keep-from 478.5`).
- **Corrections de transcription** : « John » est rendu par « Jean » (Jean Todt prononcé à la finlandaise) et « Ange Pasquale » par « Ange Pasquali ».
- **« Formula Ford »** : il est écrit « Formoula Ford » dans le texte envoyé à la synthèse, sinon la voix dit « Formule Ford ». Les sous-titres gardent « Formula Ford ».

## Contrôles

- Segments, en une seule retranscription : 84 sur 94 sont identiques ; le reste, ce sont des homophones.
- Mix complet : français détecté à 100 %, 1,2 % d'écart, uniquement des homophones et des accords.

## Commandes

```bash
python3 voiceover/segment.py data/mika_salo/transcript_en_scribe.json data/mika_salo/segments.json --journalist speaker_1 --guest mika_salo --en-until 478.5
LEVEL_MIN_GAIN_DB=-15 voiceover/clean_en.sh <itv_gphi-mika_salo.mp3> data/mika_salo/transcript_en_scribe.json work/mika_en_clean.wav work/mika_en
ELEVENLABS_API_KEY=... python3 voiceover/tts.py data/mika_salo/translation_fr.json data/mika_salo/tts_fr_v3 --model eleven_v3 --format mp3_44100_192 --seed s57=7
python3 voiceover/mix.py data/mika_salo/segments.json data/mika_salo/translation_fr.json data/mika_salo/tts_fr_v3 work/mika_en_clean.wav output/mika_salo work/mika_mix --name interview_mika_salo --keep-from 478.5
ELEVENLABS_API_KEY=... python3 voiceover/qa_vo.py data/mika_salo/translation_fr.json data/mika_salo/tts_fr_v3 work/qa.json --concat
```

---

# Interview Mika Salo — V2 (nouveau montage)

Les fichiers sont dans `output/mika_salo_v2/`.

## Rendu final

- **Modèle** : `eleven_v4`, sorti le 28 septembre 2026, le plus récent d'ElevenLabs. Stabilité 0,9, consigne de ton `[calm]` en tête de chaque phrase (elle n'est pas prononcée), contexte des phrases voisines, français forcé, 192 kb/s.
- **Voix françaises natives**, sans accent, tirées de la bibliothèque ElevenLabs. Elles ont été choisies sur un panel de 11 comédiens français, sur deux critères : retranscription exacte et intonation la plus posée.
  - **Guillaume** (« Narrator », `Qrl71rx6Yg8RvyPYRGCQ`) pour Mika Salo : voix chaude et grave, la plus régulière du panel.
  - **Léo** (accent parisien, `AfbuxQ9DVtS4azaxN1W7`) pour le journaliste : la plus mesurée sur les questions, et bien distincte de Guillaume.
  - Les voix anglophones George et Chris des versions précédentes avaient un accent en français ; elles ne sont plus utilisées ici.
- **Fins de fragments** : v4 coupe net la dernière syllabe d'un segment qui s'arrête au milieu d'une phrase. `tts.py` ajoute donc automatiquement « … » au texte envoyé à la voix, et la voix retombe naturellement.
- **Comparaison avec v3** : v4 prononce juste « Jean Todt » et « Formula Ford » sans astuce de graphie. Même avec `[calm]`, son intonation reste environ 20 % plus variée que v3 : plus naturelle, un peu moins neutre. Les segments v3 restent dans `data/mika_salo_v2/tts_fr_v3/` pour revenir en arrière.
- **Calage** : le français démarre toujours après l'anglais, 0,8 s après le début de chaque prise de parole et 0,4 s après chaque phrase suivante. L'anglais ne baisse qu'au moment où la voix française commence (`--lag-turn 0.8 --lag-seg 0.4 --pre -0.25`).
- **Traduction** : 54 segments identiques à la V1 reprennent la traduction validée ; les 30 nouveaux sont passés par le workflow (3 traducteurs, synthèse, 3 relectures adversariales).
- **Formulations ajustées pour v4**, qui avale un mot isolé en début ou en fin de segment : le « et » de s11 passe en tête de s12 ; s50 devient « On a grandi ensemble, donc… » ; s58 devient « des équipes plus petites ».
- **Échange rapide de la fin** (« Yeah, I know », « We say hello to… », « Hello, Ange ») : ces relances restent en anglais. La réplique suivante du journaliste dit « On salue Ange. Merci, Mika… ».

## Contrôles

- Mix complet (voix natives) : français à 100 %, 0,7 % d'écart, uniquement des homophones.
- Calage : aucune phrase française ne démarre avant l'anglais et aucune ne se chevauche.

## Commandes

```bash
python3 voiceover/segment.py data/mika_salo_v2/transcript_en_scribe.json data/mika_salo_v2/segments.json --journalist speaker_0 --guest mika_salo --lag-turn 0.8 --lag-seg 0.4
LEVEL_MIN_GAIN_DB=-15 voiceover/clean_en.sh <V2_ITW_Mica_Salo.mp3> data/mika_salo_v2/transcript_en_scribe.json work/v2_en_clean.wav work/v2_en
ELEVENLABS_API_KEY=... python3 voiceover/tts.py data/mika_salo_v2/translation_fr.json data/mika_salo_v2/tts_fr_v4_natif --model eleven_v4 --format mp3_44100_192 --tag "[calm]" --voice-invite Qrl71rx6Yg8RvyPYRGCQ --voice-journaliste AfbuxQ9DVtS4azaxN1W7 --seed s03=7,s45=11,s60=7,s75=7
python3 voiceover/mix.py data/mika_salo_v2/segments.json data/mika_salo_v2/translation_fr.json data/mika_salo_v2/tts_fr_v4_natif work/v2_en_clean.wav output/mika_salo_v2 work/v2_mix --name interview_mika_salo_v2 --pre -0.25
```
