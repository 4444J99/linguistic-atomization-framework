# Corpus provenance and licence notices

The MIT licence in the repository root covers LingFrame's **code and documentation**. It does
**not** cover the texts in `corpus/`. Each corpus file keeps the status it had at its source.
The corpus is **not** entirely public domain. This file records what is known about each group
of files. It is a provenance record, not legal advice. Where a status has not been verified it is
marked as such.

The `corpus/` directory is not included in the `lingframe` wheel or sdist.

## 1. Public-domain transcriptions (most files)

Most files are transcriptions, mainly from Project Gutenberg and sacred-texts.com, of works and
translations first published before 1931. These are in the public domain in the United States.
Copyright terms differ in other countries. Some files still carry the Project Gutenberg header and
licence; Project Gutenberg's trademark terms apply to copies distributed with that header (see the
licence text inside those files). The source of each file is listed in `corpus_index.yaml`.

## 2. Files under their own terms

### OpenScriptures Hebrew Bible (morphhb): `hebrew/tanakh/hebrew_masoretic.txt`

- Source: Open Scriptures Hebrew Bible (OSHB), <https://github.com/openscriptures/morphhb>,
  based on the Westminster Leningrad Codex (WLC 4.20).
- Terms, as published in the morphhb `README.md` and `LICENSE.md`: the text of the WLC is in the
  public domain; the OSHB lemma and morphology data are licensed under
  [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
- Attribution requested by OSHB: "Original work of the Open Scriptures Hebrew Bible available at
  https://github.com/openscriptures/morphhb".
- This file contains the pointed Hebrew text only. It is credited to OSHB as requested.

### Tanzil Quran Text: `arabic-persian/quran/arabic_original.txt`

- Source: Tanzil Project, <https://tanzil.net>. Tanzil Quran Text (Uthmani, Version 1.1),
  Copyright (C) 2007-2026 Tanzil Project.
- Licence: Creative Commons Attribution 3.0, with the Tanzil terms of use published at
  <https://tanzil.net/docs/text_license>:
  - Permission is granted to copy and distribute verbatim copies of this text, but changing it is
    not allowed.
  - The source (Tanzil Project) must be clearly indicated, with a link to tanzil.net so users can
    track changes.
  - The copyright notice must be included in all verbatim copies, and reproduced appropriately in
    all files derived from or containing a substantial portion of the text.
- The Tanzil copyright block is kept, unmodified, at the end of the file. **Do not edit,
  normalise, reflow or re-encode this file.** Analysis outputs that reproduce a substantial portion
  of it must carry the Tanzil notice.

### Tanzil translations: `arabic-persian/quran/english_pickthall_1930.txt`, `english_yusufali_1934.txt`

- Source: Tanzil translations page, <https://tanzil.net/trans/>.
- Tanzil's published terms for these files: "The translations provided at this page are for
  non-commercial purposes only. If used otherwise, you need to obtain necessary permission from
  the translator or the publisher."
- Underlying copyright status (not verified): Pickthall's translation was first published in 1930.
  Yusuf Ali's was first published in 1934; its US status is uncertain.

### GRETIL Sanskrit e-texts: `sanskrit/bhagavad-gita/sanskrit_original.txt`, `sanskrit/rigveda/sanskrit_original.txt`

- Publisher: Göttingen Register of Electronic Texts in Indian Languages (GRETIL), SUB Göttingen,
  <https://gretil.sub.uni-goettingen.de/>.
- Sources (TEI originals):
  - Bhagavadgītā with the commentary ascribed to Śaṃkara:
    <https://gretil.sub.uni-goettingen.de/gretil/corpustei/sa_bhagavadgItA-comm.xml>
    (data entry and contribution: Gaudiya Grantha Mandira)
  - Ṛgveda-Saṃhitā, Aufrecht edition (Bonn 1877):
    <https://gretil.sub.uni-goettingen.de/gretil/corpustei/sa_Rgveda-edAufrecht.xml>
    (data entry: Barend A. Van Nooten and Gary B. Holland; contribution: Detlef Eichler)
- Licence, as stated in the `<availability>` block of each TEI source file and in the header of
  each corpus file: "Distributed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0
  International License" (<https://creativecommons.org/licenses/by-nc-sa/4.0/>). GRETIL adds: "This
  e-text was provided to GRETIL in good faith that no copyright rights have been infringed. If
  anyone wishes to assert copyright over this file, please contact the GRETIL management ... The
  file will be immediately removed pending resolution of the claim."
- These two files may be used for **non-commercial** purposes only, adaptations must be shared
  under the same licence, and the GRETIL header must be kept. These terms are not compatible with
  MIT; the repository's MIT licence does not apply to them.

### Project Gutenberg copyrighted eBook: `modern/the-trial/english_wyllie_pg7849.txt`

- This is **David Wyllie's** English translation of Kafka's *The Trial* (Project Gutenberg eBook
  #7849). It was previously mislabelled in this repository as the 1937 Willa and Edwin Muir
  translation.
- Project Gutenberg lists it as "Copyrighted". The translation is distributed by Project Gutenberg
  with the copyright holder's permission under the Project Gutenberg License. The file keeps the
  full Project Gutenberg header, the translator's copyright notice and the Project Gutenberg
  licence; **do not strip them**.

## 3. Status not verified

These files are probably redistributable, but their status has not been checked:

| File | Why it is uncertain |
|---|---|
| `japanese/kojiki/japanese_original.txt` | Aozora Bunko annotated edition; the annotator's apparatus may still be protected in some countries |
| `japanese/oku-no-hosomichi/japanese_original.txt` | Aozora Bunko annotated edition; same as above |
| `japanese/tale-of-genji/japanese_original.txt` | Aozora Bunko text of Yosano Akiko's modern-Japanese translation (1938-39), not Murasaki Shikibu's original |
| `japanese/heike-monogatari/japanese_original.txt` | University of Virginia Japanese Text Initiative e-text; terms not checked |
| `medieval/song-of-roland/old_french_original.txt` | Bibliotheca Augustana, Mortier 1940 edition; status of the edited text not checked |
| `modern/we/russian_original.txt` | az.lib.ru; first full Russian edition 1952; US status not checked |
| `classical/iliad/greek_original.txt`, `classical/odyssey/greek_original.txt` | "Sacred Texts Archive"; the specific edition is unknown |
| `chinese-classical/*/chinese_original.txt` | ctext.org and Chinese Wikisource; ancient texts, but ctext.org's terms for bulk extraction not checked |
| `arabic-persian/rubaiyat/persian_original*.txt`, `arabic-persian/shahnameh/persian_original*.txt` | Ganjoor; medieval texts, site terms not checked |

If you are a rights holder and believe a file here should not be redistributed, please open an
issue and it will be removed.
