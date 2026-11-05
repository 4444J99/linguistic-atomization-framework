"""Static lookup tables for glyph-seed metadata.

Deterministic data — no ML dependencies. Covers Latin alphabet plus
common Unicode characters encountered in literary texts.
"""

from __future__ import annotations

# IPA phoneme approximations for Latin letters
PHONEME_HINTS: dict[str, str] = {
    "A": "/eɪ/", "a": "/æ/",
    "B": "/biː/", "b": "/b/",
    "C": "/siː/", "c": "/k/",
    "D": "/diː/", "d": "/d/",
    "E": "/iː/", "e": "/ɛ/",
    "F": "/ɛf/", "f": "/f/",
    "G": "/dʒiː/", "g": "/ɡ/",
    "H": "/eɪtʃ/", "h": "/h/",
    "I": "/aɪ/", "i": "/ɪ/",
    "J": "/dʒeɪ/", "j": "/dʒ/",
    "K": "/keɪ/", "k": "/k/",
    "L": "/ɛl/", "l": "/l/",
    "M": "/ɛm/", "m": "/m/",
    "N": "/ɛn/", "n": "/n/",
    "O": "/oʊ/", "o": "/ɒ/",
    "P": "/piː/", "p": "/p/",
    "Q": "/kjuː/", "q": "/kw/",
    "R": "/ɑːr/", "r": "/r/",
    "S": "/ɛs/", "s": "/s/",
    "T": "/tiː/", "t": "/t/",
    "U": "/juː/", "u": "/ʌ/",
    "V": "/viː/", "v": "/v/",
    "W": "/ˈdʌbəljuː/", "w": "/w/",
    "X": "/ɛks/", "x": "/ks/",
    "Y": "/waɪ/", "y": "/j/",
    "Z": "/zɛd/", "z": "/z/",
}

# Historic script forms (ancestor glyphs)
HISTORIC_FORMS: dict[str, list[str]] = {
    "A": ["Α", "א", "𐤀"],       # Greek Alpha, Hebrew Aleph, Phoenician Aleph
    "B": ["Β", "ב", "𐤁"],       # Greek Beta, Hebrew Bet, Phoenician Bet
    "C": ["Γ", "ג", "𐤂"],       # Greek Gamma, Hebrew Gimel, Phoenician Gimel
    "D": ["Δ", "ד", "𐤃"],       # Greek Delta, Hebrew Dalet, Phoenician Dalet
    "E": ["Ε", "ה", "𐤄"],       # Greek Epsilon, Hebrew He, Phoenician He
    "F": ["Ϝ", "ו"],             # Greek Digamma, Hebrew Vav
    "G": ["Γ", "ג"],             # Greek Gamma, Hebrew Gimel
    "H": ["Η", "ח", "𐤇"],       # Greek Eta, Hebrew Het, Phoenician Het
    "I": ["Ι", "י", "𐤉"],       # Greek Iota, Hebrew Yod, Phoenician Yod
    "J": ["Ι", "י"],             # Late Latin from I
    "K": ["Κ", "כ", "𐤊"],       # Greek Kappa, Hebrew Kaf, Phoenician Kaf
    "L": ["Λ", "ל", "𐤋"],       # Greek Lambda, Hebrew Lamed, Phoenician Lamed
    "M": ["Μ", "מ", "𐤌"],       # Greek Mu, Hebrew Mem, Phoenician Mem
    "N": ["Ν", "נ", "𐤍"],       # Greek Nu, Hebrew Nun, Phoenician Nun
    "O": ["Ο", "ע", "𐤏"],       # Greek Omicron, Hebrew Ayin, Phoenician Ayin
    "P": ["Π", "פ", "𐤐"],       # Greek Pi, Hebrew Pe, Phoenician Pe
    "Q": ["Ϙ", "ק", "𐤒"],       # Greek Qoppa, Hebrew Qof, Phoenician Qof
    "R": ["Ρ", "ר", "𐤓"],       # Greek Rho, Hebrew Resh, Phoenician Resh
    "S": ["Σ", "ש", "𐤔"],       # Greek Sigma, Hebrew Shin, Phoenician Shin
    "T": ["Τ", "ת", "𐤕"],       # Greek Tau, Hebrew Tav, Phoenician Tav
    "U": ["Υ", "ו"],             # Greek Upsilon, Hebrew Vav
    "V": ["Υ", "ו"],             # From Latin U
    "W": ["Ƿ"],                  # Old English Wynn
    "X": ["Ξ", "Χ"],             # Greek Xi/Chi
    "Y": ["Υ", "ו"],             # Greek Upsilon
    "Z": ["Ζ", "ז", "𐤆"],       # Greek Zeta, Hebrew Zayin, Phoenician Zayin
}

# Visual/typographic mutations
VISUAL_MUTATIONS: dict[str, list[str]] = {
    "A": ["Λ", "@", "4", "Δ"],
    "B": ["ß", "8", "β"],
    "C": ["(", "¢", "©"],
    "D": ["Ð", "đ"],
    "E": ["3", "€", "ε"],
    "F": ["ƒ"],
    "G": ["9", "ğ"],
    "H": ["#", "ħ"],
    "I": ["|", "!", "1"],
    "J": ["ĵ"],
    "K": ["κ"],
    "L": ["1", "ℓ"],
    "M": ["ℳ"],
    "N": ["ñ", "η"],
    "O": ["0", "θ", "Ω"],
    "P": ["ρ"],
    "Q": ["9"],
    "R": ["®"],
    "S": ["$", "5", "§"],
    "T": ["+", "†", "7"],
    "U": ["µ", "∪"],
    "V": ["√"],
    "W": ["ω", "ψ"],
    "X": ["×", "χ"],
    "Y": ["¥", "γ"],
    "Z": ["2", "ζ"],
}

# Thematic/symbolic associations
THEMATIC_TAGS: dict[str, list[str]] = {
    "A": ["beginning", "alpha", "apex", "air", "ascent"],
    "B": ["boundary", "body", "birth", "base"],
    "C": ["curve", "containment", "cycle", "crescent"],
    "D": ["door", "division", "descent", "dawn"],
    "E": ["energy", "expansion", "echo", "east"],
    "F": ["fire", "flux", "force", "form"],
    "G": ["ground", "gravity", "growth", "gate"],
    "H": ["horizon", "height", "home", "harmony"],
    "I": ["identity", "individuality", "intention", "illumination"],
    "J": ["journey", "junction", "joy"],
    "K": ["key", "knowledge", "kinship"],
    "L": ["light", "line", "language", "law"],
    "M": ["mother", "mountain", "mystery", "memory"],
    "N": ["night", "north", "nature", "negation"],
    "O": ["origin", "orbit", "omega", "ocean", "ouroboros"],
    "P": ["power", "path", "pattern", "prism"],
    "Q": ["question", "quest", "queen"],
    "R": ["river", "return", "rhythm", "root"],
    "S": ["serpent", "spiral", "silence", "seed", "sun"],
    "T": ["time", "tower", "threshold", "truth"],
    "U": ["unity", "universe", "underground", "upward"],
    "V": ["voice", "valley", "vessel", "void"],
    "W": ["water", "wave", "wisdom", "wind"],
    "X": ["crossing", "unknown", "transformation"],
    "Y": ["yearning", "yield", "youth"],
    "Z": ["zenith", "zero", "zone"],
}

# Extended glyph pool for future-seed evolution targets
GLYPH_POOL = [
    "∆", "Æ", "Ω", "§", "☲", "⟁",
    "Ψ", "Φ", "Θ", "Ξ", "Σ", "Π",
    "☰", "☱", "☳", "☴", "☵", "☶", "☷",
    "ᚠ", "ᚢ", "ᚦ", "ᚨ", "ᚱ", "ᚲ",
]


def get_phoneme_hint(char: str) -> str | None:
    return PHONEME_HINTS.get(char)


def get_historic_forms(char: str) -> list[str]:
    return HISTORIC_FORMS.get(char.upper(), [])


def get_visual_mutations(char: str) -> list[str]:
    return VISUAL_MUTATIONS.get(char.upper(), [])


def get_thematic_tags(char: str) -> list[str]:
    return THEMATIC_TAGS.get(char.upper(), [])


def get_future_seeds(char: str) -> list[str]:
    """Return potential evolution targets from the glyph pool."""
    upper = char.upper()
    if upper not in THEMATIC_TAGS:
        return []
    idx = ord(upper) - ord("A")
    if idx < 0 or idx >= 26:
        return []
    pool_start = idx % len(GLYPH_POOL)
    return [GLYPH_POOL[(pool_start + i) % len(GLYPH_POOL)] for i in range(3)]
