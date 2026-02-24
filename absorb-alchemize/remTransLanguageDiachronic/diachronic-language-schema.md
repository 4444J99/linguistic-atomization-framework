
# Diachronic Language Schema (SQL)

```sql
-- Families and stages
CREATE TABLE language_family (
  id serial PRIMARY KEY,
  name text UNIQUE NOT NULL
);

CREATE TABLE script (
  code text PRIMARY KEY,
  name text NOT NULL
);

CREATE TABLE language (
  code text PRIMARY KEY,
  name text NOT NULL,
  family_id int REFERENCES language_family(id),
  parent_code text REFERENCES language(code),
  notes text
);

CREATE TABLE language_stage (
  id serial PRIMARY KEY,
  lang_code text REFERENCES language(code) ON DELETE CASCADE,
  name text NOT NULL,
  abbrev text,
  start_ce int,
  end_ce int,
  script_code text REFERENCES script(code),
  orthography jsonb,
  phonology jsonb
);

CREATE TABLE stage_relation (
  src_stage_id int REFERENCES language_stage(id) ON DELETE CASCADE,
  tgt_stage_id int REFERENCES language_stage(id) ON DELETE CASCADE,
  rel_type text NOT NULL,
  weight real DEFAULT 1.0,
  PRIMARY KEY(src_stage_id, tgt_stage_id, rel_type)
);

CREATE TABLE etymon (
  id bigserial PRIMARY KEY,
  headword text NOT NULL,
  gloss text,
  stage_id int REFERENCES language_stage(id) ON DELETE SET NULL
);

CREATE TABLE cognate_set (
  id bigserial PRIMARY KEY,
  label text,
  notes text
);

CREATE TABLE lexeme (
  id bigserial PRIMARY KEY,
  lemma text NOT NULL,
  pos text,
  sense jsonb
);

CREATE TABLE lexeme_stage_map (
  lexeme_id bigint REFERENCES lexeme(id) ON DELETE CASCADE,
  stage_id int REFERENCES language_stage(id) ON DELETE CASCADE,
  etymon_id bigint REFERENCES etymon(id),
  cognate_set_id bigint REFERENCES cognate_set(id),
  reliability real DEFAULT 0.9,
  PRIMARY KEY(lexeme_id, stage_id)
);

CREATE TABLE lexeme_form (
  id bigserial PRIMARY KEY,
  lexeme_id bigint REFERENCES lexeme(id) ON DELETE CASCADE,
  stage_id int REFERENCES language_stage(id) ON DELETE CASCADE,
  form text NOT NULL,
  features jsonb
);

CREATE TABLE sound_change (
  id bigserial PRIMARY KEY,
  from_stage_id int REFERENCES language_stage(id),
  to_stage_id int REFERENCES language_stage(id),
  rule text NOT NULL,
  notation text DEFAULT 'SPE',
  priority int DEFAULT 100
);

-- if phoneme inventory table 'segment' exists, add stage reference
-- CREATE TABLE segment(id bigserial PRIMARY KEY, symbol text);
-- ALTER TABLE segment ADD COLUMN stage_id int REFERENCES language_stage(id);

CREATE TABLE alignment_stage (
  id bigserial PRIMARY KEY,
  src_seg_id bigint,
  tgt_seg_id bigint,
  unit text NOT NULL,
  relation text NOT NULL,
  score real,
  method text
);
```

## Seeds

```sql
INSERT INTO language_family(name) VALUES
('Indo-European'), ('Romance'), ('Germanic');

INSERT INTO language(code,name,family_id,parent_code) VALUES
('la','Latin',1,NULL),
('fro','Old French',2,'la'),
('fr','French',2,'fro'),
('it','Italian',2,'la'),
('es','Spanish',2,'la'),
('pt','Portuguese',2,'la'),
('ro','Romanian',2,'la'),
('en','English',1,NULL);

INSERT INTO script(code,name) VALUES ('Latn','Latin'),('Grek','Greek');

INSERT INTO language_stage(lang_code,name,abbrev,start_ce,end_ce,script_code) VALUES
('la','Classical Latin','CL',-75,200,'Latn'),
('la','Vulgar Latin','VL',200,800,'Latn'),
('fro','Old French','OF',950,1350,'Latn'),
('fr','Middle French','MF',1350,1600,'Latn'),
('fr','Modern French','ModF',1600,2100,'Latn'),
('it','Early Italian','EI',1200,1600,'Latn'),
('it','Modern Italian','ModI',1600,2100,'Latn'),
('es','Old Spanish','OSp',900,1400,'Latn'),
('es','Modern Spanish','ModSp',1600,2100,'Latn'),
('en','Old English','OE',450,1150,'Latn'),
('en','Middle English','ME',1150,1500,'Latn'),
('en','Early Modern English','EModE',1500,1700,'Latn'),
('en','Modern English','ModE',1700,2100,'Latn');
```

## Example: Regal → Royal → Real

```sql
INSERT INTO etymon(headword,gloss,stage_id) VALUES
('rēgālis','royal; of a king',(SELECT id FROM language_stage WHERE lang_code='la' AND abbrev='CL'));

INSERT INTO cognate_set(label) VALUES ('REGAL-ROYAL-REAL');

INSERT INTO lexeme(lemma,pos) VALUES ('regal','ADJ'),('royal','ADJ'),('real','ADJ');

WITH ety AS (SELECT id AS ety_id FROM etymon WHERE headword='rēgālis'),
     cs  AS (SELECT id AS cs_id  FROM cognate_set WHERE label='REGAL-ROYAL-REAL')
INSERT INTO lexeme_stage_map(lexeme_id,stage_id,etymon_id,cognate_set_id,reliability)
SELECT l.id, s.id, ety.ety_id, cs.cs_id, 0.95
FROM lexeme l
JOIN language_stage s ON ( (l.lemma='regal' AND s.abbrev='ModE')
                        OR (l.lemma='royal' AND s.abbrev='ModF')
                        OR (l.lemma='real'  AND s.abbrev='ModSp') ),
     ety, cs;
```
