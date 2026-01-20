"""
Domain profiles for specialized text analysis.

Domains provide:
- Custom sentiment lexicons
- Entity extraction patterns
- Domain-specific configuration

Available built-in domains:
- base: Generic patterns and lexicons
- military: Military memoir/narrative analysis
"""

from pathlib import Path

# Domain resource directories
DOMAINS_DIR = Path(__file__).parent
BASE_DOMAIN_DIR = DOMAINS_DIR / "base"
MILITARY_DOMAIN_DIR = DOMAINS_DIR / "military"

__all__ = [
    "DOMAINS_DIR",
    "BASE_DOMAIN_DIR",
    "MILITARY_DOMAIN_DIR",
]
