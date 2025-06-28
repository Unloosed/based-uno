"""
Uno Game Package.

This package contains the core logic for the Uno game, including cards,
deck, players, and game mechanics.
"""

# Make key classes and enums available when importing the src package directly.
from .card import Card, Color, Rank
from .deck import Deck
from .player import Player
from .game import UnoGame

__all__ = ["Card", "Color", "Rank", "Deck", "Player", "UnoGame"]
