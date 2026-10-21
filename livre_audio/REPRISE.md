# Reprise du livre audio à plusieurs voix

Ce fichier permet à une nouvelle session de continuer les enregistrements du livre audio **exactement comme les chapitres déjà faits**.

**Le dépôt est public.** On n'y met jamais :
- le texte du roman ;
- l'audio ;
- la clé ElevenLabs ;
- les détails de l'histoire.

Tout ce qui est propre au roman se trouve dans l'**archive privée** que la personne envoie dans le chat, dans le fichier `livre/NOTES_LECTURE.md`. On y trouve l'état des chapitres, les choix de lecture déjà faits, les prononciations, les graines et les consignes de découpage exactes. **Lire ce fichier en premier**, après celui-ci.

## 0. Démarrage d'une nouvelle session

1. **Outils** : dépôt `kilcham95-ctrl/d`, branche `claude/nice-johnson-v7fls3`, dossier `livre_audio/`.
2. **Clé** : la variable d'environnement `ELEVENLABS_API_KEY`, définie par la personne dans les réglages de l'environnement. Ne jamais la demander dans le chat, ne jamais l'écrire dans un fichier du dépôt.
3. **Archive privée** : la personne envoie `Diamant_et_Porcelaine_archive_travail_*.zip`.
   - La décompresser dans le dossier scratchpad de la session, **jamais dans le dépôt**. Le hook de fin de tour exige de committer et pousser tout fichier non suivi, ce qui publierait le roman. `.gitignore` exclut `livre/` par sécurité, mais l'archive doit rester hors du dépôt.
   - Dans la suite, `REPO` désigne le clone du dépôt (`/home/user/d`), `W` le dossier de travail (scratchpad) et `C=$W/livre/chN`.
4. **Prérequis** : ffmpeg avec libmp3lame et les filtres `ebur128` et `alimiter`, curl, Python 3 avec numpy et scipy. Pour le casting seulement : `pip install praat-parselmouth resemblyzer`.
   Vérification : `python3 -c "import numpy, scipy"` et `ffmpeg -hide_banner -filters | grep -E 'ebur128|alimiter'`.
5. Lancer les scripts du dépôt **sans** `python3 -I` : `livrer_chapitre.py` et `casting.py` importent `livre_audio.py`, qui est dans le même dossier.

## 1. Ce que la personne exige (à respecter sans redemander)

1. **Demande de départ** :
   - le narrateur : une voix d'homme **rauque** ;
   - Diamant : une **femme forte** ;
   - les villageois : des **voix âgées**, d'homme ou de femme selon le personnage.

   Tout villageois d'un chapitre suivant reprend les voix « vieille » ou « villageoise » (femmes) et « villageois » (homme) du tableau ci-dessous.
2. **Le texte est lu mot pour mot**, sans aucune correction, coupe ni ajout. Seul le tiret de dialogue « — » en tête de réplique est retiré.
3. **Voix françaises natives, sans aucun accent.** Ne prendre que des voix de la bibliothèque ElevenLabs :
   - dont `verified_languages` contient **uniquement** le français (`fr`, locale `fr-FR`) ;
   - très utilisées (`cloned_by_count` élevé) ;
   - de catégorie `professional` ou `high_quality`.

   Ne pas se fier au champ « accent : parisian » : une voix « parisienne » vérifiée en 24 langues avait un accent et a été refusée. La retranscription ne détecte pas les accents.
4. **Modèle `eleven_v4`**, `language_code: fr`.
5. **Le heaume de Diamant est un effet de post-production** : fonction `casque()` de `livre_audio.py`, jamais un réglage ElevenLabs.
   - Dosage validé : **réglage 2** = valeurs par défaut de `casque()`, soit `wet_db=-7`, `rt60=0.36`, `er=0.7` (clarté C50 ≈ +14,7 dB).
   - Le fichier de comparaison envoyé proposait aussi :
     - réglage 1, plus léger : `wet_db=-10, rt60=0.33, er=0.55` (C50 +18,2 dB) ;
     - réglage 3, plus présent : `wet_db=-4.5, rt60=0.38, er=0.85` (C50 +12,2 dB).

     La personne n'a pas choisi : le réglage 2 est donc validé (« sinon c'est bien »). Si elle demande 1 ou 3, changer les valeurs par défaut et remonter tous les chapitres, ce qui ne coûte aucun crédit (§5).
   - Refusé, trop fort : `wet_db=0, rt60=0.42, er=1.0` (C50 +8,4 dB, à l'époque avec un passe-bas à 9 kHz). La personne a répondu « tu pètes les plombs ».
   - Refusé, trop faible : `wet_db=-13, rt60=0.3, er=0.35` (C50 +21,9 dB). La personne a répondu « quasiment enlevé l'effet ».
   - Quand Diamant **retire son masque d'apparat** (même si la résille reste), ses répliques sont **sans aucun effet** (`"fx": ""`).
6. **Livraison de chaque chapitre** :
   - un aperçu MP3 96 kbps mono, envoyé en mode *render* (la personne écoute dans le chat ; les fichiers lourds ne se lisent pas) ;
   - un ZIP envoyé en mode *attach*. Il s'ouvre sur un dossier « Diamant et Porcelaine - Chapitre N » qui contient le MP3 stéréo 192 kbps (44,1 kHz) et la fiche des voix, avec le minutage de chaque réplique.
   - Une version corrigée porte le suffixe `_v2`, `_v3`… (option `--version`) et est annoncée comme remplaçant la précédente.
   - En cas de nouvelle voix, joindre un fichier d'essais en mode *render* : 3 voix au maximum, choisies parmi les plus solides et annoncées par le narrateur (`casting.py essais`).
7. **Message de livraison**, court et en français :
   - les voix et pourquoi ;
   - les choix de lecture à valider ;
   - le contrôle (nombre de mots ; seuls des homophones diffèrent) ;
   - le minutage de la première réplique des personnages et des scènes clés ;
   - les crédits consommés.

## 2. Distribution des voix (`voix_diamant_et_porcelaine.json`)

| Rôle (speaker) | Voix ElevenLabs | voice_id | stability | pan | effet |
|---|---|---|---|---|---|
| narrateur | Paul K — Deep French Narrator | `5l4ttmr4SKNgi0HnOelT` | 0.65 | 0 | — |
| diamant | Isabelle — Mature Narrative Voice | `8h85Kr2hDfqe0CKeh7Bq` | 0.6 | 0 | casque (heaume) |
| porcelaine | Martin — Calm, Deep and Conversational | `b0Ev8lcOOXx2o9ZcF46H` | 0.6 | 0 | — |
| vieille (villageoise principale) | Grandma Clo | `EMuO6fFLrXKOryHzij6K` | 0.55 | -0.12 | — |
| villageois (homme âgé) | HenryD | `59dhv4BKONM60oDSKECM` | 0.55 | +0.3 | — |
| villageoise (autre femme âgée) | Valy | `JgQlYGzpXIS8wtMbmdFv` | 0.55 | -0.3 | — |

- `similarity_boost` vaut 0.8 pour toutes : c'est la valeur par défaut du code, et la clé s'appelle `similarity` dans voix.json. La `stability` par défaut est 0.6.
- Pour un chapitre, copier ce fichier en `$C/voix.json` et ne garder que les rôles présents.
- Paul K, Isabelle (avec le heaume au réglage 2) et Martin sont **validés explicitement** par la personne.
- **Exception connue** : HenryD est vérifié en plusieurs langues. La personne en a été avertie et n'a rien signalé ; on le garde pour la continuité. Si elle entend un accent, le remplacer par Zion Aquila (`t2969wgUwHbBoVCZNHRU`, vérifié uniquement en français).

**Voix refusées par la personne** (ne jamais les reproposer) :

| Voix | voice_id | Motif |
|---|---|---|
| Alexandre (Calm Storyteller) | `tXDU4wD3AOfNX2o6h4Oc` | accent |
| Garçonne | `R8yx8M2U4ZwZK8trfpkc` | « pas fan » |
| Kevan | `AYfOkr1hDQYbhigmRZ16` | « trop adolescent » |
| Régjs | `jbo2bM3sjEM1VuwZTQuJ` | « horrible » |
| Eric (Calm, Low & Reflective) | `9osbeK6KzhDRV0yX4rTq` | « horrible » |
| Mathieu (Serious and calm) | `ckgFqgT4MZNQ3bggyZiF` | « horrible » |
| Timothée | `vqvgjNDXBhRGzlLsbOq5` | « horrible » |

**Alternatives déjà auditionnées** :
- Homme mûr :
  - Guillaume `tVu7uvtKsrCoOPPIUVR7`, vérifié uniquement en français ;
  - Nicolas `aQROLel5sQbj1vuIVi6B`, multilingue, mais déjà validé par la personne sur un autre projet.
- Femme forte, toutes vérifiées uniquement en français : Lawrence `EIdfNdxb4fnsE39tEAB1`, Charlène `iEWE65QDYbLsZumEBvcx`, Mess `3KUqqj6ZlrH5jkEAwiMb`, Stéphyra `QMNPncWXVcTVhJ9rDEQO`.

### Nouveau personnage

1. **Chercher** : `python3 $REPO/livre_audio/casting.py chercher --genre male|female --ages middle_aged,old --min-clones 3000`. La commande ne garde que les voix vérifiées uniquement en français.
2. **Auditionner** de 6 à 12 voix sur une vraie réplique du personnage :
   `casting.py auditionner --texte "…" --voix id1,id2,… --dossier $W/casting_X --genre male|female`.
   Repères :
   - homme mûr : F0 ≈ 100-120 Hz ; au-dessus de 140 Hz, la voix sonne jeune (« adolescent ») ;
   - variation de hauteur faible pour un jeu retenu ;
   - bruit de fond sous -65 dB ;
   - ressemblance au narrateur ≤ 0.70 ;
   - texte retranscrit exact.
3. **Produire** le chapitre avec la meilleure voix. Joindre `casting.py essais --dossier … --voix id:Nom,id:Nom,id:Nom --sortie essais.mp3` (la voix retenue en premier).
4. **Déclarer le rôle** :
   - dans `voix.json` (`voice_id`, `nom`, `stability`, `pan`, et `fx` s'il y a un effet) ;
   - dans `speaker_ids` et `speakers_doc` du découpage ;
   - et, pour l'affichage, dans le dictionnaire `NOMS` de `livrer_chapitre.py`. Sinon, le nom s'affiche simplement en majuscules.

## 3. Jeu, pauses et conventions de lecture

- **Tags de jeu** testés, jamais prononcés :
  - `[whispers]` (chuchoté) ;
  - `[tired]` (las) ;
  - `[hesitant]` ;
  - `[calm]` (posé).

  Les employer avec parcimonie, seulement quand le texte le justifie : « murmura », « soupira », « plus bas », « sa voix ne monta pas d'un ton ». Pas de `[whispers]` sur une longue réplique. Narration sans tag.
- **Diamant masquée** parle sans tag (ton assuré), sauf indication du texte. **Porcelaine** porte `[calm]` sur quelques répliques glaciales seulement.
- Les **incises** (« dit-elle », « répéta-t-il, lentement… ») sont lues par le narrateur, dans des blocs séparés.
- Le **discours rapporté sans tiret** reste au narrateur, sauf exceptions décidées et notées dans NOTES_LECTURE.md.
- Les **chuchotements de foule** sont répartis entre voix âgées, en alternant femme et homme, avec 0,25 s entre eux.
- **Niveaux** :
  - les chuchotements sont posés 6 dB sous la parole ;
  - une courte réplique ne dépasse pas le récit de plus de 1,5 dB.
- **Pauses** :
  - 0,15 à 0,35 s entre une réplique et son incise ;
  - 0,5 à 0,8 s dans un échange rapide ;
  - 0,8 à 1,1 s entre paragraphes ;
  - 1,3 à 1,8 s après une chute ou un silence décrit ;
  - 2 s après le titre.
- **Titre** : lu « Chapitre quatrième. <Titre>. », avec un point à la place du tiret long. Un tiret long à l'intérieur d'une phrase devient une virgule pour la voix.

## 4. Procédure pour un nouveau chapitre

1. **Texte** : `$C/manuscrit_chN.txt`.
   - 1ʳᵉ ligne = le titre exactement comme dans le livre (`Chapitre quatrième — <Titre>`), puis un paragraphe par ligne ;
   - tiret de dialogue « — » suivi d'une espace simple : remplacer U+00A0 et U+202F par des espaces normales ;
   - apostrophes typographiques ’ conservées, fins de ligne LF.

   Les paragraphes sont numérotés à partir de 0 (le titre).
2. **Découpage** : lancer l'outil **Workflow** avec `scriptPath` = `$REPO/livre_audio/decoupage_chapitre.js` (chemin absolu). Il fait travailler 3 découpeurs, puis une synthèse, 3 relecteurs et une version finale, avec contrôle automatique du texte.
   `args` = un objet avec **exactement** ces 7 clés :
   - `book` : `"Diamant et Porcelaine"` ;
   - `chapter_label` : `"le chapitre 4 (« <Titre> »)"` ;
   - `title_tts` : `"Chapitre quatrième. <Titre>."` ;
   - `speaker_ids` : les rôles présents ;
   - `speakers_doc` : **reprendre tel quel** celui de `livre/ch3/args_decoupage.json` (archive) et ajouter les nouveaux rôles ;
   - `rules` : sur le modèle de `livre/ch3/args_decoupage.json`. Y lister les répliques sans incise dont l'attribution est délicate, l'état du masque de Diamant, les tags attendus et les mots inventés à signaler ;
   - `manuscript` : le texte exact de `manuscrit_chN.txt`.

   À la fin, la notification donne le fichier `…/tasks/<id>.output`. Vérifier que `result.errors` vaut `[]`. Enregistrer les `args` utilisés dans `$C/args_decoupage.json`.
3. **Validation** : `python3 $REPO/livre_audio/preparer_script.py $C/manuscrit_chN.txt <fichier .output> $C/script_chN.json [--sans-effet P0-P1:diamant]`.
   - Le script refuse tout écart de texte.
   - `--sans-effet` sert aux paragraphes où Diamant a retiré son masque.
   - Si besoin, retoucher le `tts_text` à la main dans `script_chN.json`, puis le noter dans NOTES_LECTURE.md. Exemple : un mot seul suivi d'une incise qui le dit « lentement » reçoit « … » à la place de la virgule.
4. **Production** : `python3 $REPO/livre_audio/livre_audio.py $C/script_chN.json $C/voix.json $C/travail $C/Diamant_et_Porcelaine_chN.mp3 --seed "$(cat $C/graines.txt)"`.
   - Lors du premier passage, `graines.txt` est vide ou absent : omettre `--seed`.
   - Coût ≈ 0,42 crédit par caractère, soit environ 3 500 crédits pour 8 000 caractères.
5. **Contrôle des prises**, affiché par l'outil :
   - Les **homophones sont acceptés** : « dit-il » / « dix », « lieue » / « lieu », singulier / pluriel, nom inventé écrit autrement mais prononcé juste…
   - Refaire une prise avec une graine en cas de vraie erreur : mot changé, prise vide ou bruitée (« musique de fond »), mot isolé mal formé ou précédé d'un bruit de bouche. Essayer `--seed bNNN=7`, puis 19, puis 31.
   - **Garder la graine** dans `graines.txt` : une seule ligne, valeurs séparées par des virgules, sans espace, par exemple `b036=7,b052=19`. La repasser à chaque exécution, sinon la prise est régénérée.
   - Un chuchotement peut tromper la retranscription. Avant de refaire la prise, vérifier avec un mot-clé :
     `curl -sS -X POST https://api.elevenlabs.io/v1/speech-to-text -H "xi-api-key: $ELEVENLABS_API_KEY" -F model_id=scribe_v2 -F language_code=fr -F keyterms="<mot>" -F file=@$C/travail/prises/bNNN.mp3`.
   - `fins à vérifier` : `coupée` signifie que la parole touche la fin du fichier ; `bouffée` signale un bruit isolé après un silence. Les clics isolés au début ou à la fin sont retirés automatiquement au montage (vérifié sur 3 chapitres). Ne refaire la prise que si la retranscription montre un mot manquant.
6. **Livraison** : `python3 $REPO/livre_audio/livrer_chapitre.py $C N "Diamant et Porcelaine" "Chapitre quatrième : <Titre>" $W/livraison_chN [--note "choix de lecture"] [--version _v2]`.
   - Le script retranscrit le chapitre entier et le compare au manuscrit (payant, environ 9 min de Scribe), écrit la fiche des voix, puis prépare le ZIP et l'aperçu.
   - Envoyer l'aperçu (*render*), puis le ZIP (*attach*).
7. Ne rien committer du dossier `livre/`. Seuls les outils génériques vont dans le dépôt, après avoir vérifié qu'aucun texte du roman ni la clé n'y figurent.

## 5. Refaire un chapitre déjà produit (0 crédit)

Ne pas relancer le découpage. Exemple pour changer de réglage de heaume :

```
python3 $REPO/livre_audio/livre_audio.py $C/script_chN.json $C/voix.json $C/travail $C/Diamant_et_Porcelaine_chN.mp3 --seed "$(cat $C/graines.txt)" --only aucun
python3 $REPO/livre_audio/livrer_chapitre.py $C N "Diamant et Porcelaine" "Chapitre … : …" $W/livraison_chN --version _vK --sans-controle
```

- `--only aucun` garde toutes les prises présentes. La clé n'est pas nécessaire tant qu'aucune prise ne manque.
- Résultat attendu : `crédits utilisés cette exécution : 0`.
- Vérifié : le chapitre 2 refait ainsi depuis l'archive, sans clé, est **identique octet pour octet** au fichier livré.

**Ce qui coûte ou ne coûte pas** (l'empreinte d'une prise contient la voix, le texte, le tag, les réglages, la graine et le texte des deux blocs voisins) :
- **gratuit** (montage seul) : `pause_after`, `fx`, `pan`, `--sans-effet`, les réglages de `casque()` ;
- **payant** :
  - `tts_text` : le bloc et ses deux voisins sont refaits ;
  - `tag` ou graine : le bloc est refait ;
  - `stability`, `similarity` ou `voice_id` : toutes les prises de la voix sont refaites.
- **À ne jamais faire** sur un chapitre produit : le redécouper, ou ajouter ou supprimer un bloc. Cela décale les numéros bNNN, les graines visent alors le mauvais bloc et le reste est refait.
- Pour refaire une seule prise : `--only bNNN`, avec sa graine.

## 6. Réglages techniques de `livre_audio.py` (ne pas modifier sans raison)

- **Synthèse** :
  - `eleven_v4`, `mp3_44100_192` ;
  - `previous_text` / `next_text` = blocs voisins ;
  - une réplique coupée par une incise et finissant par « , ; : » est envoyée avec un point final, sinon eleven_v4 avale la fin.
- **Montage** :
  - silences rognés à -45 dB ;
  - îlots parasites retirés (moins de 120 ms, faibles, ou isolés après au moins 0,3 s de silence) ;
  - niveau par voix -20 LUFS, chuchotements -26 LUFS ;
  - stéréo selon le pan ;
  - queues de réverbération du heaume sur le silence suivant ;
  - 0,5 s en tête et 1,5 s en fin ;
  - normalisation finale à -18 LUFS, limiteur 0,63 (crête vraie ≈ -3,5 dBTP), MP3 192 kbps.
