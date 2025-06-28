"""
Defines game actions and their types for the Uno game.

This module includes enumerations for different types of actions that can occur
during the game, such as playing a card, drawing cards, or special card effects.
It also defines a class to represent a game action with its associated parameters.
"""

from enum import Enum, auto
from typing import Optional, Union, Dict
from .card import Color  # Import Color for type hinting


# More specific type for GameAction.value where possible
GameActionValue = Union[None, int, Color, Dict[str, int]]


class ActionType(Enum):
    """
    Enumerates the types of actions that can occur in the game.

    Attributes:
        NEXT_PLAYER: Standard progression to the next player.
        REVERSE_DIRECTION: Reverses the order of play.
        SKIP_PLAYER: Skips the next player in turn.
        DRAW_CARDS: Forces a player (usually the next) to draw cards.
        CHOOSE_COLOR: Prompts the current player to choose a color (after playing a Wild).
        SWAP_CARD_RIGHT: Player swaps a card with the player to their right (Rank 7 effect).
        SWAP_CARD_ANY: Player swaps a card with any other player (Rank 0 effect).
        DISCARD_FROM_PLAYER_HAND: A player forces another to discard from their hand (Blue 3 effect).
        PLAYER_DRAWS_FOUR_UNLESS_LAST: Player who played Red 8 draws 4, unless it's their last card.
        PLAY_ANY_AND_DRAW_ONE: Player plays any card from hand, then draws one (Rank 6 effect).
        TAKE_RANDOM_FROM_PREVIOUS: Player takes a random card from the previous player (Green 5 effect).
        PLACE_TOP_DRAW_PILE_CARD: Top card from draw pile is played onto discard (Rank 9 effect).
        DISCARD_ALL_TWOS: Player who played a duplicate card discards all their '2' cards.
        GAME_WIN: Indicates a player has won the game.
        CONTINUE_TURN: Allows the current player to take another turn.
        NOP: No operation; signifies the end of a simple card play with no further effects.
    """

    # Standard game flow
    NEXT_PLAYER = auto()
    REVERSE_DIRECTION = auto()
    SKIP_PLAYER = auto()

    # Drawing cards
    DRAW_CARDS = auto()  # value = number of cards, target = next player by default

    # Wild card related
    CHOOSE_COLOR = auto()  # Player who played the wild needs to choose

    # Custom rules
    SWAP_CARD_RIGHT = auto()  # Player needs to choose card to give, and one to receive
    SWAP_CARD_ANY = (
        auto()
    )  # Player needs to choose card to give, target player, and card to receive
    DISCARD_FROM_PLAYER_HAND = auto()  # Target player (player to left) discards 2 cards from current player's hand (chosen by target)
    PLAYER_DRAWS_FOUR_UNLESS_LAST = (
        auto()
    )  # Player who played it draws 4, unless it's their last card
    PLAY_ANY_AND_DRAW_ONE = auto()  # Player plays any card, then draws one
    TAKE_RANDOM_FROM_PREVIOUS = auto()
    PLACE_TOP_DRAW_PILE_CARD = (
        auto()
    )  # Places draw pile's top card onto discard; its effect applies
    DISCARD_ALL_TWOS = auto()  # Player who played duplicate discards all their 2s.

    # Meta/Game state
    GAME_WIN = auto()
    CONTINUE_TURN = (
        auto()
    )  # For when a player gets to play again (e.g. after Rank 9 places a matching card)
    NOP = auto()  # No operation, simple turn pass after card play.


class GameAction:
    """
    Represents an action to be processed by the game logic.

    Attributes:
        type (ActionType): The type of the action.
        value (GameActionValue, optional): A value associated with the action, e.g., number of cards
                                           to draw, chosen color, or specific cards for a swap.
        target_player_offset (Optional[int], optional): The offset from the current player
                                                      to the target player of the action.
                                                      (e.g., 1 for next, -1 for previous, 0 for self).
        message_override (str, optional): An optional message to describe the action,
                                          which can override default messages.
    """

    def __init__(
        self,
        action_type: ActionType,
        value: GameActionValue = None,
        target_player_offset: Optional[int] = None,
        message: str = "",
    ):
        """
        Initializes a GameAction.

        Args:
            action_type: The type of the action.
            value: Value associated with the action (e.g., number of cards, chosen color, or dict for complex data).
            target_player_offset: Offset to the target player (e.g., 1 for next, -1 for previous).
            message: Optional custom message for the action.
        """
        self.type = action_type
        self.value = value
        self.target_player_offset = target_player_offset
        self.message_override = message

    def __repr__(self) -> str:
        """Returns a string representation of the GameAction."""
        return f"GameAction({self.type.name}, value={self.value}, target_offset={self.target_player_offset})"

    @staticmethod
    def card_played_message(player_name: str, card_str: str, uno_shouted: bool) -> str:
        """
        Generates a standard message for a card being played.

        Args:
            player_name: The name of the player who played the card.
            card_str: The string representation of the card played.
            uno_shouted: Boolean indicating if the player shouted "UNO!".

        Returns:
            A formatted string message.
        """
        msg = f"{player_name} played {card_str}."
        if uno_shouted:
            msg += f" {player_name} shouts UNO!"
        return msg


# Informational comments about design choices and future considerations related to actions:
# - Multi-step actions (like Rank 7 Swap) are initiated by a GameAction, and the game loop
#   manages subsequent player inputs or state changes.
# - The `_apply_card_effect` method (or similar in Game class) typically returns a list of
#   `GameAction` objects.
# - The `play_turn` method in the Game class processes these actions, handling immediate effects
#   and setting up for actions requiring further input.
# - Color counters (coins, mana, shuffles) are awarded directly within `play_turn` after a card
#   is successfully played, based on the card's intrinsic color. Wild cards do not grant
#   these specific color counters.
# - Shuffle counter mechanics for an empty draw pile are handled within the game's drawing logic
#   (e.g., a method like `_handle_draw_pile_empty`).
# This file previously ended with 'pass', which is removed as it's no longer needed.
