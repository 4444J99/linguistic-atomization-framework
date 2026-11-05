"""ARC4N Living Digital Canon tests.

Tests for:
- Rich glyph-seed metadata
- Syllabic cluster atomization
- Expanded natural drift / evolution
- Remix/recombination engine
- Seed text corpus registry
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from nexus_babel.schemas import GlyphSeed
from nexus_babel.services.evolution import EvolutionService
from nexus_babel.services.glyph_data import (
    get_future_seeds,
    get_historic_forms,
    get_phoneme_hint,
    get_thematic_tags,
    get_visual_mutations,
)
from nexus_babel.services.seed_corpus import SeedCorpusService
from nexus_babel.services.text_utils import (
    ATOM_LEVELS,
    atomize_glyphs_rich,
    atomize_text,
    atomize_text_rich,
    syllabify,
)


# ── Glyph-Seed Tests ─────────────────────────────────────────────


class TestGlyphSeedModel:
    def test_glyph_seed_creation(self):
        gs = GlyphSeed(
            character="A",
            unicode_name="LATIN CAPITAL LETTER A",
            phoneme_hint="/eɪ/",
            historic_forms=["Α", "א"],
            visual_mutations=["Λ", "@"],
            thematic_tags=["beginning", "alpha"],
            future_seeds=["∆", "Æ"],
            position=0,
        )
        assert gs.character == "A"
        assert gs.position == 0
        assert gs.phoneme_hint == "/eɪ/"
        assert len(gs.historic_forms) == 2

    def test_glyph_seed_validation_minimal(self):
        gs = GlyphSeed(character="x", unicode_name="LATIN SMALL LETTER X", position=5)
        assert gs.character == "x"
        assert gs.phoneme_hint is None
        assert gs.thematic_tags == []


class TestGlyphData:
    def test_phoneme_hint_lookup(self):
        assert get_phoneme_hint("A") == "/eɪ/"
        assert get_phoneme_hint("a") == "/æ/"
        assert get_phoneme_hint("!") is None

    def test_historic_forms(self):
        forms = get_historic_forms("A")
        assert "Α" in forms
        assert len(forms) >= 2

    def test_visual_mutations(self):
        muts = get_visual_mutations("A")
        assert "Λ" in muts

    def test_thematic_tags(self):
        tags = get_thematic_tags("A")
        assert "beginning" in tags
        assert "alpha" in tags

    def test_future_seeds(self):
        seeds = get_future_seeds("A")
        assert len(seeds) == 3
        assert all(isinstance(s, str) for s in seeds)

    def test_unknown_char_returns_empty(self):
        assert get_historic_forms("!") == []
        assert get_visual_mutations("!") == []
        assert get_thematic_tags("!") == []
        assert get_future_seeds("!") == []


class TestAtomizeGlyphsRich:
    def test_produces_glyph_seeds(self):
        glyphs = atomize_glyphs_rich("Hi")
        assert len(glyphs) == 2
        assert glyphs[0].character == "H"
        assert glyphs[1].character == "i"
        assert glyphs[0].position == 0
        assert glyphs[1].position == 1

    def test_rich_metadata_populated(self):
        glyphs = atomize_glyphs_rich("A")
        g = glyphs[0]
        assert g.unicode_name == "LATIN CAPITAL LETTER A"
        assert g.phoneme_hint is not None
        assert len(g.historic_forms) > 0
        assert len(g.thematic_tags) > 0

    def test_skips_whitespace(self):
        glyphs = atomize_glyphs_rich("a b")
        assert len(glyphs) == 2
        assert glyphs[0].character == "a"
        assert glyphs[1].character == "b"


# ── Syllable Tests ────────────────────────────────────────────────


class TestSyllabify:
    def test_simple_word(self):
        result = syllabify("hello")
        assert len(result) >= 2
        assert "".join(result) == "hello"

    def test_short_word(self):
        result = syllabify("at")
        assert result == ["at"]

    def test_single_char(self):
        result = syllabify("I")
        assert result == ["I"]

    def test_empty(self):
        result = syllabify("")
        assert result == []

    def test_preserves_all_chars(self):
        word = "beautiful"
        result = syllabify(word)
        assert "".join(result) == word
        assert len(result) >= 2


class TestAtomizeLevels:
    def test_atom_levels_constant(self):
        assert ATOM_LEVELS == ["glyph-seed", "syllable", "word", "sentence", "paragraph"]

    def test_atomize_text_includes_syllables(self):
        result = atomize_text("Hello world")
        assert "syllable" in result
        assert len(result["syllable"]) >= 2

    def test_atomize_text_all_five_levels(self):
        text = "First paragraph here.\n\nSecond paragraph now."
        result = atomize_text(text)
        for level in ATOM_LEVELS:
            assert level in result, f"Missing level: {level}"
            assert len(result[level]) > 0, f"Empty level: {level}"

    def test_atomize_text_rich_returns_glyph_objects(self):
        result = atomize_text_rich("Hi")
        assert isinstance(result["glyph-seed"], list)
        assert len(result["glyph-seed"]) == 2
        assert hasattr(result["glyph-seed"][0], "character")
        assert result["glyph-seed"][0].character == "H"


# ── Evolution Tests ───────────────────────────────────────────────


class TestExpandedNaturalDrift:
    def setup_method(self):
        self.evo = EvolutionService()

    def test_natural_map_expanded(self):
        assert len(self.evo.NATURAL_MAP) >= 25

    def test_original_entries_preserved(self):
        assert self.evo.NATURAL_MAP["th"] == "þ"
        assert self.evo.NATURAL_MAP["ae"] == "æ"
        assert self.evo.NATURAL_MAP["ph"] == "f"

    def test_latin_italian_shifts(self):
        assert self.evo.NATURAL_MAP["ct"] == "tt"
        assert self.evo.NATURAL_MAP["fl"] == "fi"

    def test_old_english_shifts(self):
        assert self.evo.NATURAL_MAP["sc"] == "sh"
        assert self.evo.NATURAL_MAP["kn"] == "n"

    def test_reverse_map_exists(self):
        assert len(self.evo.REVERSE_NATURAL_MAP) > 0
        assert self.evo.REVERSE_NATURAL_MAP["þ"] == "th"

    def test_natural_drift_applies_new_mappings(self):
        result = self.evo._apply_event("the knight wrote", "natural_drift", {"seed": 42})
        # "kn" -> "n", "wr" -> "r"
        assert "n" in result.output_text.lower()

    def test_drift_deterministic(self):
        r1 = self.evo._apply_event("the knight", "natural_drift", {"seed": 1})
        r2 = self.evo._apply_event("the knight", "natural_drift", {"seed": 1})
        assert r1.output_text == r2.output_text


class TestPhaseShiftAcceleration:
    def setup_method(self):
        self.evo = EvolutionService()

    def test_expansion_phase_default(self):
        result = self.evo._apply_event("hello world", "phase_shift", {"phase": "expansion", "seed": 0})
        assert "mythic" in result.output_text

    def test_acceleration_increases_intensity(self):
        slow = self.evo._apply_event("hello world foo bar baz", "phase_shift", {"phase": "expansion", "seed": 0, "acceleration": 1.0})
        fast = self.evo._apply_event("hello world foo bar baz", "phase_shift", {"phase": "expansion", "seed": 0, "acceleration": 3.0})
        # Higher acceleration = more mythic insertions = longer text
        assert len(fast.output_text) >= len(slow.output_text)

    def test_compression_removes_vowels(self):
        result = self.evo._apply_event("hello world", "phase_shift", {"phase": "compression", "seed": 0})
        vowel_count = sum(1 for c in result.output_text if c.lower() in "aeiou")
        original_vowels = sum(1 for c in "hello world" if c.lower() in "aeiou")
        assert vowel_count < original_vowels

    def test_rebirth_adds_songbirth(self):
        result = self.evo._apply_event("hello world", "phase_shift", {"phase": "rebirth", "seed": 0})
        assert "SONG-BIRTH" in result.output_text

    def test_acceleration_in_diff_summary(self):
        result = self.evo._apply_event("test", "phase_shift", {"phase": "expansion", "seed": 0, "acceleration": 2.5})
        assert "acceleration" in result.diff_summary


class TestRemixEventType:
    def setup_method(self):
        self.evo = EvolutionService()

    def test_remix_event_validated(self):
        payload = self.evo._validate_event_payload("remix", {"seed": 1, "strategy": "interleave"})
        assert payload["strategy"] == "interleave"
        assert payload["seed"] == 1

    def test_remix_event_applied(self):
        result = self.evo._apply_event("original", "remix", {"seed": 0, "strategy": "interleave", "remixed_text": "remixed content"})
        assert result.output_text == "remixed content"
        assert result.diff_summary["strategy"] == "interleave"


# ── Remix Service Tests ───────────────────────────────────────────


class TestRemixStrategies:
    def setup_method(self):
        from nexus_babel.services.remix import RemixService

        self.remix = RemixService(evolution_service=EvolutionService())

    def test_interleave(self):
        result = self.remix._interleave("one two three", "alpha beta gamma")
        words = result.split()
        assert "one" in words
        assert "alpha" in words
        # Interleaved: should alternate
        assert words[0] == "one"
        assert words[1] == "alpha"

    def test_thematic_blend_deterministic(self):
        import random

        rng1 = random.Random(42)
        rng2 = random.Random(42)
        r1 = self.remix._thematic_blend("Hello world. Foo bar.", "Alpha beta. Gamma delta.", rng1)
        r2 = self.remix._thematic_blend("Hello world. Foo bar.", "Alpha beta. Gamma delta.", rng2)
        assert r1 == r2

    def test_glyph_collide_produces_output(self):
        import random

        rng = random.Random(42)
        result = self.remix._glyph_collide("abcdef", "xyzabc", rng)
        assert len(result) > 0
        assert len(result) == 6

    def test_temporal_layer(self):
        import random

        rng = random.Random(42)
        result = self.remix._temporal_layer("Para one.\n\nPara two.", "Target one.\n\nTarget two.", rng)
        assert "Para one" in result


# ── Seed Corpus Tests ─────────────────────────────────────────────


class TestSeedCorpusService:
    def test_list_seed_texts(self, tmp_path: Path):
        service = SeedCorpusService(seeds_dir=tmp_path / "seeds")
        seeds = service.list_seed_texts()
        assert len(seeds) == 5
        titles = [s["title"] for s in seeds]
        assert "The Odyssey" in titles
        assert "Leaves of Grass" in titles
        assert all(s["atomization_status"] == "not_provisioned" for s in seeds)

    def test_list_shows_provisioned(self, tmp_path: Path):
        seeds_dir = tmp_path / "seeds"
        seeds_dir.mkdir(parents=True)
        (seeds_dir / "the_odyssey.txt").write_text("test content")
        service = SeedCorpusService(seeds_dir=seeds_dir)
        seeds = service.list_seed_texts()
        odyssey = next(s for s in seeds if s["title"] == "The Odyssey")
        assert odyssey["atomization_status"] == "provisioned"
        assert odyssey["local_path"] is not None

    def test_provision_unknown_title_raises(self, tmp_path: Path):
        service = SeedCorpusService(seeds_dir=tmp_path / "seeds")
        with pytest.raises(ValueError, match="Unknown seed text"):
            service.provision_seed_text("Nonexistent Book")

    def test_provision_downloads(self, tmp_path: Path):
        service = SeedCorpusService(seeds_dir=tmp_path / "seeds")
        with patch.object(service, "_download") as mock_dl:
            result = service.provision_seed_text("Leaves of Grass")
            assert result["status"] == "provisioned"
            assert mock_dl.called

    def test_provision_already_exists(self, tmp_path: Path):
        seeds_dir = tmp_path / "seeds"
        seeds_dir.mkdir(parents=True)
        (seeds_dir / "leaves_of_grass.txt").write_text("already here")
        service = SeedCorpusService(seeds_dir=seeds_dir)
        result = service.provision_seed_text("Leaves of Grass")
        assert result["status"] == "already_provisioned"


# ── API Integration Tests ─────────────────────────────────────────


class TestSeedCorpusAPI:
    def test_list_seeds_endpoint(self, client, auth_headers):
        resp = client.get("/api/v1/corpus/seeds", headers=auth_headers["viewer"])
        assert resp.status_code == 200
        data = resp.json()
        assert "seeds" in data
        assert len(data["seeds"]) == 5

    def test_list_seeds_requires_auth(self, client):
        resp = client.get("/api/v1/corpus/seeds")
        assert resp.status_code == 401


class TestRemixAPI:
    def test_remix_requires_auth(self, client):
        resp = client.post("/api/v1/remix", json={"strategy": "interleave"})
        assert resp.status_code == 401

    def test_remix_with_two_documents(self, client, auth_headers, sample_corpus):
        # Ingest two documents
        r1 = client.post(
            "/api/v1/ingest/batch",
            json={"source_paths": [str(sample_corpus["text"])]},
            headers=auth_headers["operator"],
        )
        assert r1.status_code == 200

        clean = sample_corpus["clean_yaml"]
        r2 = client.post(
            "/api/v1/ingest/batch",
            json={"source_paths": [str(clean)]},
            headers=auth_headers["operator"],
        )
        assert r2.status_code == 200

        # Get document IDs
        docs = client.get("/api/v1/documents", headers=auth_headers["viewer"]).json()["documents"]
        ingested = [d for d in docs if d["ingested"]]
        assert len(ingested) >= 2

        resp = client.post(
            "/api/v1/remix",
            json={
                "source_document_id": ingested[0]["id"],
                "target_document_id": ingested[1]["id"],
                "strategy": "interleave",
                "seed": 42,
            },
            headers=auth_headers["operator"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["strategy"] == "interleave"
        assert "new_branch_id" in data


class TestIngestWithRichAtoms:
    def test_ingest_creates_syllable_atoms(self, client, auth_headers, sample_corpus):
        resp = client.post(
            "/api/v1/ingest/batch",
            json={"source_paths": [str(sample_corpus["text"])]},
            headers=auth_headers["operator"],
        )
        assert resp.status_code == 200
        assert resp.json()["atoms_created"] > 0
