export const meta = {
  name: 'livre-audio-decoupage-chapitre',
  description: 'Découpe un chapitre de roman en répliques par voix pour un livre audio (paramétré), avec relectures adversariales et contrôle exact du texte',
  phases: [
    { title: 'Découper', detail: '3 découpages indépendants' },
    { title: 'Synthèse', detail: 'meilleur découpage' },
    { title: 'Relecture', detail: 'texte exact, attribution, technique voix' },
    { title: 'Final', detail: 'corrections validées + contrôle exact' },
  ],
}

const MS = args.manuscript
const PARAS = MS.split('\n').filter(l => l.trim().length)

const CONTEXT = `
TÂCHE : préparer le script d'un LIVRE AUDIO à plusieurs voix (synthèse ElevenLabs eleven_v4, voix françaises natives) pour ${args.chapter_label} du roman « ${args.book} » (texte ci-dessous, à ne JAMAIS modifier).

VOIX DISPONIBLES (champ speaker) :
${args.speakers_doc}

PARAGRAPHES DU MANUSCRIT (numérotés à partir de 0, un par ligne) :
${PARAS.map((p, i) => `[${i}] ${p}`).join('\n')}

RÈGLES IMPÉRATIVES
1. TEXTE EXACT : chaque bloc a un champ "para" (numéro du paragraphe) et un champ "text". Pour chaque paragraphe, la concaténation des "text" de ses blocs, dans l'ordre et joints par une espace, doit redonner EXACTEMENT le paragraphe, au caractère près (mêmes apostrophes typographiques ’, mêmes espaces avant ; : ? !), à une seule exception : le tiret de dialogue initial « — » et l'espace qui le suit sont retirés. On ne coupe qu'aux espaces. Aucun mot ajouté, retiré, corrigé ou déplacé.
2. ATTRIBUTION : une réplique entre tirets va au personnage qui parle (dans un dialogue à deux, les répliques sans incise alternent : vérifie qui parle à chaque ligne d'après le sens) ; une incise (« , dit-elle. », « reprit-elle, du ton de… », « répéta-t-il, lentement, comme… ») est un bloc séparé lu par "narrateur", et la suite de la réplique après l'incise redevient un bloc du personnage. ${args.rules}
3. TAGS (champ "tag") : uniquement "" ou l'un de "[whispers]", "[hesitant]", "[tired]", "[calm]". Le tag n'est pas prononcé : il règle le jeu. Les utiliser avec parcimonie et seulement quand le texte le justifie. Narration sans tag.
4. PAUSES (champ "pause_after", en secondes, silence après le bloc) : 0.15 à 0.35 entre une réplique et son incise ou à l'intérieur d'un même paragraphe ; 0.5 à 0.8 entre deux répliques d'un échange rapide ; 0.8 à 1.1 entre deux paragraphes de narration ; 1.3 à 1.8 après une phrase isolée qui fait chute ou un silence décrit par le texte (« Elle ne répondit pas. ») ; 2.0 après le titre ; 0 pour le tout dernier bloc.
5. Le titre (paragraphe 0) est lu par le narrateur ; son texte reste exactement celui du manuscrit. Le champ "tts_text" sert au texte envoyé à la voix : identique à "text", sauf (a) pour le titre où l'on écrit « ${args.title_tts} » (le tiret long se lit mal) et (b) un tiret long à l'intérieur d'une phrase, qu'on remplace par une virgule dans tts_text ; partout ailleurs tts_text = text.
6. Un bloc de narration = un paragraphe entier ; une réplique longue reste un seul bloc (tous les paragraphes sont sous 900 caractères).
7. Champ "notes" : choix d'attribution délicats, risques de prononciation pour la voix française (noms inventés du roman ; subjonctifs imparfaits ; « puis » au sens de « peux »…).
`
const BLOCK = { type: 'object', properties: {
  para: { type: 'integer' }, speaker: { type: 'string', enum: args.speaker_ids },
  text: { type: 'string' }, tts_text: { type: 'string' }, tag: { type: 'string', enum: ['', '[whispers]', '[hesitant]', '[tired]', '[calm]'] },
  pause_after: { type: 'number' } }, required: ['para', 'speaker', 'text', 'tts_text', 'tag', 'pause_after'] }
const SCRIPT_SCHEMA = { type: 'object', properties: { blocks: { type: 'array', items: BLOCK }, notes: { type: 'string' } }, required: ['blocks', 'notes'] }
const REVIEW_SCHEMA = { type: 'object', properties: {
  issues: { type: 'array', items: { type: 'object', properties: { para: { type: 'integer' }, severity: { type: 'string', enum: ['blocker', 'major', 'minor'] }, problem: { type: 'string' }, fix: { type: 'string' } }, required: ['para', 'severity', 'problem', 'fix'] } },
  summary: { type: 'string' } }, required: ['issues', 'summary'] }

// contrôle déterministe : chaque paragraphe se reconstruit exactement
function check(blocks) {
  const errs = []
  PARAS.forEach((p, i) => {
    const want = p.replace(/^— /, '')
    const got = blocks.filter(b => b.para === i).map(b => b.text).join(' ')
    if (got !== want) errs.push(`paragraphe ${i} : attendu « ${want.slice(0, 80)}… », obtenu « ${got.slice(0, 80)}… »`)
  })
  const order = blocks.map(b => b.para)
  for (let k = 1; k < order.length; k++) if (order[k] < order[k - 1]) errs.push(`ordre des blocs cassé au bloc ${k}`)
  blocks.forEach((b, k) => { if (b.para !== 0 && b.tts_text !== b.text.replace(/ — /g, ', ')) errs.push(`bloc ${k} : tts_text différent de text`) })
  return errs
}

const LENSES = [
  { key: 'fidelite', role: 'Tu es un éditeur de livres audio, obsédé par le respect exact du texte de l\'auteur et des conventions de lecture (incises, tirets de dialogue).' },
  { key: 'mise_en_scene', role: 'Tu es un directeur artistique de fiction audio : distribution des voix, rythme, silences, jeu juste et sobre.' },
  { key: 'technique', role: 'Tu es un ingénieur de synthèse vocale : découpage sûr pour la TTS, tags de jeu pertinents, risques de prononciation.' },
]

phase('Découper')
const drafts = (await parallel(LENSES.map(l => () =>
  agent(`${l.role}\n${CONTEXT}\nProduis le script complet (tous les paragraphes, dans l'ordre). Vérifie avec python la règle 1 (reconstruction exacte de chaque paragraphe) avant de répondre.`,
    { label: `decoupage:${l.key}`, phase: 'Découper', schema: SCRIPT_SCHEMA })
))).filter(Boolean).map((d, i) => ({ lens: LENSES[i].key, errors: check(d.blocks), ...d }))
log(drafts.map(d => `${d.lens} : ${d.errors.length} écart(s) de texte`).join(' | '))

phase('Synthèse')
let synth = await agent(`Tu es le directeur artistique du livre audio. Construis le MEILLEUR script à partir de ces ${drafts.length} propositions (attribution juste, jeu sobre, pauses musicales, texte exact). Le champ "errors" de chaque proposition liste ses écarts de texte détectés automatiquement : ne les reproduis pas.
${CONTEXT}
PROPOSITIONS :
${JSON.stringify(drafts)}
Vérifie la règle 1 avec python avant de répondre.`, { label: 'synthese', phase: 'Synthèse', schema: SCRIPT_SCHEMA })
let errs = check(synth.blocks)
if (errs.length) {
  synth = await agent(`Corrige ce script : le contrôle automatique a trouvé des écarts de texte. Garde tout le reste identique.\n${CONTEXT}\nÉCARTS :\n${errs.join('\n')}\nSCRIPT :\n${JSON.stringify(synth)}`, { label: 'synthese:correction', phase: 'Synthèse', schema: SCRIPT_SCHEMA })
  errs = check(synth.blocks)
}
log(`synthèse : ${synth.blocks.length} blocs, ${errs.length} écart(s) de texte`)

const REVIEWERS = [
  { key: 'texte', prompt: 'Relecteur adversarial — TEXTE EXACT ET CONVENTIONS : chaque mot de l\'auteur présent, rien d\'ajouté, coupures aux bons endroits (incises), tiret de dialogue retiré seulement en début de réplique, apostrophes et ponctuation intactes. Utilise python pour comparer.' },
  { key: 'attribution', prompt: 'Relecteur adversarial — ATTRIBUTION ET JEU : qui parle à chaque bloc (pièges : répliques sans incise qui alternent, incises, discours rapporté, lignes sans tiret), tags justifiés par le texte et pas sur-joués, cohérence des personnages.' },
  { key: 'rythme_tts', prompt: 'Relecteur adversarial — RYTHME ET TECHNIQUE VOIX : pauses (chutes, changements de scène, enchaînements réplique/incise), longueur des blocs, titre, tts_text, risques de prononciation à tester (noms inventés, subjonctifs imparfaits) ; propose des pauses précises.' },
]
phase('Relecture')
const reviews = (await parallel(REVIEWERS.map(r => () =>
  agent(`${r.prompt}\nSois exigeant. Pour chaque problème réel : paragraphe, gravité, problème, correction précise. Ne liste pas ce qui est correct.\n${CONTEXT}\nSCRIPT À RELIRE :\n${JSON.stringify(synth.blocks)}`,
    { label: `relecture:${r.key}`, phase: 'Relecture', schema: REVIEW_SCHEMA })
))).filter(Boolean).map((r, i) => ({ reviewer: REVIEWERS[i].key, ...r }))
log(`${reviews.reduce((a, r) => a + r.issues.length, 0)} remarques`)

phase('Final')
let final = await agent(`Tu es le directeur artistique. Évalue CHAQUE remarque : applique si juste, rejette sinon. Rends le script final complet. Vérifie la règle 1 avec python. Notes : remarques appliquées/rejetées (court) + risques de prononciation à tester.
${CONTEXT}
SCRIPT :
${JSON.stringify(synth.blocks)}
REMARQUES :
${JSON.stringify(reviews)}`, { label: 'final', phase: 'Final', schema: SCRIPT_SCHEMA })
errs = check(final.blocks)
if (errs.length) {
  final = await agent(`Corrige ce script : le contrôle automatique a trouvé des écarts de texte. Garde tout le reste identique.\n${CONTEXT}\nÉCARTS :\n${errs.join('\n')}\nSCRIPT :\n${JSON.stringify(final)}`, { label: 'final:correction', phase: 'Final', schema: SCRIPT_SCHEMA })
  errs = check(final.blocks)
}
log(`final : ${final.blocks.length} blocs, ${errs.length} écart(s) de texte`)
return { final, errors: errs }
