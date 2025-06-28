from enum import Enum, auto
from typing import Optional, Any


class ActionType(Enum):
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
    def __init__(
        self,
        action_type: ActionType,
        value: Any = None,
        target_player_offset: Optional[int] = None,
        message: str = "",
    ):
        self.type = action_type
        self.value = value  # e.g., number of cards to draw, chosen color, specific cards for swap
        self.target_player_offset = target_player_offset  # e.g., 1 for next player, -1 for previous, 0 for current
        self.message_override = (
            message  # Optional message to use instead of a default one
        )

    def __repr__(self):
        return f"GameAction({self.type.name}, value={self.value}, target_offset={self.target_player_offset})"

    @staticmethod
    def card_played_message(player_name: str, card_str: str, uno_shouted: bool):
        msg = f"{player_name} played {card_str}."
        if uno_shouted:
            msg += f" {player_name} shouts UNO!"
        return msg


# Example of how this might be used:
# if card.rank == Rank.DRAW_TWO:
# return [GameAction(ActionType.DRAW_CARDS, value=2, target_player_offset=1), GameAction(ActionType.SKIP_PLAYER, target_player_offset=1)]
# if card.rank == Rank.WILD:
# return [GameAction(ActionType.CHOOSE_COLOR)] # This would likely be a preliminary action before other effects

# For Rank 7 (Swap with right):
# This will be complex as it requires multiple steps of player input.
# 1. Initial play of 7: Game notes SWAP_CARD_RIGHT is pending.
# 2. Game prompts current player: "Choose a card from your hand to give."
# 3. Game prompts current player: "Choose a card from player X's hand to take." (Player X is to the right)
# Or, if non-interactive, these choices are made randomly/strategically.

# For now, when _apply_card_effect sees a Rank 7, it will simply return GameAction(ActionType.SWAP_CARD_RIGHT).
# The main game loop will then need a handler for SWAP_CARD_RIGHT that contains the logic for these choices.
# This makes _apply_card_effect a dispatcher for effects rather than an executor of all of them.
# The play_turn method will then interpret these actions.
# Some actions are immediate (like REVERSE_DIRECTION), others set up next step (like CHOOSE_COLOR or SWAP_CARD_RIGHT).
# Some actions might target the *next* player (DRAW_CARDS, SKIP_PLAYER).
# play_turn returns a list of messages and potentially a "next_state" for the game if it needs more input.
# Or, play_turn itself becomes a state machine.
# Let's make play_turn handle the immediate consequences and setup for multi-step actions.
# _apply_card_effect will return a list of GameAction objects.
# play_turn will iterate through them.
# If an action requires more input (like choosing a card for swap), play_turn might return a special status
# indicating more input is needed from the same player.

# Color counters will also be handled. When a card is played, its color increments a counter for the player.
# This can be done directly in play_turn after a card is successfully played.
# Yellow -- 1 coin
# Green -- 1 shuffle
# Blue -- 1 lunar mana
# Red -- 1 solar mana
# These are awarded to the player who *played* the card.
# Wild cards, when played, do not award these specific color counters, as their played color is chosen
# and isn't one of the four basic elements. If a Wild is played and (e.g.) BLUE is chosen,
# it does not grant lunar mana. Only naturally Blue cards grant lunar mana.
# This needs to be clarified if my assumption is wrong. Assuming it's for playing R,Y,G,B non-Wild cards.

# Let's confirm: Does playing a "Wild, chosen Blue" count for Blue mana?
# For now, I'll assume NO: only intrinsic Red, Yellow, Green, Blue cards grant their respective counters.
# The rules state "Each color played adds a counter", which could imply the chosen color of a Wild.
# User clarified: "The color triangle does not have any other gameplay effect." - this doesn't directly answer the Wild counter question.
# "Color Elements: Fire-water-grass triangle... Yellow is neutral. Each color played adds a counter"
# This suggests the *actual color on the card face*. So a Wild card (which is Color.WILD) would not grant these.
# I will proceed with this assumption: Wilds do not grant these specific R,Y,G,B counters.
# The "Yellow 4" get out of jail free pile is separate.

# Shuffle counter mechanic:
# "If the draw pile is empty and a player needs to draw a card, they must use a shuffle counter
# to shuffle the discard pile into a new draw pile. If they don't have a shuffle counter,
# they can't draw and must skip their turn... If no one has shuffle counters and the draw pile is empty,
# the player who needs to draw skips their turn."
# This will be integrated into `_handle_draw_pile_empty`.
pass  # Placeholder for actual file content creation using the tool
