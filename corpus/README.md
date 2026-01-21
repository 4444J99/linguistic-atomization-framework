# LingFrame Corpus

A curated collection of literary texts for rhetorical analysis tutorials and experimentation.

---

## Overview

| Period | Texts | Files | Total Lines | Date Range |
|--------|-------|-------|-------------|------------|
| Classical | 2 | 3 | 36,684 | 8th c. BCE – 1st c. BCE |
| Medieval | 3 | 6 | 89,602 | 8th–14th c. CE |
| Early Modern | 1 | 1 | 4,129 | 17th c. CE |
| **Total** | **6** | **10** | **130,415** | |

*Includes original language texts (Latin, Old English, Italian) alongside English translations.*

---

## Directory Structure

```
corpus/
├── classical/
│   ├── odyssey/          Homer's Odyssey
│   └── aeneid/           Virgil's Aeneid
├── medieval/
│   ├── beowulf/          Anonymous epic
│   ├── canterbury-tales/ Chaucer
│   └── inferno/          Dante's Inferno
├── early-modern/
│   └── tempest/          Shakespeare
└── modern/
    └── (reserved)
```

---

## Texts Included

### Classical (8th c. BCE – 1st c. BCE)

| Text | Author | Version | Lines | Source |
|------|--------|---------|-------|--------|
| Odyssey | Homer | Samuel Butler translation (1900) | 11,841 | Project Gutenberg |
| Aeneid | Virgil | **Latin original** | 10,396 | Project Gutenberg |
| Aeneid | Virgil | John Dryden translation (1697) | 14,447 | Project Gutenberg |

### Medieval (8th–14th c. CE)

| Text | Author | Version | Lines | Source |
|------|--------|---------|-------|--------|
| Beowulf | Anonymous | **Old English original** | 20,120 | Project Gutenberg |
| Beowulf | Anonymous | Francis Gummere translation (1910) | 6,565 | Project Gutenberg |
| Canterbury Tales | Geoffrey Chaucer | Middle English original | 36,321 | Project Gutenberg |
| Inferno | Dante Alighieri | **Italian original** | 6,613 | Project Gutenberg |
| Inferno | Dante Alighieri | Henry W. Longfellow translation (1867) | 19,983 | Project Gutenberg |

### Early Modern (17th c. CE)

| Text | Author | Version | Lines | Source |
|------|--------|---------|-------|--------|
| The Tempest | William Shakespeare | First Folio (1623) | 4,129 | Project Gutenberg |

---

## License

All texts are in the **public domain** in the United States.

- Works published before 1929 are public domain in the US
- Project Gutenberg texts are freely redistributable
- See individual directory READMEs for specific details

---

## Usage

These texts are included for:

1. **Tutorial examples** - Learn LingFrame with real literary texts
2. **Comparative analysis** - Study rhetorical evolution across eras
3. **Testing** - Validate analysis modules against known texts
4. **Research** - Explore computational approaches to literary analysis

---

## Adding Texts

To add new texts to the corpus:

1. Create appropriate directory under the relevant period
2. Use descriptive filenames (e.g., `english_translator.txt`, `original.txt`)
3. Add a README.md documenting source, license, and any preprocessing
4. Prefer plain text (.txt) format
5. Ensure the text is public domain or appropriately licensed

---

## Preprocessing Notes

Texts have been minimally processed:

- Gutenberg headers/footers removed
- Encoding normalized to UTF-8
- Line endings normalized
- No content modifications

Original formatting (line breaks, spacing) preserved where possible.
