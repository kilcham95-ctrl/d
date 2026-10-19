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
  - **Louis** (« French Documentary Narrator », `jGGIwkfv43kUFffPXEEO`) pour le journaliste. Il remplace Léo, jugé trop suave : c'est une voix nette et neutre de narration documentaire, choisie parmi 9 voix neutres auditionnées. Remplaçants possibles : Noah (`OSc8NW5kpGzPyeZB3Wjq`), Sébastien (`5DgHTbl1HXudcxdBp5pQ`).
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
ELEVENLABS_API_KEY=... python3 voiceover/tts.py data/mika_salo_v2/translation_fr.json data/mika_salo_v2/tts_fr_v4_louis --model eleven_v4 --format mp3_44100_192 --tag "[calm]" --voice-invite Qrl71rx6Yg8RvyPYRGCQ --voice-journaliste jGGIwkfv43kUFffPXEEO --seed s03=7,s45=11,s60=7,s75=7
python3 voiceover/mix.py data/mika_salo_v2/segments.json data/mika_salo_v2/translation_fr.json data/mika_salo_v2/tts_fr_v4_louis work/v2_en_clean.wav output/mika_salo_v2 work/v2_mix --name interview_mika_salo_v2 --pre -0.25
```

---

# Interview Eddie Irvine — nouvelle version (ITW_Eddy_Irvine_A_traduire)

Les fichiers sont dans `output/eddie_irvine_v2/`. Réglages identiques à Mika Salo V2 :

- **Voix et modèle** : `eleven_v4` avec des voix françaises natives, Guillaume pour Eddie Irvine et Louis pour le journaliste (il remplace Léo, jugé trop suave). Consigne `[calm]`, 192 kb/s.
- **Calage** : le français démarre toujours après l'anglais (0,8 s en début de prise de parole, 0,4 s ensuite). L'anglais baisse au moment où la voix française commence.
- **Traduction** : 34 segments sur 47 reprennent la traduction validée de la première version. Les 13 redécoupés sont passés par le workflow (3 traducteurs, synthèse, 3 relectures adversariales). « La F1 » est lu « la F un ». Le « Bye-bye » final reste en anglais.
- **Piste anglaise** : le micro d'Eddie (−35 à −38 LUFS) est remonté. Toutes les prises de parole sont entre −15,7 et −17 LUFS.
- **Contrôles** : 42 segments sur 46 identiques, le reste ce sont des homophones ; aucune fin de phrase coupée. Mix complet : français à 100 %, 0,7 % d'écart. Aucune phrase française avant l'anglais, aucun chevauchement.

```bash
python3 voiceover/segment.py data/eddie_irvine_v2/transcript_en_scribe.json data/eddie_irvine_v2/segments.json --journalist speaker_0 --guest eddie_irvine --lag-turn 0.8 --lag-seg 0.4
LEVEL_MIN_GAIN_DB=-15 voiceover/clean_en.sh <ITW_Eddy_Irvine_A_traduire.mp3> data/eddie_irvine_v2/transcript_en_scribe.json work/e2_en_clean.wav work/e2_en
ELEVENLABS_API_KEY=... python3 voiceover/tts.py data/eddie_irvine_v2/translation_fr.json data/eddie_irvine_v2/tts_fr_v4_louis --model eleven_v4 --format mp3_44100_192 --tag "[calm]" --voice-invite Qrl71rx6Yg8RvyPYRGCQ --voice-journaliste jGGIwkfv43kUFffPXEEO
python3 voiceover/mix.py data/eddie_irvine_v2/segments.json data/eddie_irvine_v2/translation_fr.json data/eddie_irvine_v2/tts_fr_v4_louis work/e2_en_clean.wav output/eddie_irvine_v2 work/e2_mix --name interview_eddie_irvine_v2 --pre -0.25
```

---

# Interviews Luca Badoer, Gerhard Berger, Riccardo Patrese

Les fichiers sont dans `output/luca_badoer/`, `output/gerhard_berger/` et `output/riccardo_patrese/`. Les interviews ont été traitées l'une après l'autre, avec le même procédé :

1. **Transcription** ElevenLabs Scribe v2 avec séparation des voix.
2. **Découpe** en phrases (`segment.py --lag-turn 0.8 --lag-seg 0.4`).
3. **Traduction** par workflow : 3 traducteurs (fidélité, adaptation voice-over, terminologie F1), synthèse, 3 relectures adversariales (sens, noms et prononciation, durée), puis correction finale.
4. **Piste anglaise** nivelée mot par mot (`LEVEL_MIN_GAIN_DB=-15 clean_en.sh`).
5. **Fin de chaîne** : `fin_de_chaine.sh` (eleven_v4, Guillaume pour l'invité, Louis pour le journaliste, consigne `[calm]`), contrôle par retranscription, détection des fins coupées, mix où le français arrive toujours après l'anglais, contrôle du mix complet.
6. `coupe_queue.py` retire la bouffée parasite qu'eleven_v4 laisse parfois tout à la fin d'un segment (Badoer s05, Patrese s08 et s41).

| Interview | Durée | Segments identiques au contrôle | Écart sur le mix complet | Retard max de la VF |
|---|---|---|---|---|
| Luca Badoer | 3:03 | 31/31 | 0,0 % | 1,3 s |
| Gerhard Berger | 3:52 | 36/37 | 0,0 % | 1,0 s |
| Riccardo Patrese | 3:31 | 38/39 | 0,0 % | 1,9 s (« D'accord, merci » final) |

Choix particuliers :

- **Badoer** : c'est un monologue (les questions ont été coupées au montage) ; le seul « Of course » du journaliste reste en anglais.
- **Berger** : le lapsus « Frank » (corrigé aussitôt en « Ayrton ») n'est pas traduit, et « Mr. Ferrari » devient « Monsieur Ferrari ».
- **Patrese** :
  - « he's not anymore with us, even if he's with us in the heart » est traduit littéralement : « il n'est plus avec nous, même s'il est avec nous dans nos cœurs ».
  - Les bouts de question du journaliste dans l'échange haché vers 1:00 (« He was your teammate at— … in Benetton? ») restent en anglais pour garder la synchro.
  - « Franco Coppini » est gardé tel que transcrit.
