from typing import List, Optional
from .card import Card, Color, Rank  # Assuming card.py is in the same directory


class Player:
    def __init__(self, name: str, player_type: str = "HUMAN"):
        self.name: str = name
        self.player_type: str = player_type  # HUMAN or CPU
        self.hand: List[Card] = []

        # Game-specific counters
        self.coins: int = 0
        self.shuffle_counters: int = 0
        self.lunar_mana: int = 0
        self.solar_mana: int = 0

        # Special Yellow 4 rule
        self.get_out_of_jail_yellow_4: Optional[Card] = None

    def add_card_to_hand(self, card: Card):
        """Adds a single card to the player's hand."""
        if not isinstance(card, Card):
            raise TypeError("Can only add Card objects to hand.")
        self.hand.append(card)

    def add_cards_to_hand(self, cards: List[Card]):
        """Adds multiple cards to the player's hand."""
        for card in cards:
            self.add_card_to_hand(
                card
            )  # Leverage the single card add for type checking

    def remove_card_from_hand(self, card_to_remove: Card) -> Optional[Card]:
        """
        Removes a specific card from the player's hand.
        Returns the card if found and removed, otherwise None.
        Need to be careful if player has multiple identical cards.
        This implementation removes the first encountered match.
        """
        try:
            self.hand.remove(card_to_remove)  # Relies on Card.__eq__
            return card_to_remove
        except ValueError:
            # Card not found in hand
            return None

    def play_card(self, card_index: int) -> Optional[Card]:
        """
        Plays a card from the player's hand by its index.
        Returns the card if the index is valid, otherwise None.
        """
        if 0 <= card_index < len(self.hand):
            return self.hand.pop(card_index)
        return None

    def has_card(self, card_to_check: Card) -> bool:
        """Checks if the player has a specific card in hand."""
        return card_to_check in self.hand

    def hand_size(self) -> int:
        """Returns the number of cards in the player's hand."""
        return len(self.hand)

    def is_hand_empty(self) -> bool:
        """Checks if the player's hand is empty."""
        return not self.hand

    def can_play_on(
        self, top_discard_card: Card, current_wild_color: Optional[Color]
    ) -> List[Card]:
        """
        Returns a list of playable cards from the hand given the top discard card
        and the active color if the top card is a Wild.
        """
        playable_cards = []
        for card in self.hand:
            if card.matches(top_discard_card, current_wild_color):
                playable_cards.append(card)
        return playable_cards

    def has_playable_card(
        self, top_discard_card: Card, current_wild_color: Optional[Color]
    ) -> bool:
        """Checks if the player has any card they can play."""
        return any(
            card.matches(top_discard_card, current_wild_color) for card in self.hand
        )

    def store_yellow_4_get_out_of_jail(self, card: Card):
        """Stores a Yellow 4 card for 'get out of jail free' pile."""
        if card.color == Color.YELLOW and card.rank == Rank.FOUR:
            if self.get_out_of_jail_yellow_4 is None:  # Rule: cannot be accumulated
                self.get_out_of_jail_yellow_4 = card
                return True
        return False

    def use_get_out_of_jail_card(self) -> Optional[Card]:
        """Uses the stored Yellow 4 card."""
        card = self.get_out_of_jail_yellow_4
        self.get_out_of_jail_yellow_4 = None
        return card

    def has_get_out_of_jail_card(self) -> bool:
        return self.get_out_of_jail_yellow_4 is not None

    def get_hand_display(self, show_indices: bool = True) -> str:
        """Returns a string representation of the player's hand."""
        if not self.hand:
            return "Hand is empty."
        display = []
        for i, card in enumerate(self.hand):
            if show_indices:
                display.append(f"{i}: {str(card)}")
            else:
                display.append(str(card))
        return ", ".join(display)

    def __str__(self):
        return f"Player {self.name} (Cards: {self.hand_size()}, Coins: {self.coins}, Shuffles: {self.shuffle_counters}, Lunar: {self.lunar_mana}, Solar: {self.solar_mana})"

    def __repr__(self):
        return f"Player(name='{self.name}')"


if __name__ == "__main__":
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
