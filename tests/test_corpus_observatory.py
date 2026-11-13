"""Unit tests for corpus observatory index loading and collision prevention."""

from pathlib import Path
import pytest
import yaml

from app.components.corpus_observatory import load_corpus_index


def test_cross_tradition_metadata_isolation(tmp_path: Path):
    """Hermetic fixture with the same text ID under western and eastern traditions.

    Verifies that each entry loads with its own metadata (title, author, language,
    script, translations) and does not overwrite or collide with the other.
    """
    western_text_dir = tmp_path / "western" / "classical" / "flood_myth"
    western_text_dir.mkdir(parents=True)
    (western_text_dir / "text.txt").write_text("Western narrative text.")

    eastern_text_dir = tmp_path / "eastern" / "classical" / "flood_myth"
    eastern_text_dir.mkdir(parents=True)
    (eastern_text_dir / "text.txt").write_text("Eastern narrative text.")

    index_data = {
        "western": {
            "classical": {
                "flood_myth": {
                    "title": "Western Flood Tale",
                    "original_title": "Deucalion",
                    "author": "Ovidian Bard",
                    "original_language": "la",
                    "script": "latin",
                    "translations": ["english_dryden.txt"],
                }
            }
        },
        "eastern": {
            "classical": {
                "flood_myth": {
                    "title": "Eastern Flood Tale",
                    "original_title": "Gun-Yu",
                    "author": "Eastern Chronicler",
                    "original_language": "zh",
                    "script": "chinese",
                    "translations": ["english_legge.txt"],
                }
            }
        },
    }
    with open(tmp_path / "corpus_index.yaml", "w", encoding="utf-8") as f:
        yaml.dump(index_data, f)

    results = load_corpus_index(tmp_path)
    assert len(results) == 2

    res_by_tradition = {r["tradition"]: r for r in results}
    assert "Western" in res_by_tradition
    assert "Eastern" in res_by_tradition

    western_entry = res_by_tradition["Western"]
    eastern_entry = res_by_tradition["Eastern"]

    assert western_entry["id"] == "classical/flood_myth"
    assert western_entry["title"] == "Western Flood Tale"
    assert western_entry["original_title"] == "Deucalion"
    assert western_entry["author"] == "Ovidian Bard"
    assert western_entry["language"] == "la"
    assert western_entry["script"] == "latin"
    assert western_entry["translations"] == ["english_dryden.txt"]

    assert eastern_entry["id"] == "classical/flood_myth"
    assert eastern_entry["title"] == "Eastern Flood Tale"
    assert eastern_entry["original_title"] == "Gun-Yu"
    assert eastern_entry["author"] == "Eastern Chronicler"
    assert eastern_entry["language"] == "zh"
    assert eastern_entry["script"] == "chinese"
    assert eastern_entry["translations"] == ["english_legge.txt"]


def test_cross_period_metadata_isolation(tmp_path: Path):
    """Hermetic fixture with the same text ID under two different periods.

    Verifies that duplicate bare text IDs in different periods load their respective
    metadata without collision or leak.
    """
    antiquity_dir = tmp_path / "antiquity" / "creation_myth"
    antiquity_dir.mkdir(parents=True)
    (antiquity_dir / "text.txt").write_text("Antiquity poem.")

    medieval_dir = tmp_path / "medieval" / "creation_myth"
    medieval_dir.mkdir(parents=True)
    (medieval_dir / "text.txt").write_text("Medieval poem.")

    index_data = {
        "antiquity": {
            "creation_myth": {
                "title": "Cosmogony of the Ancients",
                "author": "Ancient Poet",
                "original_language": "akk",
                "script": "cuneiform",
            }
        },
        "medieval": {
            "creation_myth": {
                "title": "Genesis in the Middle Ages",
                "author": "Monastic Scribe",
                "original_language": "ang",
                "script": "latin",
            }
        },
    }
    with open(tmp_path / "corpus_index.yaml", "w", encoding="utf-8") as f:
        yaml.dump(index_data, f)

    results = load_corpus_index(tmp_path)
    assert len(results) == 2

    res_by_period = {r["period"]: r for r in results}
    assert "Antiquity" in res_by_period
    assert "Medieval" in res_by_period

    antiq_entry = res_by_period["Antiquity"]
    assert antiq_entry["title"] == "Cosmogony of the Ancients"
    assert antiq_entry["author"] == "Ancient Poet"
    assert antiq_entry["language"] == "akk"
    assert antiq_entry["script"] == "cuneiform"

    med_entry = res_by_period["Medieval"]
    assert med_entry["title"] == "Genesis in the Middle Ages"
    assert med_entry["author"] == "Monastic Scribe"
    assert med_entry["language"] == "ang"
    assert med_entry["script"] == "latin"


def test_bare_id_collision_prevention_on_unindexed_text(tmp_path: Path):
    """Negative test: duplicate bare text ID in metadata should not leak to unindexed text."""
    # We have an unindexed text in a third period with the same directory name
    other_dir = tmp_path / "renaissance" / "creation-myth"
    other_dir.mkdir(parents=True)
    (other_dir / "text.txt").write_text("Renaissance unindexed text.")

    index_data = {
        "antiquity": {
            "creation_myth": {
                "title": "Cosmogony of the Ancients",
                "author": "Ancient Poet",
                "original_language": "akk",
                "script": "cuneiform",
            }
        },
        "medieval": {
            "creation_myth": {
                "title": "Genesis in the Middle Ages",
                "author": "Monastic Scribe",
                "original_language": "ang",
                "script": "latin",
            }
        },
    }
    with open(tmp_path / "corpus_index.yaml", "w", encoding="utf-8") as f:
        yaml.dump(index_data, f)

    results = load_corpus_index(tmp_path)
    res_by_period = {r["period"]: r for r in results}

    assert "Renaissance" in res_by_period
    ren_entry = res_by_period["Renaissance"]
    # Should fall back to directory-based defaults, NOT leak from antiquity or medieval
    assert ren_entry["title"] == "Creation Myth"
    assert ren_entry["author"] == "Unknown"
    assert ren_entry["language"] == "en"
    assert ren_entry["script"] == "latin"


def test_legacy_flat_layout_fallback(tmp_path: Path):
    """Negative/fallback test: legacy flat-layout entries retain documented defaults/fallback."""
    flat_dir = tmp_path / "flat_period" / "single_work"
    flat_dir.mkdir(parents=True)
    (flat_dir / "text.txt").write_text("Flat work text.")

    # In legacy flat structure without period match in YAML, an unambiguous bare key resolves
    index_data = {
        "other_period": {
            "single_work": {
                "title": "Single Legacy Work",
                "author": "Solitary Author",
                "original_language": "de",
                "script": "latin",
            }
        }
    }
    with open(tmp_path / "corpus_index.yaml", "w", encoding="utf-8") as f:
        yaml.dump(index_data, f)

    results = load_corpus_index(tmp_path)
    assert len(results) == 1
    entry = results[0]
    assert entry["title"] == "Single Legacy Work"
    assert entry["author"] == "Solitary Author"
    assert entry["language"] == "de"
    assert entry["tradition"] is None


def test_real_corpus_loads_deterministically():
    """Positive test: existing repository corpus loads deterministically and preserves metadata."""
    texts = load_corpus_index()
    assert len(texts) >= 40

    # Ensure deterministic sort: tradition, period, title
    for i in range(len(texts) - 1):
        t1, t2 = texts[i], texts[i + 1]
        key1 = (t1.get("tradition") or "", t1["period"], t1["title"])
        key2 = (t2.get("tradition") or "", t2["period"], t2["title"])
        assert key1 <= key2

    # Check known items have correct metadata attached
    iliad = next((t for t in texts if t["id"] == "classical/iliad"), None)
    assert iliad is not None
    assert iliad["title"] == "The Iliad"
    assert iliad["author"] == "Homer"
    assert iliad["language"] == "grc"
    assert iliad["script"] == "greek"

    analects = next((t for t in texts if t["id"] == "chinese-classical/analects"), None)
    assert analects is not None
    assert analects["title"] == "The Analects"
    assert analects["language"] == "zh"
    assert analects["script"] == "chinese"
