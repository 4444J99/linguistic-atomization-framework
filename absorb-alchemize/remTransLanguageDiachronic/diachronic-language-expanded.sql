-- Requires base schema and seeds from diachronic_language_schema.sql

-- Cognate set: REGNUM→REALM/REINO/REGNO/RÈGNE
INSERT INTO etymon(headword,gloss,stage_id) VALUES ('rēgnum','kingdom',(SELECT id FROM language_stage WHERE lang_code='la' AND abbrev='CL')) ON CONFLICT DO NOTHING;
INSERT INTO cognate_set(label) VALUES ('REGNUM→REALM/REINO/REGNO/RÈGNE') ON CONFLICT DO NOTHING;
WITH ety AS (SELECT id AS ety_id FROM etymon WHERE headword = 'rēgnum'), cs AS (SELECT id AS cs_id FROM cognate_set WHERE label = 'REGNUM→REALM/REINO/REGNO/RÈGNE')
INSERT INTO lexeme(lemma,pos) VALUES ('realm','NOUN'), ('reino','NOUN'), ('regno','NOUN'), ('règne','NOUN') ON CONFLICT DO NOTHING;
INSERT INTO lexeme_stage_map(lexeme_id,stage_id,etymon_id,cognate_set_id,reliability) VALUES ( (SELECT id FROM lexeme WHERE lemma='realm'), (SELECT id FROM language_stage WHERE abbrev='ModE'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='reino'), (SELECT id FROM language_stage WHERE abbrev='ModSp'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='regno'), (SELECT id FROM language_stage WHERE abbrev='ModI'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='règne'), (SELECT id FROM language_stage WHERE abbrev='ModF'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 );

-- Cognate set: CAPUT→CHIEF/CABEZA/CAPO/TÊTE*
INSERT INTO etymon(headword,gloss,stage_id) VALUES ('caput','head',(SELECT id FROM language_stage WHERE lang_code='la' AND abbrev='CL')) ON CONFLICT DO NOTHING;
INSERT INTO cognate_set(label) VALUES ('CAPUT→CHIEF/CABEZA/CAPO/TÊTE*') ON CONFLICT DO NOTHING;
WITH ety AS (SELECT id AS ety_id FROM etymon WHERE headword = 'caput'), cs AS (SELECT id AS cs_id FROM cognate_set WHERE label = 'CAPUT→CHIEF/CABEZA/CAPO/TÊTE*')
INSERT INTO lexeme(lemma,pos) VALUES ('chief','NOUN'), ('cabeza','NOUN'), ('capo','NOUN'), ('chef','NOUN') ON CONFLICT DO NOTHING;
INSERT INTO lexeme_stage_map(lexeme_id,stage_id,etymon_id,cognate_set_id,reliability) VALUES ( (SELECT id FROM lexeme WHERE lemma='chief'), (SELECT id FROM language_stage WHERE abbrev='ModE'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='cabeza'), (SELECT id FROM language_stage WHERE abbrev='ModSp'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='capo'), (SELECT id FROM language_stage WHERE abbrev='ModI'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='chef'), (SELECT id FROM language_stage WHERE abbrev='ModF'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 );

-- Cognate set: AUDIO→AUDIENCE/AUDIENCIA/AUDIENCE/UDIENZA
INSERT INTO etymon(headword,gloss,stage_id) VALUES ('audīre','to hear',(SELECT id FROM language_stage WHERE lang_code='la' AND abbrev='CL')) ON CONFLICT DO NOTHING;
INSERT INTO cognate_set(label) VALUES ('AUDIO→AUDIENCE/AUDIENCIA/AUDIENCE/UDIENZA') ON CONFLICT DO NOTHING;
WITH ety AS (SELECT id AS ety_id FROM etymon WHERE headword = 'audīre'), cs AS (SELECT id AS cs_id FROM cognate_set WHERE label = 'AUDIO→AUDIENCE/AUDIENCIA/AUDIENCE/UDIENZA')
INSERT INTO lexeme(lemma,pos) VALUES ('audience','NOUN'), ('audiencia','NOUN'), ('audience','NOUN'), ('udienza','NOUN') ON CONFLICT DO NOTHING;
INSERT INTO lexeme_stage_map(lexeme_id,stage_id,etymon_id,cognate_set_id,reliability) VALUES ( (SELECT id FROM lexeme WHERE lemma='audience'), (SELECT id FROM language_stage WHERE abbrev='ModE'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='audiencia'), (SELECT id FROM language_stage WHERE abbrev='ModSp'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='audience'), (SELECT id FROM language_stage WHERE abbrev='ModF'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='udienza'), (SELECT id FROM language_stage WHERE abbrev='ModI'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 );

-- Cognate set: SCRIPTUM→SCRIPT/ESCRITURA/ÉCRIT/ SCRITTA
INSERT INTO etymon(headword,gloss,stage_id) VALUES ('scrīptum','writing',(SELECT id FROM language_stage WHERE lang_code='la' AND abbrev='CL')) ON CONFLICT DO NOTHING;
INSERT INTO cognate_set(label) VALUES ('SCRIPTUM→SCRIPT/ESCRITURA/ÉCRIT/ SCRITTA') ON CONFLICT DO NOTHING;
WITH ety AS (SELECT id AS ety_id FROM etymon WHERE headword = 'scrīptum'), cs AS (SELECT id AS cs_id FROM cognate_set WHERE label = 'SCRIPTUM→SCRIPT/ESCRITURA/ÉCRIT/ SCRITTA')
INSERT INTO lexeme(lemma,pos) VALUES ('script','NOUN'), ('escritura','NOUN'), ('écrit','NOUN'), ('scritta','NOUN') ON CONFLICT DO NOTHING;
INSERT INTO lexeme_stage_map(lexeme_id,stage_id,etymon_id,cognate_set_id,reliability) VALUES ( (SELECT id FROM lexeme WHERE lemma='script'), (SELECT id FROM language_stage WHERE abbrev='ModE'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='escritura'), (SELECT id FROM language_stage WHERE abbrev='ModSp'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='écrit'), (SELECT id FROM language_stage WHERE abbrev='ModF'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='scritta'), (SELECT id FROM language_stage WHERE abbrev='ModI'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 );

-- Cognate set: DIGITUS→DIGIT/DEDO/DOIGT/DITO
INSERT INTO etymon(headword,gloss,stage_id) VALUES ('digitus','finger',(SELECT id FROM language_stage WHERE lang_code='la' AND abbrev='CL')) ON CONFLICT DO NOTHING;
INSERT INTO cognate_set(label) VALUES ('DIGITUS→DIGIT/DEDO/DOIGT/DITO') ON CONFLICT DO NOTHING;
WITH ety AS (SELECT id AS ety_id FROM etymon WHERE headword = 'digitus'), cs AS (SELECT id AS cs_id FROM cognate_set WHERE label = 'DIGITUS→DIGIT/DEDO/DOIGT/DITO')
INSERT INTO lexeme(lemma,pos) VALUES ('digit','NOUN'), ('dedo','NOUN'), ('doigt','NOUN'), ('dito','NOUN') ON CONFLICT DO NOTHING;
INSERT INTO lexeme_stage_map(lexeme_id,stage_id,etymon_id,cognate_set_id,reliability) VALUES ( (SELECT id FROM lexeme WHERE lemma='digit'), (SELECT id FROM language_stage WHERE abbrev='ModE'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='dedo'), (SELECT id FROM language_stage WHERE abbrev='ModSp'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='doigt'), (SELECT id FROM language_stage WHERE abbrev='ModF'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='dito'), (SELECT id FROM language_stage WHERE abbrev='ModI'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 );

-- Cognate set: FACERE→FACT/HECHO/FAIT/FATTO
INSERT INTO etymon(headword,gloss,stage_id) VALUES ('facere','to do, make',(SELECT id FROM language_stage WHERE lang_code='la' AND abbrev='CL')) ON CONFLICT DO NOTHING;
INSERT INTO cognate_set(label) VALUES ('FACERE→FACT/HECHO/FAIT/FATTO') ON CONFLICT DO NOTHING;
WITH ety AS (SELECT id AS ety_id FROM etymon WHERE headword = 'facere'), cs AS (SELECT id AS cs_id FROM cognate_set WHERE label = 'FACERE→FACT/HECHO/FAIT/FATTO')
INSERT INTO lexeme(lemma,pos) VALUES ('fact','NOUN'), ('hecho','NOUN'), ('fait','NOUN'), ('fatto','NOUN') ON CONFLICT DO NOTHING;
INSERT INTO lexeme_stage_map(lexeme_id,stage_id,etymon_id,cognate_set_id,reliability) VALUES ( (SELECT id FROM lexeme WHERE lemma='fact'), (SELECT id FROM language_stage WHERE abbrev='ModE'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='hecho'), (SELECT id FROM language_stage WHERE abbrev='ModSp'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='fait'), (SELECT id FROM language_stage WHERE abbrev='ModF'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='fatto'), (SELECT id FROM language_stage WHERE abbrev='ModI'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 );

-- Cognate set: RATIO→REASON/RAZÓN/RAISON/RAGIONE
INSERT INTO etymon(headword,gloss,stage_id) VALUES ('ratiō','reason, account',(SELECT id FROM language_stage WHERE lang_code='la' AND abbrev='CL')) ON CONFLICT DO NOTHING;
INSERT INTO cognate_set(label) VALUES ('RATIO→REASON/RAZÓN/RAISON/RAGIONE') ON CONFLICT DO NOTHING;
WITH ety AS (SELECT id AS ety_id FROM etymon WHERE headword = 'ratiō'), cs AS (SELECT id AS cs_id FROM cognate_set WHERE label = 'RATIO→REASON/RAZÓN/RAISON/RAGIONE')
INSERT INTO lexeme(lemma,pos) VALUES ('reason','NOUN'), ('razón','NOUN'), ('raison','NOUN'), ('ragione','NOUN') ON CONFLICT DO NOTHING;
INSERT INTO lexeme_stage_map(lexeme_id,stage_id,etymon_id,cognate_set_id,reliability) VALUES ( (SELECT id FROM lexeme WHERE lemma='reason'), (SELECT id FROM language_stage WHERE abbrev='ModE'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='razón'), (SELECT id FROM language_stage WHERE abbrev='ModSp'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='raison'), (SELECT id FROM language_stage WHERE abbrev='ModF'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='ragione'), (SELECT id FROM language_stage WHERE abbrev='ModI'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 );

-- Cognate set: NATIO→NATION/NACIÓN/NATION/NAZIONE
INSERT INTO etymon(headword,gloss,stage_id) VALUES ('nātiō','people, nation',(SELECT id FROM language_stage WHERE lang_code='la' AND abbrev='CL')) ON CONFLICT DO NOTHING;
INSERT INTO cognate_set(label) VALUES ('NATIO→NATION/NACIÓN/NATION/NAZIONE') ON CONFLICT DO NOTHING;
WITH ety AS (SELECT id AS ety_id FROM etymon WHERE headword = 'nātiō'), cs AS (SELECT id AS cs_id FROM cognate_set WHERE label = 'NATIO→NATION/NACIÓN/NATION/NAZIONE')
INSERT INTO lexeme(lemma,pos) VALUES ('nation','NOUN'), ('nación','NOUN'), ('nation','NOUN'), ('nazione','NOUN') ON CONFLICT DO NOTHING;
INSERT INTO lexeme_stage_map(lexeme_id,stage_id,etymon_id,cognate_set_id,reliability) VALUES ( (SELECT id FROM lexeme WHERE lemma='nation'), (SELECT id FROM language_stage WHERE abbrev='ModE'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='nación'), (SELECT id FROM language_stage WHERE abbrev='ModSp'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='nation'), (SELECT id FROM language_stage WHERE abbrev='ModF'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='nazione'), (SELECT id FROM language_stage WHERE abbrev='ModI'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 );

-- Cognate set: COMPUTARE→COMPUTE/CONTAR/COMPTER/CONTARE
INSERT INTO etymon(headword,gloss,stage_id) VALUES ('computāre','to reckon',(SELECT id FROM language_stage WHERE lang_code='la' AND abbrev='CL')) ON CONFLICT DO NOTHING;
INSERT INTO cognate_set(label) VALUES ('COMPUTARE→COMPUTE/CONTAR/COMPTER/CONTARE') ON CONFLICT DO NOTHING;
WITH ety AS (SELECT id AS ety_id FROM etymon WHERE headword = 'computāre'), cs AS (SELECT id AS cs_id FROM cognate_set WHERE label = 'COMPUTARE→COMPUTE/CONTAR/COMPTER/CONTARE')
INSERT INTO lexeme(lemma,pos) VALUES ('compute','NOUN'), ('contar','NOUN'), ('compter','NOUN'), ('contare','NOUN') ON CONFLICT DO NOTHING;
INSERT INTO lexeme_stage_map(lexeme_id,stage_id,etymon_id,cognate_set_id,reliability) VALUES ( (SELECT id FROM lexeme WHERE lemma='compute'), (SELECT id FROM language_stage WHERE abbrev='ModE'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='contar'), (SELECT id FROM language_stage WHERE abbrev='ModSp'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='compter'), (SELECT id FROM language_stage WHERE abbrev='ModF'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='contare'), (SELECT id FROM language_stage WHERE abbrev='ModI'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 );

-- Cognate set: CREDERE→CREDIT/CREER/CROIRE/CREDERE
INSERT INTO etymon(headword,gloss,stage_id) VALUES ('crēdere','to believe, entrust',(SELECT id FROM language_stage WHERE lang_code='la' AND abbrev='CL')) ON CONFLICT DO NOTHING;
INSERT INTO cognate_set(label) VALUES ('CREDERE→CREDIT/CREER/CROIRE/CREDERE') ON CONFLICT DO NOTHING;
WITH ety AS (SELECT id AS ety_id FROM etymon WHERE headword = 'crēdere'), cs AS (SELECT id AS cs_id FROM cognate_set WHERE label = 'CREDERE→CREDIT/CREER/CROIRE/CREDERE')
INSERT INTO lexeme(lemma,pos) VALUES ('credit','NOUN'), ('creer','NOUN'), ('croire','NOUN'), ('credere','NOUN') ON CONFLICT DO NOTHING;
INSERT INTO lexeme_stage_map(lexeme_id,stage_id,etymon_id,cognate_set_id,reliability) VALUES ( (SELECT id FROM lexeme WHERE lemma='credit'), (SELECT id FROM language_stage WHERE abbrev='ModE'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='creer'), (SELECT id FROM language_stage WHERE abbrev='ModSp'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='croire'), (SELECT id FROM language_stage WHERE abbrev='ModF'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 ), ( (SELECT id FROM lexeme WHERE lemma='credere'), (SELECT id FROM language_stage WHERE abbrev='ModI'), (SELECT ety_id FROM ety), (SELECT cs_id FROM cs), 0.95 );

-- Sound change placeholders (illustrative)

INSERT INTO sound_change(from_stage_id,to_stage_id,rule,priority)
SELECT s1.id, s2.id, 'Vulgar Latin lenition set (placeholder)', 100
FROM language_stage s1, language_stage s2
WHERE s1.abbrev='VL' AND s2.abbrev IN ('OF','OSp','EI');

INSERT INTO sound_change(from_stage_id,to_stage_id,rule,priority)
SELECT s1.id, s2.id, 'Palatalization front vowels (placeholder)', 110
FROM language_stage s1, language_stage s2
WHERE s1.abbrev IN ('VL','OF') AND s2.abbrev IN ('MF','ModF','ModI','ModSp');
