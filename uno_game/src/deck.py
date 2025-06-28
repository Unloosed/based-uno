import random
from typing import List, Optional
from .card import (
    Card,
    Color,
    Rank,
)  # Use absolute import based on common project structures


class Deck:
    def __init__(self, empty: bool = False):
        self.cards: List[Card] = []
        self.discard_pile: List[Card] = []
        if not empty:
            self.create_standard_deck()
            self.shuffle()

    def create_standard_deck(self):
        """
        Creates a standard Uno deck.
        - 19 of each color (Red, Yellow, Green, Blue): 1x Zero, 2x One-Nine
        - 8 Draw Two (2 of each color)
        - 8 Reverse (2 of each color)
        - 8 Skip (2 of each color)
        - 4 Wild cards
        - 4 Wild Draw Four cards
        Total: 108 cards
        """
        self.cards = []
        colors = [Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE]

        for color in colors:
            # One Zero card
            self.cards.append(Card(color, Rank.ZERO))
            # Two of each number card 1-9
            for i in range(1, 10):
                rank = Rank(i)
                self.cards.append(Card(color, rank))
                self.cards.append(Card(color, rank))
            # Two of each action card
            for rank_action in [Rank.DRAW_TWO, Rank.SKIP, Rank.REVERSE]:
                self.cards.append(Card(color, rank_action))
                self.cards.append(Card(color, rank_action))

        # Wild cards
        for _ in range(4):
            self.cards.append(Card(Color.WILD, Rank.WILD))
            self.cards.append(Card(Color.WILD, Rank.WILD_DRAW_FOUR))

        # print(f"Deck created with {len(self.cards)} cards.") # For debugging

    def shuffle(self):
        """Shuffles the main draw pile."""
        random.shuffle(self.cards)

    def draw_card(self) -> Optional[Card]:
        """Draws a card from the top of the deck."""
        if not self.cards:
            return None  # Or raise an exception, or handle reshuffling here
        return self.cards.pop()

    def add_to_discard(self, card: Card):
        """Adds a card to the top of the discard pile."""
        if not isinstance(card, Card):
            raise TypeError("Can only add Card objects to discard pile.")
        self.discard_pile.append(card)

    def get_top_discard_card(self) -> Optional[Card]:
        """Returns the top card of the discard pile without removing it."""
        if not self.discard_pile:
            return None
        return self.discard_pile[-1]

    def is_empty(self) -> bool:
        """Checks if the draw pile is empty."""
        return not self.cards

    def needs_reshuffle(self) -> bool:
        """Checks if the draw pile is empty and the discard pile has cards."""
        return self.is_empty() and bool(self.discard_pile)

    def reshuffle_discard_pile_into_deck(self, keep_top_card: bool = True) -> bool:
        """
        Reshuffles the discard pile (except the top card, usually) into the draw pile.
        Returns True if reshuffle happened, False otherwise.
        """
        if not self.discard_pile:
            return False

        top_card = None
        if keep_top_card and self.discard_pile:
            top_card = self.discard_pile.pop()  # Keep the current top card on discard

        self.cards.extend(self.discard_pile)
        self.discard_pile = []
        if top_card:
            self.discard_pile.append(top_card)  # Put the top card back

        self.shuffle()
        # print(f"Reshuffled. Draw pile: {len(self.cards)}, Discard pile: {len(self.discard_pile)}")
        return True

    def __len__(self):
        """Returns the number of cards in the draw pile."""
        return len(self.cards)


if __name__ == "__main__":
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
        deck.add_to_discard("not a card")  # type: ignore[arg-type]
    except TypeError as e:
        print(f"Error adding non-card to discard: {e}")

    print("Deck class tests completed.")
