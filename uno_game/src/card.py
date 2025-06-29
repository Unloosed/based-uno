from enum import Enum, auto
from typing import Optional


class Color(Enum):
    RED = auto()
    YELLOW = auto()
    GREEN = auto()
    BLUE = auto()
    WILD = auto()  # For Wild and Wild Draw Four

    def __str__(self):
        return self.name


class Rank(Enum):
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
    WILD = 13
    WILD_DRAW_FOUR = 14

    def __str__(self):
        if self.value < 10:
            return str(self.value)
        return self.name


class Card:
    def __init__(self, color: Color, rank: Rank):
        if not isinstance(color, Color):
            raise TypeError("Color must be an instance of Color Enum")
        if not isinstance(rank, Rank):
            raise TypeError("Rank must be an instance of Rank Enum")

        # Wild cards should have the color WILD
        if rank in [Rank.WILD, Rank.WILD_DRAW_FOUR]:
            if color != Color.WILD:
                # Automatically set color to WILD for these ranks if a specific color was provided
                color = Color.WILD
        # Non-wild cards should not have the color WILD
        elif color == Color.WILD and rank not in [Rank.WILD, Rank.WILD_DRAW_FOUR]:
            raise ValueError(f"Non-special rank {rank} cannot have color WILD")

        self.color = color
        self.rank = rank
        self.active_color = color  # For Wild cards, this will be set when played

    def __str__(self):
        if self.rank == Rank.WILD or self.rank == Rank.WILD_DRAW_FOUR:
            if self.active_color != Color.WILD:
                return f"WILD ({self.active_color.name})"
            return f"{self.rank.name}"  # e.g. WILD, WILD_DRAW_FOUR
        return f"{self.color.name} {self.rank}"

    def __repr__(self):
        return f"Card({self.color.name}, {self.rank.name})"

    def __eq__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.color == other.color and self.rank == other.rank

    def __hash__(self):
        return hash((self.color, self.rank))

    def is_special_action(self) -> bool:
        """Checks if the card is an action card (Skip, Reverse, Draw Two)."""
        return self.rank in [Rank.DRAW_TWO, Rank.SKIP, Rank.REVERSE]

    def is_wild(self) -> bool:
        """Checks if the card is a Wild or Wild Draw Four."""
        return self.rank in [Rank.WILD, Rank.WILD_DRAW_FOUR]

    def matches(
        self, other_card: "Card", current_color_chosen_for_wild: Optional[Color] = None
    ) -> bool:
        """
        Checks if this card can be played on top of other_card.
        current_color_chosen_for_wild is the color chosen if other_card is a Wild card.
        """
        if self.is_wild():  # Wild cards can be played on anything
            return True
        if other_card.is_wild():
            # If the other card is wild, this card must match the chosen active color
            return self.color == current_color_chosen_for_wild
        # Standard match: color or rank
        return self.color == other_card.color or self.rank == other_card.rank

    def to_dict(self):
        """Returns a dictionary representation of the card."""
        return {
            "color": self.color.name,
            "rank": self.rank.name,
            "value_str": str(self.rank), # For display like "7" or "SKIP"
            "active_color": self.active_color.name if self.active_color else self.color.name,
            "display_str": str(self),
        }


if __name__ == "__main__":
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
        Card("RED", Rank.SEVEN)  # type: ignore[arg-type]
    except TypeError as e:
        print(f"Error test for invalid color type: {e}")

    c1 = Card(Color.RED, Rank.ONE)
    c2 = Card(Color.RED, Rank.ONE)
    c3 = Card(Color.BLUE, Rank.ONE)
    card_set = {c1, c2, c3}
    print(f"Set of cards: {card_set}")  # Should contain 2 cards
    assert len(card_set) == 2

    print("Card class tests completed.")
