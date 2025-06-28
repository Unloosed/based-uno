"""
Defines the cards used in the Uno game.

This module includes enumerations for card colors and ranks, and a class
representing an individual card with its properties and behaviors, such as
matching rules.
"""

from enum import Enum, auto
from typing import Optional  # For type hinting


class Color(Enum):
    """Enumeration for card colors."""

    RED = auto()
    YELLOW = auto()
    GREEN = auto()
    BLUE = auto()
    WILD = auto()  # Represents the intrinsic color of Wild and Wild Draw Four cards

    def __str__(self) -> str:
        """Returns the string representation of the color (its name)."""
        return self.name


class Rank(Enum):
    """Enumeration for card ranks, including numbers and special actions."""

    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    DRAW_TWO = 10
    SKIP = 11
    REVERSE = 12
    WILD = 13  # Represents a standard Wild card
    WILD_DRAW_FOUR = 14

    def __str__(self) -> str:
        """Returns the string representation of the rank."""
        if self.value < 10:  # Numbered cards
            return str(self.value)
        return self.name  # Action cards (DRAW_TWO, SKIP, etc.)


class Card:
    """
    Represents a single Uno card.

    Attributes:
        color (Color): The intrinsic color of the card. For Wild cards, this is Color.WILD.
        rank (Rank): The rank of the card (e.g., SEVEN, SKIP, WILD_DRAW_FOUR).
        active_color (Color): The color chosen by a player when a Wild card is played.
                              For non-Wild cards, this is the same as `color`.
    """

    def __init__(self, color: Color, rank: Rank):
        """
        Initializes a Card.

        Args:
            color: The color of the card.
            rank: The rank of the card.

        Raises:
            TypeError: If color is not an instance of Color or rank is not an instance of Rank.
            ValueError: If a non-Wild rank is given Color.WILD.
        """
        if not isinstance(color, Color):
            raise TypeError("Color must be an instance of Color Enum")
        if not isinstance(rank, Rank):
            raise TypeError("Rank must be an instance of Rank Enum")

        # Wild cards must intrinsically have the color WILD.
        if rank in [Rank.WILD, Rank.WILD_DRAW_FOUR]:
            if color != Color.WILD:
                # Auto-correct to Color.WILD for Wild/Wild D4 ranks.
                color = Color.WILD
        # Non-wild cards cannot intrinsically have the color WILD.
        elif color == Color.WILD and rank not in [Rank.WILD, Rank.WILD_DRAW_FOUR]:
            raise ValueError(
                f"Non-special rank {rank.name} cannot have intrinsic color WILD"
            )

        self.color: Color = color
        self.rank: Rank = rank
        self.active_color: Color = (
            color  # Initially, active_color is the card's own color.
        )
        # For Wild cards, active_color will be updated when played and a color is chosen.

    def __str__(self) -> str:
        """Returns a user-friendly string representation of the card."""
        if self.rank in [Rank.WILD, Rank.WILD_DRAW_FOUR]:
            # If a Wild card has had a color chosen for it (i.e., it's on the discard pile)
            if self.active_color != Color.WILD:
                return f"WILD ({self.active_color.name})"
            return f"{self.rank.name}"  # e.g., "WILD", "WILD_DRAW_FOUR" if color not yet chosen
        return f"{self.color.name} {self.rank}"  # e.g., "RED SEVEN"

    def __repr__(self) -> str:
        """Returns a developer-friendly string representation of the card."""
        return f"Card(Color.{self.color.name}, Rank.{self.rank.name})"

    def __eq__(self, other: object) -> bool:
        """Checks if this card is equal to another card (based on color and rank)."""
        if not isinstance(other, Card):
            return NotImplemented
        # Note: active_color is not part of equality, as it represents a state of play,
        # not the intrinsic nature of the card itself. Two "Red Seven" cards are equal
        # regardless of game context. Two "Wild" cards are equal.
        return self.color == other.color and self.rank == other.rank

    def __hash__(self) -> int:
        """Returns a hash for the card, allowing cards to be used in sets/dictionary keys."""
        return hash((self.color, self.rank))

    def is_special_action(self) -> bool:
        """
        Checks if the card is a standard action card (Skip, Reverse, Draw Two).
        This does not include Wild cards.
        """
        return self.rank in [Rank.DRAW_TWO, Rank.SKIP, Rank.REVERSE]

    def is_wild(self) -> bool:
        """Checks if the card is a Wild or Wild Draw Four."""
        return self.rank in [Rank.WILD, Rank.WILD_DRAW_FOUR]

    def matches(
        self, other_card: "Card", current_color_chosen_for_wild: Optional[Color] = None
    ) -> bool:
        """
        Checks if this card (the one being played) can be played on top of `other_card`
        (the current top card on the discard pile).

        Args:
            other_card: The card currently on top of the discard pile.
            current_color_chosen_for_wild: If `other_card` is a Wild card, this is the
                                           color that was chosen for it.

        Returns:
            True if this card can be played, False otherwise.
        """
        if self.is_wild():  # A Wild card can be played on any card.
            return True

        if other_card.is_wild():
            # If the card on the table is a Wild card, this card (being played)
            # must match the color chosen for that Wild card.
            if current_color_chosen_for_wild is None:
                # This case should ideally be prevented by game logic ensuring a color is chosen
                # for a played Wild card before the next turn.
                raise ValueError(
                    "Cannot match against a Wild card without a chosen active color."
                )
            return self.color == current_color_chosen_for_wild

        # Standard Uno matching rules: color or rank must match.
        return self.color == other_card.color or self.rank == other_card.rank


if __name__ == "__main__":
    # Docstrings added, no functional change to __main__
    # Test basic card creation
    red_seven = Card(Color.RED, Rank.SEVEN)
    print(red_seven)

    blue_skip = Card(Color.BLUE, Rank.SKIP)
    print(blue_skip)

    wild_card = Card(Color.WILD, Rank.WILD)
    print(wild_card)
    wild_card.active_color = Color.GREEN  # Player chooses green
    print(wild_card)

    wild_d4 = Card(Color.WILD, Rank.WILD_DRAW_FOUR)
    print(wild_d4)

    # Test matching
    red_five = Card(Color.RED, Rank.FIVE)
    print(f"RED SEVEN matches RED FIVE? {red_seven.matches(red_five)}")  # True (color)
    blue_seven = Card(Color.BLUE, Rank.SEVEN)
    print(
        f"RED SEVEN matches BLUE SEVEN? {red_seven.matches(blue_seven)}"
    )  # True (rank)
    print(f"RED FIVE matches BLUE SEVEN? {red_five.matches(blue_seven)}")  # False

    # Test matching with wild
    wild_card_on_table = Card(Color.WILD, Rank.WILD)
    # wild_card_on_table.active_color = Color.BLUE # Imagine player chose BLUE for the wild
    print(
        f"RED FIVE matches WILD (active BLUE)? {red_five.matches(wild_card_on_table, Color.BLUE)}"
    )  # False
    blue_card = Card(Color.BLUE, Rank.ONE)
    print(
        f"BLUE ONE matches WILD (active BLUE)? {blue_card.matches(wild_card_on_table, Color.BLUE)}"
    )  # True

    # Test playing a wild card
    print(f"WILD card matches RED FIVE? {wild_card.matches(red_five)}")  # True

    # Test error conditions
    try:
        Card(Color.RED, Rank.WILD)  # Should correct to Color.WILD
        # This should not raise error, it auto-corrects
        card_auto_correct = Card(Color.RED, Rank.WILD)
        assert card_auto_correct.color == Color.WILD
        print("Auto-correction for Wild card color: PASS")
    except ValueError as e:
        print(f"Error test: {e}")  # Should not happen

    try:
        Card(Color.WILD, Rank.SEVEN)  # Should raise error
    except ValueError as e:
        print(f"Error test for non-wild rank with WILD color: {e}")

    try:
        Card("RED", Rank.SEVEN)
    except TypeError as e:
        print(f"Error test for invalid color type: {e}")

    c1 = Card(Color.RED, Rank.ONE)
    c2 = Card(Color.RED, Rank.ONE)
    c3 = Card(Color.BLUE, Rank.ONE)
    card_set = {c1, c2, c3}
    print(f"Set of cards: {card_set}")  # Should contain 2 cards
    assert len(card_set) == 2

    print("Card class tests completed.")
