"""
MIDI Engine - Production-ready MIDI generation with zero dependencies

A framework-agnostic MIDI generation package with:
- Zero-dependency SMF writer
- Music theory helpers
- Pattern generators for ambient/sad music
- Clean APIs for web integration
"""

__version__ = "1.0.0"
__author__ = "MIDI Engine"

from .api import create_ambient_midi

__all__ = ["create_ambient_midi"]
