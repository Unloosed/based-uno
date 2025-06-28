"""
Represents a player in the Uno game.

This module defines the Player class, which manages a player's hand,
game-specific counters (like coins, mana), and actions related to their cards.
"""

from typing import List, Optional
from .card import Card, Color, Rank


class Player:
    """
    Represents a player in the Uno game.

    Each player has a name, a hand of cards, and various counters for
    game-specific mechanics (e.g., coins, mana, shuffle tokens).

    Attributes:
        name (str): The name of the player.
        hand (List[Card]): A list of Card objects representing the player's hand.
        coins (int): Number of coins the player has (Yellow card resource).
        shuffle_counters (int): Number of shuffle tokens (Green card resource).
        lunar_mana (int): Amount of lunar mana (Blue card resource).
        solar_mana (int): Amount of solar mana (Red card resource).
        get_out_of_jail_yellow_4 (Optional[Card]): Stores a Yellow 4 card if the player
                                                   has one set aside for the "get out of jail free" rule.
    """

    def __init__(self, name: str):
        """
        Initializes a Player.

        Args:
            name: The name of the player.
        """
        self.name: str = name
        self.hand: List[Card] = []

        # Game-specific counters
        self.coins: int = 0
        self.shuffle_counters: int = 0
        self.lunar_mana: int = 0
        self.solar_mana: int = 0

        # Special Yellow 4 rule storage
        self.get_out_of_jail_yellow_4: Optional[Card] = None

    def add_card_to_hand(self, card: Card) -> None:
        """
        Adds a single card to the player's hand.

        Args:
            card: The Card object to add.

        Raises:
            TypeError: If the provided item is not a Card instance.
        """
        if not isinstance(card, Card):
            raise TypeError("Can only add Card objects to hand.")
        self.hand.append(card)

    def add_cards_to_hand(self, cards: List[Card]) -> None:
        """
        Adds multiple cards to the player's hand.

        Args:
            cards: A list of Card objects to add.
        """
        for card in cards:
            self.add_card_to_hand(card)  # Leverages single add for type checking

    def remove_card_from_hand(self, card_to_remove: Card) -> Optional[Card]:
        """
        Removes a specific card object from the player's hand.

        This method removes the first occurrence of the card if duplicates exist.
        It relies on the `Card.__eq__` method for matching.

        Args:
            card_to_remove: The Card object to remove from the hand.

        Returns:
            The Card object if found and removed, otherwise None.
        """
        try:
            self.hand.remove(card_to_remove)
            return card_to_remove
        except ValueError:  # Card not found in hand
            return None

    def play_card(self, card_index: int) -> Optional[Card]:
        """
        Removes and returns a card from the player's hand by its index.

        This simulates playing a card.

        Args:
            card_index: The index of the card in the hand to play.

        Returns:
            The Card object if the index is valid, otherwise None.
        """
        if 0 <= card_index < len(self.hand):
            return self.hand.pop(card_index)
        return None

    def has_card(self, card_to_check: Card) -> bool:
        """Checks if the player has a specific card instance in their hand."""
        return card_to_check in self.hand

    def hand_size(self) -> int:
        """Returns the number of cards currently in the player's hand."""
        return len(self.hand)

    def is_hand_empty(self) -> bool:
        """Checks if the player's hand is empty."""
        return not self.hand

    def can_play_on(
        self, top_discard_card: Card, current_wild_color: Optional[Color]
    ) -> List[Card]:
        """
        Determines which cards in the player's hand are playable on the given top discard card.

        Args:
            top_discard_card: The card currently on top of the discard pile.
            current_wild_color: The active color if `top_discard_card` is a Wild card.

        Returns:
            A list of Card objects from the player's hand that can be legally played.
        """
        playable_cards = []
        for card_in_hand in self.hand:
            if card_in_hand.matches(top_discard_card, current_wild_color):
                playable_cards.append(card_in_hand)
        return playable_cards

    def has_playable_card(
        self, top_discard_card: Card, current_wild_color: Optional[Color]
    ) -> bool:
        """
        Checks if the player has at least one card in their hand that can be
        played on the given top discard card.

        Args:
            top_discard_card: The card currently on top of the discard pile.
            current_wild_color: The active color if `top_discard_card` is a Wild card.

        Returns:
            True if the player has a playable card, False otherwise.
        """
        return any(
            card_in_hand.matches(top_discard_card, current_wild_color)
            for card_in_hand in self.hand
        )

    def store_yellow_4_get_out_of_jail(self, card: Card) -> bool:
        """
        Stores a Yellow 4 card for the 'get out of jail free' pile.

        According to the custom rule, a player can store one Yellow 4 card.
        This card is removed from their hand and held separately.

        Args:
            card: The Yellow 4 card to store.

        Returns:
            True if the card was successfully stored, False otherwise (e.g., if it's not
            a Yellow 4, or if a card is already stored).
        """
        if card.color == Color.YELLOW and card.rank == Rank.FOUR:
            if self.get_out_of_jail_yellow_4 is None:  # Rule: cannot be accumulated
                self.get_out_of_jail_yellow_4 = card
                # Note: The card should also be removed from the player's main hand by game logic
                # if this method is called after confirming the play.
                return True
        return False

    def use_get_out_of_jail_card(self) -> Optional[Card]:
        """
        Uses the stored Yellow 4 'get out of jail free' card.

        The card is removed from storage. It's up to the game logic to handle
        its effect (e.g., playing it).

        Returns:
            The stored Yellow 4 Card if one was present, otherwise None.
        """
        card_to_use = self.get_out_of_jail_yellow_4
        self.get_out_of_jail_yellow_4 = None
        return card_to_use

    def has_get_out_of_jail_card(self) -> bool:
        """Checks if the player has a Yellow 4 card stored for 'get out of jail free'."""
        return self.get_out_of_jail_yellow_4 is not None

    def get_hand_display(self, show_indices: bool = True) -> str:
        """
        Returns a string representation of the player's hand, optionally with indices.

        Args:
            show_indices: If True, prefixes each card with its index in the hand.

        Returns:
            A comma-separated string of cards in hand, or "Hand is empty."
        """
        if not self.hand:
            return "Hand is empty."
        display_parts = []
        for i, card_in_hand in enumerate(self.hand):
            if show_indices:
                display_parts.append(f"{i}: {str(card_in_hand)}")
            else:
                display_parts.append(str(card_in_hand))
        return ", ".join(display_parts)

    def __str__(self) -> str:
        """Returns a string summary of the player's status."""
        return (
            f"Player {self.name} (Cards: {self.hand_size()}, "
            f"Coins: {self.coins}, Shuffles: {self.shuffle_counters}, "
            f"Lunar: {self.lunar_mana}, Solar: {self.solar_mana})"
        )

    def __repr__(self) -> str:
        """Returns a developer-friendly representation of the Player object."""
        return f"Player(name='{self.name}')"


if __name__ == "__main__":
    # Docstrings added, no functional change to __main__
    player1 = Player("Alice")
    print(player1)

    # Test adding cards
    red_1 = Card(Color.RED, Rank.ONE)
    blue_2 = Card(Color.BLUE, Rank.TWO)
    red_1_dup = Card(Color.RED, Rank.ONE)  # Duplicate for testing removal

    player1.add_card_to_hand(red_1)
    player1.add_cards_to_hand([blue_2, red_1_dup])
    print(f"{player1.name}'s hand: {player1.get_hand_display()}")
    assert player1.hand_size() == 3

    # Test removing card
    removed = player1.remove_card_from_hand(red_1)
    print(f"Removed: {removed}")
    assert removed == red_1
    assert player1.hand_size() == 2
    print(f"{player1.name}'s hand after removing RED ONE: {player1.get_hand_display()}")

    # Test removing card not in hand
    green_5 = Card(Color.GREEN, Rank.FIVE)
    removed_none = player1.remove_card_from_hand(green_5)
    assert removed_none is None
    assert player1.hand_size() == 2

    # Test playing card by index
    # Hand should be [BLUE TWO, RED ONE]
    played_card = player1.play_card(0)  # Play BLUE TWO
    assert played_card == blue_2
    assert player1.hand_size() == 1
    print(f"{player1.name}'s hand after playing by index: {player1.get_hand_display()}")

    played_invalid = player1.play_card(5)  # Invalid index
    assert played_invalid is None
    assert player1.hand_size() == 1

    # Test can_play_on / has_playable_card
    # Hand: [RED ONE]
    player1.add_card_to_hand(
        Card(Color.BLUE, Rank.SEVEN)
    )  # Hand: [RED ONE, BLUE SEVEN]
    print(f"{player1.name}'s hand: {player1.get_hand_display()}")

    top_discard_red_5 = Card(Color.RED, Rank.FIVE)
    playable = player1.can_play_on(top_discard_red_5, None)
    print(f"Playable on RED FIVE: {[str(c) for c in playable]}")  # Should be RED ONE
    assert any(c.color == Color.RED and c.rank == Rank.ONE for c in playable)
    assert player1.has_playable_card(top_discard_red_5, None)

    top_discard_yellow_7 = Card(Color.YELLOW, Rank.SEVEN)
    playable = player1.can_play_on(top_discard_yellow_7, None)
    print(
        f"Playable on YELLOW SEVEN: {[str(c) for c in playable]}"
    )  # Should be BLUE SEVEN
    assert any(c.color == Color.BLUE and c.rank == Rank.SEVEN for c in playable)
    assert player1.has_playable_card(top_discard_yellow_7, None)

    top_discard_green_skip = Card(Color.GREEN, Rank.SKIP)
    playable = player1.can_play_on(top_discard_green_skip, None)  # Should be none
    print(f"Playable on GREEN SKIP: {[str(c) for c in playable]}")
    assert not player1.has_playable_card(top_discard_green_skip, None)

    # Test with Wild card on table
    wild_on_table = Card(Color.WILD, Rank.WILD)
    # wild_on_table.active_color = Color.BLUE # Player chose blue
    playable_on_wild_blue = player1.can_play_on(wild_on_table, Color.BLUE)
    print(
        f"Playable on WILD (active BLUE): {[str(c) for c in playable_on_wild_blue]}"
    )  # BLUE SEVEN
    assert any(
        c.color == Color.BLUE and c.rank == Rank.SEVEN for c in playable_on_wild_blue
    )

    # Test Yellow 4 "get out of jail"
    yellow_4_card = Card(Color.YELLOW, Rank.FOUR)
    not_yellow_4 = Card(Color.RED, Rank.FOUR)

    assert not player1.has_get_out_of_jail_card()
    stored_y4 = player1.store_yellow_4_get_out_of_jail(yellow_4_card)
    assert stored_y4
    assert player1.has_get_out_of_jail_card()
    assert player1.get_out_of_jail_yellow_4 == yellow_4_card

    # Try storing another one (should not accumulate)
    another_y4 = Card(Color.YELLOW, Rank.FOUR)
    stored_another_y4 = player1.store_yellow_4_get_out_of_jail(another_y4)
    assert not stored_another_y4  # Cannot store if one already exists
    assert player1.get_out_of_jail_yellow_4 == yellow_4_card  # Original one still there

    stored_not_y4 = player1.store_yellow_4_get_out_of_jail(not_yellow_4)
    assert not stored_not_y4

    used_y4 = player1.use_get_out_of_jail_card()
    assert used_y4 == yellow_4_card
    assert not player1.has_get_out_of_jail_card()
    assert player1.get_out_of_jail_yellow_4 is None

    print("Player class tests completed.")
