# Reprise du livre audio « Diamant et Porcelaine »

Ce fichier permet à une nouvelle session de continuer les enregistrements **exactement comme les chapitres 1 à 3**.
Le dépôt est **public** : on n'y met jamais le texte du roman, l'audio, ni la clé ElevenLabs.
Le texte et les prises restent dans l'espace de travail de la session (et dans l'archive privée envoyée à l'autrice/l'auteur).

## État au moment de la reprise

| Chapitre | Titre | Version livrée | Durée |
|---|---|---|---|
| 1 | Chapitre premier — La Trop-Vue | v5 (heaume dosé, réglage 2) | 8 min 00 |
| 2 | Chapitre deuxième — Le Fêlé | v3 (Porcelaine = Martin, clics retirés) | 9 min 20 |
| 3 | Chapitre troisième — Le Masque posé | v1 | 9 min 20 |

La personne a validé : narrateur Paul K, Diamant Isabelle + heaume réglage 2, Porcelaine Martin (« c'est très bien »).

## Ce que la personne exige (à respecter sans redemander)

1. **Le texte est lu mot pour mot** : aucune correction, coupe ou ajout. Seul le tiret de dialogue « — » en tête de réplique est retiré.
2. **Voix françaises natives, sans aucun accent.** Ne prendre que des voix de la bibliothèque ElevenLabs dont
   `verified_languages` ne contient **que** le français (`fr`, locale `fr-FR`), de préférence très utilisées
   (`cloned_by_count` élevé). Ne pas se fier au champ « accent : parisian » : la voix « Alexandre » (créée par Alejandro Durán,
   vérifiée en 24 langues) avait un accent et a été rejetée. La retranscription ne détecte pas les accents.
3. **Modèle `eleven_v4`**, `language_code: fr`, le plus performant.
4. **Le heaume de Diamant est un effet ajouté en post-production** (fonction `casque()` de `livre_audio.py`), jamais par ElevenLabs.
   Dosage validé : **réglage 2** = valeurs par défaut de `casque()` (`wet_db=-7`, `rt60=0.36`, `er=0.7`, clarté C50 ≈ +14,7 dB).
   - Réglage trop fort, refusé : `wet_db=0, rt60=0.42, er=1.0` (C50 +8,4 dB), « tu pètes les plombs ».
   - Réglage trop faible, refusé : `wet_db=-13, rt60=0.3, er=0.35` (C50 +21,9 dB), « quasiment enlevé l'effet ».
   - Quand Diamant **retire son masque**, ses répliques sont **sans effet** (`"fx": ""`, voir chapitre 3, nuit avec Songe).
5. **Livraison de chaque chapitre** : un aperçu MP3 96 kbps mono (pour écouter dans le chat) + un ZIP
   (MP3 stéréo 192 kbps 44,1 kHz + fiche des voix avec le minutage de chaque réplique).
   Sur demande ou en cas de changement de voix, un fichier d'essais de voix (3 voix maximum, annoncées par le narrateur).
6. Répondre en français, simplement ; donner les crédits consommés.

## Distribution des voix (fichier `voix_diamant_et_porcelaine.json`)

| Rôle (speaker) | Voix ElevenLabs | voice_id | stability | pan | effet |
|---|---|---|---|---|---|
| narrateur | Paul K — Deep French Narrator | `5l4ttmr4SKNgi0HnOelT` | 0.65 | 0 | — |
| diamant | Isabelle — Mature Narrative Voice | `8h85Kr2hDfqe0CKeh7Bq` | 0.6 | 0 | casque (heaume) |
| porcelaine | Martin — Calm, Deep and Conversational | `b0Ev8lcOOXx2o9ZcF46H` | 0.6 | 0 | — |
| vieille (ch. 1) | Grandma Clo | `EMuO6fFLrXKOryHzij6K` | 0.55 | -0.12 | — |
| villageois (ch. 1) | HenryD | `59dhv4BKONM60oDSKECM` | 0.55 | +0.3 | — |
| villageoise (ch. 1) | Valy | `JgQlYGzpXIS8wtMbmdFv` | 0.55 | -0.3 | — |

`similarity_boost` 0.8 pour toutes. Pour un chapitre, copier ce fichier en `voix.json` et ne garder que les rôles présents
(ajouter un rôle si un nouveau personnage parle).

Voix essayées et **refusées** par la personne (ne pas les reproposer) :
Alexandre (accent), Garçonne (Diamant, « pas fan »), Kevan (Porcelaine, « trop adolescent »),
Régis/Régjs, Éric, Mathieu (Serious and calm), Timothée (« horribles »).
Autres voix saines déjà auditionnées pour un homme mûr : Guillaume `tVu7uvtKsrCoOPPIUVR7`, Nicolas `aQROLel5sQbj1vuIVi6B`.
Pour Diamant : Lawrence `EIdfNdxb4fnsE39tEAB1`, Charlène `iEWE65QDYbLsZumEBvcx`, Mess `3KUqqj6ZlrH5jkEAwiMb`, Stéphyra `QMNPncWXVcTVhJ9rDEQO`.

### Nouveau personnage : méthode de casting

1. Chercher dans la bibliothèque (`GET /v1/shared-voices?language=fr&gender=…&age=…&page_size=100&page=N`),
   garder les voix vérifiées **uniquement** en français, très utilisées, catégorie professionnelle.
2. Auditionner 6 à 12 voix sur une vraie réplique du personnage (eleven_v4, stability 0.6), mesurer :
   hauteur F0 (parselmouth), variation de hauteur (jeu retenu), bruit de fond (5ᵉ centile, viser < -65 dB),
   ressemblance au narrateur (Resemblyzer, viser ≤ 0.70) et retranscription exacte.
   Un homme mûr : F0 ≈ 100-120 Hz ; au-dessus de 140 Hz, la voix sonne jeune (« adolescent »).
3. Produire le chapitre avec la meilleure, et joindre un court fichier d'essais avec 2 alternatives solides.

## Jeu, pauses et conventions de lecture

- Tags de jeu testés (non prononcés) : `[whispers]` (chuchoté), `[tired]` (las), `[hesitant]`, `[calm]` (posé). Avec parcimonie,
  seulement quand le texte le justifie (« murmura-t-elle », « soupira-t-elle », « plus bas », « sa voix ne monta pas d'un ton »).
- Les **incises** (« dit-elle », « répéta-t-il, lentement… ») sont lues par le narrateur, en blocs séparés.
- Les chuchotements sont posés 6 dB sous la parole ; une courte réplique ne dépasse pas le récit de plus de 1,5 dB.
- Pauses : 0,15-0,35 s réplique/incise ; 0,5-0,8 s échange rapide ; 0,8-1,1 s entre paragraphes ; 1,3-1,8 s après une chute
  ou un silence décrit ; 2 s après le titre.
- Titre lu « Chapitre troisième. Le Masque posé. » (point à la place du tiret long) ; un tiret long dans une phrase devient une virgule pour la voix.
- Choix déjà faits : ch. 2, « Rien n'en demeure. » (ligne sans tiret) est lu par Porcelaine ; ch. 1, la foule chuchote
  (villageoise, villageois, la vieille en alternance) ; Songe (le nauroch) ne parle jamais.
- Prononciations vérifiées : Éclisse, Aurécume (la retranscription écrit « Orécume / Auricum » : c'est correct),
  Verre-Mort (« Vermor »), Sel-Mort, Trop-Vue, nauroch (« no-rok » ; entendu « un auroch », c'est la liaison).

## Procédure pour un nouveau chapitre

Arborescence (dans l'espace de travail, **pas dans le dépôt**) : `livre/chN/manuscrit_chN.txt`, `script_chN.json`,
`voix.json`, `graines.txt`, `travail/`, `Diamant_et_Porcelaine_chN.mp3`.
La clé est lue dans la variable d'environnement `ELEVENLABS_API_KEY` (à définir dans les réglages de l'environnement).

1. **Texte** : enregistrer le chapitre tel quel dans `manuscrit_chN.txt` (un paragraphe par ligne, apostrophes ’ conservées).
2. **Découpage** par le workflow `livre_audio/decoupage_chapitre.js` (3 découpeurs, synthèse, 3 relecteurs, final, contrôle
   automatique du texte). Arguments :
   `{"book": "Diamant et Porcelaine", "chapter_label": "le chapitre 4 (« … »)", "title_tts": "Chapitre quatrième. ….",
   "speaker_ids": ["narrateur", "diamant", "porcelaine"], "speakers_doc": "…description des voix…",
   "rules": "…pièges d'attribution propres au chapitre, tags…", "manuscript": "<texte exact>"}`.
   Dans `rules`, lister les répliques sans incise dont l'attribution est délicate, et l'état du masque de Diamant.
3. **Validation** : `python3 livre_audio/preparer_script.py manuscrit_chN.txt <sortie du workflow> script_chN.json [--sans-effet P0-P1:diamant]`
   (refuse tout écart de texte ; `--sans-effet` pour les scènes où Diamant a retiré son masque).
4. **Production** : `python3 livre_audio/livre_audio.py script_chN.json voix.json travail Diamant_et_Porcelaine_chN.mp3 [--seed bNNN=7]`.
   Coût ≈ 0,42 crédit par caractère (≈ 3 500 crédits pour 8 000 caractères).
5. **Contrôle des prises** (affiché par l'outil) : les homophones sont acceptés (« dit Diamant » / « dix diamants », « lieue » / « lieu »…).
   Refaire avec une graine (`--seed bNNN=7`, puis 19, 31) en cas de vraie erreur : mot changé (« Comment il appelle-t-on »),
   prise vide ou bruitée (« musique de fond »), mot isolé mal formé. Noter les graines retenues dans `graines.txt` et les repasser
   à chaque exécution, sinon la prise est régénérée. Un chuchotement peut tromper la retranscription (« à l'écart » / « à l'égard ») :
   comparer avec un `keyterms` avant de refaire.
   Les clics parasites en fin de prise sont retirés automatiquement au montage (vérifié sur les 3 chapitres).
6. **Livraison** : `python3 livre_audio/livrer_chapitre.py livre/chN N "Diamant et Porcelaine" "Chapitre … : …" <dossier_livraison> [--note "choix de lecture"]`
   (retranscription du chapitre entier comparée au manuscrit, fiche des voix, ZIP, aperçu), puis envoyer l'aperçu et le ZIP.

## Réglages techniques de `livre_audio.py` (ne pas modifier sans raison)

- Synthèse : `eleven_v4`, `mp3_44100_192`, `previous_text` / `next_text` = blocs voisins ; une réplique coupée par une incise
  et finissant par « , ; : » est envoyée avec un point final (sinon eleven_v4 avale la fin).
- Montage : silences rognés (-45 dB), îlots parasites retirés, niveau par voix -20 LUFS, chuchotements -26 LUFS,
  stéréo (pan), queues de réverbération du heaume sur le silence suivant, 0,5 s en tête et 1,5 s en fin,
  normalisation finale -18 LUFS, limiteur 0,63 (crête vraie ≈ -3,5 dBTP), MP3 192 kbps.
