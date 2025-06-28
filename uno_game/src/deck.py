"""
Manages the Uno deck, including the draw pile and discard pile.

This module provides functionality to create, shuffle, draw from, and manage
the cards in an Uno game deck.
"""

import random
from typing import List, Optional
from .card import Card, Color, Rank


class Deck:
    """
    Represents the game deck in Uno.

    This includes both the main draw pile and the discard pile.
    It handles operations like shuffling, drawing cards, adding to discard,
    and reshuffling the discard pile back into the draw pile when needed.

    Attributes:
        cards (List[Card]): The list of cards in the draw pile.
        discard_pile (List[Card]): The list of cards in the discard pile.
    """

    def __init__(self, empty: bool = False):
        """
        Initializes the Deck.

        Args:
            empty (bool): If True, creates an empty deck without standard cards.
                          Defaults to False, creating and shuffling a standard Uno deck.
        """
        self.cards: List[Card] = []
        self.discard_pile: List[Card] = []
        if not empty:
            self.create_standard_deck()
            self.shuffle()

    def create_standard_deck(self) -> None:
        """
        Populates the deck with a standard set of 108 Uno cards.

        A standard Uno deck consists of:
        - Four colors (Red, Yellow, Green, Blue).
        - For each color:
            - One '0' card.
            - Two each of '1' through '9' cards.
            - Two 'Skip' cards.
            - Two 'Reverse' cards.
            - Two 'Draw Two' cards.
        - Four 'Wild' cards (colorless).
        - Four 'Wild Draw Four' cards (colorless).
        """
        self.cards = []
        colors = [Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE]

        for color in colors:
            # One Zero card
            self.cards.append(Card(color, Rank.ZERO))
            # Two of each number card 1-9
            for i in range(1, 10):  # Ranks 1 through 9
                rank_enum = Rank(i)  # Convert integer to Rank enum member
                self.cards.append(Card(color, rank_enum))
                self.cards.append(Card(color, rank_enum))
            # Two of each action card (Draw Two, Skip, Reverse)
            for rank_action_enum in [Rank.DRAW_TWO, Rank.SKIP, Rank.REVERSE]:
                self.cards.append(Card(color, rank_action_enum))
                self.cards.append(Card(color, rank_action_enum))

        # Wild cards (Color.WILD is their intrinsic color)
        for _ in range(4):
            self.cards.append(Card(Color.WILD, Rank.WILD))
            self.cards.append(Card(Color.WILD, Rank.WILD_DRAW_FOUR))

    def shuffle(self) -> None:
        """Shuffles the cards in the main draw pile."""
        random.shuffle(self.cards)

    def draw_card(self) -> Optional[Card]:
        """
        Draws a card from the top of the draw pile.

        Returns:
            The card drawn from the deck, or None if the draw pile is empty.
        """
        if not self.cards:
            return None
        return self.cards.pop()

    def add_to_discard(self, card: Card) -> None:
        """
        Adds a card to the top of the discard pile.

        Args:
            card: The card to add to the discard pile.

        Raises:
            TypeError: If the item to add is not a Card object.
        """
        if not isinstance(card, Card):
            raise TypeError("Can only add Card objects to discard pile.")
        self.discard_pile.append(card)

    def get_top_discard_card(self) -> Optional[Card]:
        """
        Returns the card on top of the discard pile without removing it.

        Returns:
            The top card of the discard pile, or None if the pile is empty.
        """
        if not self.discard_pile:
            return None
        return self.discard_pile[-1]

    def is_empty(self) -> bool:
        """Checks if the draw pile is empty."""
        return not self.cards

    def needs_reshuffle(self) -> bool:
        """
        Checks if the draw pile is empty and there are cards in the discard pile
        that can be used for reshuffling.
        """
        return self.is_empty() and bool(self.discard_pile)

    def reshuffle_discard_pile_into_deck(self, keep_top_card: bool = True) -> bool:
        """
        Reshuffles the discard pile (optionally keeping its top card) into the draw pile.

        The discard pile is emptied (or left with its top card), its contents are
        added to the draw pile, and then the draw pile is shuffled.

        Args:
            keep_top_card (bool): If True, the current top card of the discard pile
                                  is preserved and remains on the discard pile.
                                  Defaults to True.

        Returns:
            True if a reshuffle occurred, False otherwise (e.g., if discard pile was empty).
        """
        if not self.discard_pile:
            return False  # Cannot reshuffle an empty discard pile

        top_card_to_keep: Optional[Card] = None
        if keep_top_card and self.discard_pile:
            top_card_to_keep = self.discard_pile.pop()  # Remove top to save it

        # Add the rest of the discard pile to the main deck
        self.cards.extend(self.discard_pile)
        self.discard_pile = []  # Clear the discard pile

        if top_card_to_keep:
            self.discard_pile.append(top_card_to_keep)  # Put the saved top card back

        self.shuffle()
        return True

    def __len__(self) -> int:
        """Returns the number of cards currently in the draw pile."""
        return len(self.cards)


if __name__ == "__main__":
    # Docstrings added, no functional change to __main__
    deck = Deck()
    print(f"Initial deck size: {len(deck)}")

    # Test drawing cards
    drawn_cards = []
    for _ in range(10):
        card = deck.draw_card()
        if card:
            drawn_cards.append(card)
            deck.add_to_discard(card)  # Add drawn card to discard
        else:
            print("Deck is empty!")
            break

    print(f"Drawn cards: {[str(c) for c in drawn_cards]}")
    print(f"Deck size after drawing 10: {len(deck)}")
    print(f"Discard pile size: {len(deck.discard_pile)}")
    print(f"Top discard: {deck.get_top_discard_card()}")

    # Test reshuffle
    # Draw all cards to force a reshuffle scenario
    while not deck.is_empty():
        card = deck.draw_card()
        if card:
            deck.add_to_discard(card)  # Simulate playing cards

    print(f"Deck empty. Draw pile: {len(deck)}, Discard pile: {len(deck.discard_pile)}")

    if deck.needs_reshuffle():
        print("Deck needs reshuffle.")
        # Simulate drawing when empty - game logic would handle this
        # For now, manually trigger reshuffle
        if deck.reshuffle_discard_pile_into_deck():
            print("Reshuffle successful.")
        else:
            print("Reshuffle failed (no cards in discard).")

    print(f"Deck size after reshuffle: {len(deck)}")
    print(f"Discard pile size after reshuffle: {len(deck.discard_pile)}")  # Should be 1
    if deck.discard_pile:
        print(f"Top discard after reshuffle: {str(deck.get_top_discard_card())}")

    # Test drawing again
    card = deck.draw_card()
    print(f"Drew one more card: {card}")
    print(f"Deck size: {len(deck)}")

    # Test creating an empty deck
    empty_deck = Deck(empty=True)
    print(f"Empty deck size: {len(empty_deck)}")
    print(f"Empty deck discard size: {len(empty_deck.discard_pile)}")
    card = empty_deck.draw_card()
    assert card is None
    print("Empty deck tests completed.")

    # Verify deck composition (simple check for total cards)
    full_deck = Deck()
    assert len(full_deck) == 108, f"Expected 108 cards, got {len(full_deck)}"
    print("Deck composition count check: PASS")

    # Test adding non-card to discard
    try:
        deck.add_to_discard("not a card")
    except TypeError as e:
        print(f"Error adding non-card to discard: {e}")

    print("Deck class tests completed.")
