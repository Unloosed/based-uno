"""
Core game logic for the Uno card game.

This module defines the `UnoGame` class, which orchestrates the game flow,
manages players, the deck, card plays, and special card effects according
to standard and custom Uno rules.
"""

from typing import List, Optional, Tuple, Dict, Any  # Added Dict, Any
import random

from .card import Card, Color, Rank
from .deck import Deck
from .player import Player
from .actions import ActionType, GameAction


class UnoGame:
    """
    Manages the state and logic of an Uno game session.

    This class handles game setup, player turns, card playing, effects,
    and determining the winner. It incorporates standard Uno rules along with
    custom rules defined for this version of the game (e.g., color counters,
    special card effects for specific ranks/colors).

    Attributes:
        deck (Deck): The game deck, including draw and discard piles.
        players (List[Player]): A list of Player objects participating in the game.
        initial_hand_size (int): The number of cards dealt to each player at the start.
        current_player_index (int): Index of the current player in the `players` list.
        game_over (bool): Flag indicating if the game has ended.
        winner (Optional[Player]): The Player object who won the game, if any.
        play_direction (int): Direction of play (1 for forward, -1 for reverse).
        current_wild_color (Optional[Color]): The color chosen when a Wild card is active.
        pending_action (Optional[GameAction]): Stores an action that requires further
                                               player input (e.g., choosing a color for a Wild,
                                               selecting cards for a swap).
        action_data (Dict[str, Any]): Stores auxiliary data needed to complete a pending_action.
    """

    def __init__(self, player_names: List[str], initial_hand_size: int = 7):
        """
        Initializes an UnoGame session.

        Args:
            player_names: A list of names for the players.
            initial_hand_size: The number of cards to deal to each player initially.

        Raises:
            ValueError: If the number of players is not between 2 and 4,
                        or if initial_hand_size is not positive.
        """
        if (
            not 2 <= len(player_names) <= 4
        ):  # Standard Uno typically supports more, but this impl limits to 2-4
            raise ValueError("UnoGame current implementation requires 2 to 4 players.")
        if initial_hand_size <= 0:
            raise ValueError("Initial hand size must be a positive integer.")

        self.deck: Deck = Deck()
        self.players: List[Player] = [Player(name) for name in player_names]
        self.initial_hand_size: int = initial_hand_size

        self.current_player_index: int = 0
        self.game_over: bool = False
        self.winner: Optional[Player] = None
        self.play_direction: int = 1  # 1 for normal (clockwise), -1 for reverse

        self.current_wild_color: Optional[Color] = (
            None  # Active color if top card is Wild
        )
        self.pending_action: Optional[GameAction] = None  # For multi-step actions
        self.action_data: Dict[str, Any] = {}  # Data for pending_action

        self._setup_game()

    def _setup_game(self) -> None:
        """
        Sets up the initial state of the game.

        This includes:
        - Dealing initial hands to all players.
        - Drawing the first card for the discard pile (ensuring it's not a Wild Draw Four).
        - Randomly selecting the starting player.
        - Handling the case where the first discard card is a Wild (randomly choosing its color).
        - Printing a warning if the first card has an immediate action (as full effect handling
          on the first player is simplified in this setup).

        Raises:
            RuntimeError: If the deck runs out of cards during setup.
        """
        # Deal initial hands
        for _ in range(self.initial_hand_size):
            for player in self.players:
                card = self.deck.draw_card()
                if card:
                    player.add_card_to_hand(card)
                else:
                    # This should ideally not happen with a standard deck and hand size
                    raise RuntimeError("Deck ran out of cards during initial deal.")

        # Draw the first card for the discard pile
        first_discard = self.deck.draw_card()
        # Wild Draw Four cannot be the starting card. If drawn, re-add and reshuffle.
        while first_discard is None or first_discard.rank == Rank.WILD_DRAW_FOUR:
            if first_discard:  # Was Wild Draw Four
                self.deck.cards.append(first_discard)  # Put it back in draw pile
                self.deck.shuffle()
            first_discard = self.deck.draw_card()
            if first_discard is None and self.deck.needs_reshuffle():
                self.deck.reshuffle_discard_pile_into_deck(keep_top_card=False)
                first_discard = self.deck.draw_card()
            elif first_discard is None:  # Still no card after potential reshuffle
                raise RuntimeError(
                    "Deck ran out of cards while setting up discard pile."
                )

        self.deck.add_to_discard(first_discard)
        self.current_wild_color = None  # Reset, will be set if first_discard is Wild

        # Randomly select starting player
        self.current_player_index = random.randint(0, len(self.players) - 1)

        # Handle if the first card is a Wild card
        if first_discard.is_wild():
            # For simplicity, system randomly chooses a color for the starting Wild.
            # In a real game, the first player (or dealer) might choose.
            chosen_color = random.choice([c for c in Color if c != Color.WILD])
            self.current_wild_color = chosen_color
            first_discard.active_color = (
                chosen_color  # Set active color on the card itself
            )
            print(
                f"Game starts with a Wild card ({first_discard}). System chose {chosen_color.name} as the active color."
            )

        # Note on starting with action cards (Draw Two, Skip, Reverse):
        # Standard Uno rules often have these affect the first player.
        # This implementation currently prints a warning as full effect application
        # at this stage is not implemented. A more robust setup might pre-process these.
        if (
            first_discard.rank in [Rank.DRAW_TWO, Rank.SKIP, Rank.REVERSE]
            and not first_discard.is_wild()  # Standard action cards, not Wilds
        ):
            print(
                f"Warning: Game started with an action card: {first_discard}. "
                f"Its effect on the first player ({self.get_current_player().name}) "
                "is not fully enacted by this setup logic."
            )

    def get_current_player(self) -> Player:
        """Returns the Player object whose current turn it is."""
        return self.players[self.current_player_index]

    def get_top_card(self) -> Optional[Card]:
        """
        Returns the card currently on top of the discard pile.

        Returns:
            The top Card object, or None if the discard pile is empty.
        """
        return self.deck.get_top_discard_card()

    def _get_player_at_offset(self, base_player_idx: int, offset: int) -> Player:
        """
        Calculates the index of a player relative to a base player,
        considering the current play direction and wrapping around the player list.

        Args:
            base_player_idx: The index of the player from which to calculate the offset.
            offset: The offset from the base player. For game actions, this offset
                    is typically directional (e.g., 1 for the next player in the
                    current `play_direction`, -1 for the previous).

        Returns:
            The Player object at the calculated offset.
        """
        # The offset for GameActions (like DRAW_CARDS, SKIP_PLAYER) is usually
        # relative to the flow of play (e.g., 1 means the *next* player in sequence).
        # So, if play_direction is -1 (reverse), an offset of 1 still means the
        # player who would be "next" in that reversed sequence.
        # This method assumes `offset` is already directional if needed, or that
        # `play_direction` will be multiplied with it by the caller if `offset`
        # is meant to be absolute (e.g. 1 always means clockwise next).
        # For GameAction.target_player_offset, it usually means "next in turn order".
        # Let's clarify: if offset is 1, it's the *next* player.
        # If play_direction is 1 (forward), next is base_player_idx + 1.
        # If play_direction is -1 (reverse), next is base_player_idx - 1.
        # So, target_idx = (base_player_idx + offset * self.play_direction ...
        # However, GameAction.target_player_offset seems to be defined as "1 for next player".
        # The current usage in _get_card_actions for DRAW_CARDS, SKIP uses offset=1,
        # and play_turn multiplies by self.play_direction before calling this.
        # So, this function should just use the raw offset.
        num_players = len(self.players)
        target_idx = (base_player_idx + offset + num_players) % num_players
        return self.players[target_idx]

    def _advance_turn_marker(self, steps: int = 1) -> None:
        """
        Advances the current player index according to the play direction.

        Args:
            steps (int): The number of steps/players to advance. Defaults to 1.
                         Used for Skip effects (steps=1 for skipping one player, effectively
                         advancing the marker by 2 if we consider the current player's turn ends
                         and then one more is skipped).
                         However, typically this is called to advance by one logical turn.
                         If a skip action occurs, it's often handled by calling this twice,
                         or by passing steps=2. Let's assume steps=1 means "move to next player".
                         If a skip occurs, the game logic might call this, then call it again.
                         Or, if ActionType.SKIP_PLAYER implies advancing by `steps` *additional* players.
                         The current `play_turn` calls this with `steps=1` after a normal turn,
                         and again with `steps=1` if a skip flag is set. This seems correct.
        """
        num_players = len(self.players)
        self.current_player_index = (
            self.current_player_index + (self.play_direction * steps) + num_players
        ) % num_players
        # Added num_players before modulo to handle negative results correctly.

    def _handle_draw_pile_empty(self, drawing_player: Player) -> bool:
        """
        Manages the situation when a player needs to draw a card but the draw pile is empty.

        If the discard pile can be reshuffled:
        - If `drawing_player` has shuffle counters, one is used, and the discard pile
          is reshuffled into the draw pile.
        - If `drawing_player` has no shuffle counters, they cannot draw and effectively
          skip the draw.
        If the draw pile is empty and cannot be reshuffled (e.g., discard pile also empty),
        the player cannot draw.

        Args:
            drawing_player: The player attempting to draw.

        Returns:
            True if the player can draw a card (either from existing pile or after
            successful reshuffle), False otherwise.
        """
        if self.deck.needs_reshuffle():  # Draw pile empty, discard pile has cards
            if drawing_player.shuffle_counters > 0:
                drawing_player.shuffle_counters -= 1
                print(
                    f"{drawing_player.name} uses a shuffle counter ({drawing_player.shuffle_counters} remaining). Reshuffling discard pile..."
                )
                self.deck.reshuffle_discard_pile_into_deck()  # Standard reshuffle keeps top discard
                if (
                    self.deck.is_empty()
                ):  # Still empty after reshuffle (e.g. only 1 card was in discard)
                    print("Draw pile is still empty after reshuffle. No cards to draw.")
                    return False  # Cannot draw
                return True  # Can draw now
            else:  # No shuffle counters
                print(
                    f"{drawing_player.name} needs to draw, draw pile empty, but has no shuffle counters. Draw is skipped."
                )
                return False  # Cannot draw
        elif (
            self.deck.is_empty()
        ):  # Draw pile empty, and discard pile also empty (or cannot be reshuffled)
            print(
                "Draw pile is empty and no cards in discard to reshuffle. No cards to draw."
            )
            return False  # Cannot draw
        return True  # Draw pile has cards

    def player_draws_card(self, player: Player, count: int = 1) -> List[Card]:
        """
        Facilitates a player drawing a specified number of cards from the deck.

        Handles draw pile empty scenarios using `_handle_draw_pile_empty`.
        Adds drawn cards to the player's hand.

        Args:
            player: The Player who is drawing cards.
            count: The number of cards to draw. Defaults to 1.

        Returns:
            A list of Card objects that were successfully drawn and added to the hand.
            This list may be empty if no cards could be drawn.
        """
        drawn_cards: List[Card] = []
        for _ in range(count):  # Corrected loop variable from i to _
            can_draw_this_card = self._handle_draw_pile_empty(player)
            if not can_draw_this_card:
                break  # Stop trying to draw if conditions prevent it

            card = self.deck.draw_card()
            if card:
                player.add_card_to_hand(card)
                drawn_cards.append(card)
            else:
                # This case should ideally be covered by _handle_draw_pile_empty,
                # but as a safeguard:
                print(
                    f"Warning: {player.name} tried to draw, but no card was available even after checks."
                )
                break  # Should not happen if _handle_draw_pile_empty is correct
        return drawn_cards

    def _get_card_actions(
        self,
        card: Card,
        playing_player: Player,
        chosen_color_for_wild: Optional[Color] = None,
    ) -> List[GameAction]:
        """
        Determines the list of game actions triggered by playing a specific card.

        This method translates a card play into a sequence of `GameAction` objects
        that the game loop will process. It handles both standard Uno card effects
        (Skip, Reverse, Draw Two, Wilds) and custom effects defined for this game
        (e.g., effects for specific Ranks like 0, 3 (Blue), 5 (Green), 6, 7, 8 (Red), 9).

        Args:
            card: The Card object that was played.
            playing_player: The Player who played the card.
            chosen_color_for_wild: If `card` is a Wild card, this is the color
                                   chosen by `playing_player`. If None, a
                                   `CHOOSE_COLOR` action will be generated.

        Returns:
            A list of `GameAction` objects representing the effects of the played card.
            Returns a list containing a single `NOP` (No Operation) action if the card
            has no special effect beyond being played.
        """
        actions: List[GameAction] = []
        player_name = playing_player.name
        player_idx = self.players.index(
            playing_player
        )  # Base index for relative targets

        # --- Custom Card Effects ---
        # These typically override standard Uno actions for the card.
        # Note: The order of these checks might matter if a card could theoretically
        # match multiple custom rules (though current design avoids this).

        if card.rank == Rank.SEVEN:  # Swap card with player to the right
            actions.append(
                GameAction(
                    ActionType.SWAP_CARD_RIGHT,
                    message=f"{player_name} plays {card}, triggering card swap with player to their right.",
                )
            )
        elif card.rank == Rank.ZERO:  # Swap card with any player
            actions.append(
                GameAction(
                    ActionType.SWAP_CARD_ANY,
                    message=f"{player_name} plays {card}, triggering card swap with any chosen player.",
                )
            )
        elif (
            card.color == Color.BLUE and card.rank == Rank.THREE
        ):  # Player to left discards from Blue3-player's hand
            actions.append(
                GameAction(
                    ActionType.DISCARD_FROM_PLAYER_HAND,
                    # Target for this action is the player to the *left* of who played Blue 3.
                    # Offset is relative to Blue3 player. If play_direction=1 (forward), left is -1.
                    # If play_direction=-1 (reverse), left is +1. So, -self.play_direction.
                    target_player_offset=-self.play_direction,
                    value={
                        "count": 2,  # Number of cards to make victim choose
                        "from_player_idx": player_idx,  # Index of player whose hand cards are taken from (Blue3 player)
                    },
                    message=f"{player_name} plays {card}. Player to their left must choose 2 cards from {player_name}'s hand to discard.",
                )
            )
        elif (
            card.color == Color.RED and card.rank == Rank.EIGHT
        ):  # Player draws 4 unless it's their last card
            # The hand size check is for the player who played the Red 8, *after* it's played.
            # If playing_player.hand_size() > 0 at the point of action processing, it means Red 8 was not their last.
            # This check will be done in play_turn when processing PLAYER_DRAWS_FOUR_UNLESS_LAST.
            # Here, we just generate the action type.
            # The message is also conditional and handled in play_turn.
            actions.append(
                GameAction(
                    ActionType.PLAYER_DRAWS_FOUR_UNLESS_LAST,
                    target_player_offset=0,  # Target is self (the player who played Red 8)
                )
            )
        elif card.rank == Rank.SIX:  # Play any card from hand, then draw one
            actions.append(
                GameAction(
                    ActionType.PLAY_ANY_AND_DRAW_ONE,
                    target_player_offset=0,  # Action is for the current player
                    message=f"{player_name} plays {card}. They can play any card next, then must draw one.",
                )
            )
        elif (
            card.color == Color.GREEN and card.rank == Rank.FIVE
        ):  # Take random card from previous player
            actions.append(
                GameAction(
                    ActionType.TAKE_RANDOM_FROM_PREVIOUS,
                    # Target is previous player. Offset is -1 relative to current play direction.
                    target_player_offset=-self.play_direction,  # Corrected: was missing self.play_direction
                    message=f"{player_name} plays {card} and attempts to take a random card from the previous player.",
                )
            )
        elif card.rank == Rank.NINE:  # Place top card from draw pile onto discard pile
            actions.append(
                GameAction(
                    ActionType.PLACE_TOP_DRAW_PILE_CARD,
                    message=f"{player_name} plays {card}. Top card from draw pile will be revealed and played.",
                )
            )
        # Note: DISCARD_ALL_TWOS (for duplicate Rank 2 play) is handled directly in `play_turn`
        # as it depends on the state of the discard pile *before* the current card's actions.

        # --- Standard Uno Actions (if no custom effect took precedence) ---
        # Check if any custom action (other than NOP or CHOOSE_COLOR placeholder) was added.
        # CHOOSE_COLOR is often a precursor to other Wild effects, so it doesn't count as "handled" here.
        is_custom_effect_primary = any(
            a.type not in [ActionType.NOP, ActionType.CHOOSE_COLOR] for a in actions
        )

        if not is_custom_effect_primary:
            if card.is_wild():
                # If chosen_color_for_wild is already provided (e.g., by AI or UI for the wild play),
                # it's passed as `action.value`. Otherwise, `value` is None, signaling need for input.
                actions.append(
                    GameAction(
                        ActionType.CHOOSE_COLOR,
                        value=chosen_color_for_wild,  # This will be None if color not yet chosen
                        message_override=(
                            f"{player_name} chose {chosen_color_for_wild.name}."
                            if chosen_color_for_wild
                            else "Wild card played, color choice needed."
                        ),
                    )
                )
                if card.rank == Rank.WILD_DRAW_FOUR:
                    actions.append(
                        GameAction(
                            ActionType.DRAW_CARDS,
                            value=4,
                            target_player_offset=1,  # Next player in turn order
                            message="Next player draws 4 cards",  # Simplified message
                        )
                    )
                    actions.append(
                        GameAction(
                            ActionType.SKIP_PLAYER,
                            target_player_offset=1,  # Next player in turn order
                            message="and is skipped.",  # Appends to previous message
                        )
                    )
            elif card.rank == Rank.DRAW_TWO:
                actions.append(
                    GameAction(
                        ActionType.DRAW_CARDS,
                        value=2,
                        target_player_offset=1,
                        message="Next player draws 2 cards",
                    )
                )
                actions.append(
                    GameAction(
                        ActionType.SKIP_PLAYER,
                        target_player_offset=1,
                        message="and is skipped.",
                    )
                )
            elif card.rank == Rank.SKIP:
                actions.append(
                    GameAction(
                        ActionType.SKIP_PLAYER,
                        target_player_offset=1,
                        message="Next player is skipped.",
                    )
                )
            elif card.rank == Rank.REVERSE:
                actions.append(
                    GameAction(
                        ActionType.REVERSE_DIRECTION, message="Play direction reversed."
                    )
                )
                if (
                    len(self.players) == 2
                ):  # In a 2-player game, Reverse acts like a Skip
                    actions.append(
                        GameAction(
                            ActionType.SKIP_PLAYER,
                            target_player_offset=0,  # The "next" player is effectively the current player again (who gets skipped)
                            message="In a 2-player game, Reverse acts like a Skip.",
                        )
                    )

        # If no actions were generated by custom or standard rules, it's a simple play.
        if not actions:
            actions.append(
                GameAction(ActionType.NOP, message="")
            )  # Signifies turn ends after this play.

        return actions

    def _award_color_counters(self, player: Player, card: Card) -> None:
        """
        Awards color-specific counters to a player based on the card they played.

        This is called after a card is successfully played.
        - Red card: +1 Solar Mana
        - Yellow card: +1 Coin. If Yellow 4, special storage rule applies.
        - Green card: +1 Shuffle Counter
        - Blue card: +1 Lunar Mana
        Wild cards (intrinsic Color.WILD) do not award these specific counters,
        even if a color is chosen for them.

        Args:
            player: The player who played the card.
            card: The card that was played.
        """
        if card.is_wild():  # Wild cards themselves don't grant R,Y,G,B counters
            return

        if card.color == Color.RED:
            player.solar_mana += 1
            print(f"{player.name} gained 1 Solar Mana (Total: {player.solar_mana}).")
        elif card.color == Color.YELLOW:
            player.coins += 1
            print(f"{player.name} gained 1 Coin (Total: {player.coins}).")
            # The logic for storing a Yellow 4 is handled in `play_turn` after this,
            # as it involves the specific played card and player choice/confirmation.
            # This method purely awards the resource for the color.
        elif card.color == Color.GREEN:
            player.shuffle_counters += 1
            print(
                f"{player.name} gained 1 Shuffle Counter (Total: {player.shuffle_counters})."
            )
        elif card.color == Color.BLUE:
            player.lunar_mana += 1
            print(f"{player.name} gained 1 Lunar Mana (Total: {player.lunar_mana}).")

    def play_turn(
        self,
        player: Player,
        card_index: Optional[int],
        action_input: Optional[Dict[str, Any]] = None,  # Type hint for action_input
        chosen_color_for_wild: Optional[Color] = None,
    ) -> Tuple[bool, str, Optional[ActionType]]:
        """
        Processes a single player's turn or a segment of a multi-step action.

        This is the main entry point for game progression. It handles:
        1.  Validating if it's the correct player's turn or if they are acting on a pending action.
        2.  Processing pending multi-step actions (like swaps, choosing colors) if any.
        3.  If no pending action, attempting to play a card from the player's hand.
            - Validates if the card is playable.
            - Adds the card to the discard pile.
            - Handles special rule for duplicate Rank 2 plays (discard all 2s).
            - Awards color counters.
            - Gets actions resulting from the played card.
        4.  Processing the list of actions generated by the card play or pending action resolution.
            - Updates game state (e.g., draw cards, skip players, reverse direction, win game).
            - Sets up new pending actions if the played card initiates one.
        5.  Advancing the turn to the next player unless an action prevents it (e.g., player
            gets another turn due to Rank 9, or a pending action requires more input from
            the same or another player).

        Args:
            player: The Player object attempting to make a move or provide input.
            card_index: The index of the card in the player's hand to play.
                        Can be None if the call is to resolve a pending action that
                        doesn't involve playing a new card from hand (e.g., choosing a color).
            action_input: A dictionary containing player inputs needed for pending actions
                          (e.g., chosen color, indices of cards for swap).
            chosen_color_for_wild: If `card_index` refers to playing a Wild card, this is
                                   the color chosen for it. If None and a Wild is played,
                                   a CHOOSE_COLOR action will be initiated.

        Returns:
            A tuple (success, message, next_action_prompt):
            - success (bool): True if the turn/action was processed successfully (though it
                              might be an invalid move that's correctly identified).
            - message (str): A descriptive message of what happened during the turn/action.
            - next_action_prompt (Optional[ActionType]): If further input is needed from a
                                                        player, this indicates the type of
                                                        pending action. Otherwise, None.
        """
        current_turn_player_obj = self.get_current_player()

        # Basic turn validation
        if self.pending_action is None and player != current_turn_player_obj:
            return False, "It's not your turn.", None
        if self.game_over:
            return False, "The game is already over.", None

        message_parts: List[str] = []
        next_action_needed: Optional[ActionType] = None

        # --- Part 1: Handle pending multi-step actions if one exists ---
        if self.pending_action:
            # Determine who should be acting on this pending action.
            # This can be complex depending on the action.
            actor_for_pending = (
                player  # Assume the 'player' arg is the one providing input.
            )
            # Logic below will verify if this 'player' is the correct one.
            original_initiator_idx = self.action_data.get(
                "original_player_idx", self.players.index(current_turn_player_obj)
            )
            original_initiator = self.players[original_initiator_idx]

            # --- SWAP_CARD_RIGHT (Rank 7) Resolution ---
            if self.pending_action.type == ActionType.SWAP_CARD_RIGHT:
                if (
                    actor_for_pending != original_initiator
                ):  # Only original Rank 7 player provides input
                    return (
                        False,
                        f"Waiting for {original_initiator.name} to complete SWAP_CARD_RIGHT.",
                        ActionType.SWAP_CARD_RIGHT,
                    )

                player_to_right = self._get_player_at_offset(
                    original_initiator_idx, self.play_direction
                )
                card_to_give_idx = (
                    action_input.get("card_to_give_idx") if action_input else None
                )
                card_to_take_idx = (
                    action_input.get("card_to_take_idx") if action_input else None
                )

                if card_to_give_idx is None or card_to_take_idx is None:
                    return (
                        False,
                        "Card choices (indices to give and take) are missing for Rank 7 swap.",
                        ActionType.SWAP_CARD_RIGHT,
                    )
                if not (0 <= card_to_give_idx < actor_for_pending.hand_size()):
                    return (
                        False,
                        f"Invalid card index to give: {card_to_give_idx}.",
                        ActionType.SWAP_CARD_RIGHT,
                    )

                if player_to_right.is_hand_empty():
                    message_parts.append(
                        f"{player_to_right.name}'s hand is empty, Rank 7 swap cannot complete fully."
                    )
                elif not (0 <= card_to_take_idx < player_to_right.hand_size()):
                    return (
                        False,
                        f"Invalid card index to take from {player_to_right.name}: {card_to_take_idx}.",
                        ActionType.SWAP_CARD_RIGHT,
                    )
                else:
                    card_given = actor_for_pending.play_card(
                        card_to_give_idx
                    )  # play_card removes from hand
                    card_taken = player_to_right.play_card(card_to_take_idx)

                    if card_given and card_taken:
                        actor_for_pending.add_card_to_hand(card_taken)
                        player_to_right.add_card_to_hand(card_given)
                        message_parts.append(
                            f"{actor_for_pending.name} (Rank 7) gave {card_given} to {player_to_right.name} and took {card_taken}."
                        )
                    else:  # Should not happen if indices are valid and hands not empty
                        if card_given:
                            actor_for_pending.add_card_to_hand(card_given)  # Rollback
                        if card_taken:
                            player_to_right.add_card_to_hand(card_taken)  # Rollback
                        message_parts.append("Error during Rank 7 card swap process.")

                self.pending_action = None
                self.action_data.clear()
                self.current_player_index = (
                    original_initiator_idx  # Turn was for original initiator
                )
                self._advance_turn_marker()  # Advance to next player after Rank 7 effect
                return True, " ".join(filter(None, message_parts)), None

            # --- SWAP_CARD_ANY (Rank 0) Resolution ---
            elif self.pending_action.type == ActionType.SWAP_CARD_ANY:
                if actor_for_pending != original_initiator:
                    return (
                        False,
                        f"Waiting for {original_initiator.name} to complete SWAP_CARD_ANY.",
                        ActionType.SWAP_CARD_ANY,
                    )

                # Stage 1: Choose target player
                if "target_player_idx" not in self.action_data:
                    target_idx_input = (
                        action_input.get("target_player_idx") if action_input else None
                    )
                    if (
                        target_idx_input is None
                        or not (0 <= target_idx_input < len(self.players))
                        or target_idx_input == original_initiator_idx
                    ):
                        return (
                            False,
                            "Invalid or missing target player index for Rank 0 swap.",
                            ActionType.SWAP_CARD_ANY,
                        )
                    self.action_data["target_player_idx"] = target_idx_input
                    message_parts.append(
                        f"{actor_for_pending.name} (Rank 0) targets {self.players[target_idx_input].name} for swap."
                    )
                    return (
                        True,
                        " ".join(filter(None, message_parts))
                        + " Now choose cards to swap.",
                        ActionType.SWAP_CARD_ANY,
                    )  # Still pending

                # Stage 2: Choose cards to swap with the selected target
                target_player = self.players[self.action_data["target_player_idx"]]
                card_to_give_idx = (
                    action_input.get("card_to_give_idx") if action_input else None
                )
                card_to_take_idx = (
                    action_input.get("card_to_take_idx") if action_input else None
                )

                if card_to_give_idx is None or card_to_take_idx is None:
                    return (
                        False,
                        "Card choices (indices to give and take) are missing for Rank 0 swap.",
                        ActionType.SWAP_CARD_ANY,
                    )
                if not (0 <= card_to_give_idx < actor_for_pending.hand_size()):
                    return (
                        False,
                        f"Invalid card index to give: {card_to_give_idx}.",
                        ActionType.SWAP_CARD_ANY,
                    )

                if target_player.is_hand_empty():
                    message_parts.append(
                        f"{target_player.name}'s hand is empty, Rank 0 swap cannot complete fully."
                    )
                elif not (0 <= card_to_take_idx < target_player.hand_size()):
                    return (
                        False,
                        f"Invalid card index to take from {target_player.name}: {card_to_take_idx}.",
                        ActionType.SWAP_CARD_ANY,
                    )
                else:
                    card_given = actor_for_pending.play_card(card_to_give_idx)
                    card_taken = target_player.play_card(card_to_take_idx)
                    if card_given and card_taken:
                        actor_for_pending.add_card_to_hand(card_taken)
                        target_player.add_card_to_hand(card_given)
                        message_parts.append(
                            f"{actor_for_pending.name} (Rank 0) gave {card_given} to {target_player.name} and took {card_taken}."
                        )
                    else:  # Rollback if something went wrong
                        if card_given:
                            actor_for_pending.add_card_to_hand(card_given)
                        if card_taken:
                            target_player.add_card_to_hand(card_taken)
                        message_parts.append("Error during Rank 0 card swap process.")

                self.pending_action = None
                self.action_data.clear()
                self.current_player_index = original_initiator_idx
                self._advance_turn_marker()
                return True, " ".join(filter(None, message_parts)), None

            # --- DISCARD_FROM_PLAYER_HAND (Blue 3) Resolution ---
            elif self.pending_action.type == ActionType.DISCARD_FROM_PLAYER_HAND:
                chooser_idx = self.action_data.get("chooser_idx")
                victim_of_discard_idx = self.action_data.get(
                    "victim_idx"
                )  # This is the Blue3 player

                if chooser_idx is None or victim_of_discard_idx is None:
                    return (
                        False,
                        "Error: Context missing for DISCARD_FROM_PLAYER_HAND.",
                        None,
                    )

                chooser = self.players[chooser_idx]
                victim_of_discard = self.players[
                    victim_of_discard_idx
                ]  # Player whose hand cards are chosen from

                if (
                    actor_for_pending != chooser
                ):  # Input must come from the designated chooser
                    return (
                        False,
                        f"Waiting for {chooser.name} to choose cards for Blue 3 effect.",
                        ActionType.DISCARD_FROM_PLAYER_HAND,
                    )

                num_to_discard = self.action_data.get("count", 2)
                chosen_indices_from_victim_hand = (
                    action_input.get("chosen_indices_from_victim", [])
                    if action_input
                    else []
                )

                actual_cards_to_make_victim_discard = min(
                    num_to_discard, victim_of_discard.hand_size()
                )
                if (
                    not isinstance(chosen_indices_from_victim_hand, list)
                    or len(set(chosen_indices_from_victim_hand))
                    != actual_cards_to_make_victim_discard
                ):
                    return (
                        False,
                        f"{chooser.name} must choose {actual_cards_to_make_victim_discard} distinct card indices from {victim_of_discard.name}'s hand.",
                        ActionType.DISCARD_FROM_PLAYER_HAND,
                    )

                # Validate indices and prepare cards for discard
                chosen_indices_from_victim_hand.sort(
                    reverse=True
                )  # Sort to pop correctly
                cards_discarded_by_victim_strs = []
                cards_actually_removed_objs = []
                valid_indices_chosen = True

                for idx_to_pop in chosen_indices_from_victim_hand:
                    if not (
                        0 <= idx_to_pop < victim_of_discard.hand_size()
                    ):  # Check against current hand size before pop
                        valid_indices_chosen = False
                        break
                    # card_obj_to_discard = victim_of_discard.hand[  # Unused variable
                    #     idx_to_pop
                    # ]  # Peek before pop for safety if pop fails
                    # Now actually remove it
                    removed_card = victim_of_discard.play_card(
                        idx_to_pop
                    )  # play_card pops
                    if removed_card:
                        cards_actually_removed_objs.append(removed_card)
                        cards_discarded_by_victim_strs.append(str(removed_card))
                    else:  # Should not happen if index was valid
                        valid_indices_chosen = False
                        break

                if not valid_indices_chosen:
                    for (
                        c_obj_rollback
                    ) in cards_actually_removed_objs:  # Rollback removals
                        victim_of_discard.add_card_to_hand(c_obj_rollback)
                    return (
                        False,
                        "Error processing chosen discard indices for Blue 3. Invalid index or card not found.",
                        ActionType.DISCARD_FROM_PLAYER_HAND,
                    )

                for card_obj_final_discard in cards_actually_removed_objs:
                    self.deck.add_to_discard(
                        card_obj_final_discard
                    )  # Add to main discard pile

                message_parts.append(
                    f"{chooser.name} (Blue 3 effect) made {victim_of_discard.name} discard: {', '.join(cards_discarded_by_victim_strs)}."
                )

                self.pending_action = None
                self.action_data.clear()
                self.current_player_index = (
                    victim_of_discard_idx  # Turn was originally for Blue3 player
                )
                self._advance_turn_marker()  # Advance after Blue 3 effect
                return True, " ".join(filter(None, message_parts)), None

            # --- PLAY_ANY_AND_DRAW_ONE (Rank 6) Resolution ---
            elif self.pending_action.type == ActionType.PLAY_ANY_AND_DRAW_ONE:
                player_who_played_rank_6 = original_initiator
                if actor_for_pending != player_who_played_rank_6:
                    return (
                        False,
                        f"Waiting for {player_who_played_rank_6.name} to complete Rank 6 effect.",
                        ActionType.PLAY_ANY_AND_DRAW_ONE,
                    )

                card_idx_for_rank_6_effect = (
                    card_index  # This is the card chosen to play freely
                )
                color_for_rank_6_wild = (
                    action_input.get("chosen_color_for_rank_6_wild")
                    if action_input
                    else None
                )

                if card_idx_for_rank_6_effect is None:
                    return (
                        False,
                        "Must choose a card from hand to play for Rank 6 effect.",
                        ActionType.PLAY_ANY_AND_DRAW_ONE,
                    )
                if not (
                    0
                    <= card_idx_for_rank_6_effect
                    < player_who_played_rank_6.hand_size()
                ):
                    return (
                        False,
                        f"Invalid card index for Rank 6 effect: {card_idx_for_rank_6_effect}.",
                        ActionType.PLAY_ANY_AND_DRAW_ONE,
                    )

                card_to_play_freely = player_who_played_rank_6.hand[
                    card_idx_for_rank_6_effect
                ]

                # If the freely chosen card is Wild and color isn't provided yet, ask for color first.
                if card_to_play_freely.is_wild() and color_for_rank_6_wild is None:
                    self.action_data["is_for_rank_6_wild"] = (
                        True  # Mark that CHOOSE_COLOR is for this
                    )
                    self.action_data["rank_6_card_idx_pending_color"] = (
                        card_idx_for_rank_6_effect
                    )
                    # original_player_idx is already set for player_who_played_rank_6
                    self.pending_action = GameAction(
                        ActionType.CHOOSE_COLOR
                    )  # Change pending to CHOOSE_COLOR
                    return (
                        True,
                        f"{player_who_played_rank_6.name} chose Wild {card_to_play_freely} for Rank 6. Now, choose its color.",
                        ActionType.CHOOSE_COLOR,
                    )

                # Play the chosen card for Rank 6
                played_card_obj_for_rank_6 = player_who_played_rank_6.play_card(
                    card_idx_for_rank_6_effect
                )
                if not played_card_obj_for_rank_6:
                    return (
                        False,
                        "Error playing card for Rank 6.",
                        None,
                    )  # Should not happen

                message_parts.append(
                    f"{player_who_played_rank_6.name} (Rank 6) freely plays {played_card_obj_for_rank_6}."
                )
                self.deck.add_to_discard(played_card_obj_for_rank_6)

                active_color_for_freely_played_card = None
                if played_card_obj_for_rank_6.is_wild():
                    if color_for_rank_6_wild is None:
                        return (
                            False,
                            "Logic Error: Color for Rank 6 Wild missing after prompt.",
                            None,
                        )
                    self.current_wild_color = color_for_rank_6_wild
                    played_card_obj_for_rank_6.active_color = color_for_rank_6_wild
                    active_color_for_freely_played_card = color_for_rank_6_wild
                    message_parts.append(
                        f"Chosen color for Wild: {color_for_rank_6_wild.name}."
                    )
                else:
                    self.current_wild_color = None  # Played card is not Wild
                    active_color_for_freely_played_card = (
                        played_card_obj_for_rank_6.color
                    )

                self._award_color_counters(
                    player_who_played_rank_6, played_card_obj_for_rank_6
                )

                # Process actions of the freely played card
                actions_from_freely_played_card = self._get_card_actions(
                    played_card_obj_for_rank_6,
                    player_who_played_rank_6,
                    active_color_for_freely_played_card,
                )

                # IMPORTANT: Win by Rank 6 freely played card.
                if player_who_played_rank_6.is_hand_empty() and not any(
                    a.type == ActionType.GAME_WIN
                    for a in actions_from_freely_played_card
                ):
                    actions_from_freely_played_card = [GameAction(ActionType.GAME_WIN)]

                skip_after_freely_played_card = False
                for sub_action in actions_from_freely_played_card:
                    if sub_action.message_override:
                        message_parts.append(sub_action.message_override)
                    if sub_action.type == ActionType.GAME_WIN:
                        self.game_over = True
                        self.winner = player_who_played_rank_6
                        message_parts.append(
                            f" {player_who_played_rank_6.name} wins with Rank 6 effect!"
                        )
                        break
                    if sub_action.type == ActionType.DRAW_CARDS:
                        target_offset = (
                            sub_action.target_player_offset
                            if sub_action.target_player_offset is not None
                            else 1
                        )
                        victim = self._get_player_at_offset(
                            original_initiator_idx, self.play_direction * target_offset
                        )
                        drawn = self.player_draws_card(victim, sub_action.value)
                        message_parts.append(
                            f"{victim.name} draws {len(drawn)} card(s) due to Rank 6's sub-effect."
                        )
                    if sub_action.type == ActionType.SKIP_PLAYER:
                        skip_after_freely_played_card = True
                    if sub_action.type == ActionType.REVERSE_DIRECTION:
                        self.play_direction *= -1
                        message_parts.append(
                            "Play direction reversed by Rank 6's sub-effect."
                        )
                    # CHOOSE_COLOR from a freely played Wild inside Rank 6 is handled by the re-entry logic above.

                if self.game_over:
                    return True, " ".join(filter(None, message_parts)), None

                # Finally, player who played Rank 6 draws one card
                drawn_for_rank_6 = self.player_draws_card(player_who_played_rank_6, 1)
                message_parts.append(
                    f"{player_who_played_rank_6.name} draws 1 card as part of Rank 6 effect ({drawn_for_rank_6[0] if drawn_for_rank_6 else 'None drawn'})."
                )

                self.pending_action = None
                self.action_data.clear()
                self.current_player_index = (
                    original_initiator_idx  # Turn was for Rank 6 player
                )
                self._advance_turn_marker()  # Advance turn after Rank 6 full effect
                if skip_after_freely_played_card:
                    message_parts.append(
                        f"{self.get_current_player().name} is skipped by Rank 6's sub-effect."
                    )
                    self._advance_turn_marker()
                return True, " ".join(filter(None, message_parts)), None

            # --- CHOOSE_COLOR (for a standard Wild/WD4 or a Wild played via Rank 9) Resolution ---
            elif self.pending_action.type == ActionType.CHOOSE_COLOR:
                chosen_color_input = (
                    action_input.get("chosen_color") if action_input else None
                )
                if (
                    not isinstance(chosen_color_input, Color)
                    or chosen_color_input == Color.WILD
                ):
                    return (
                        False,
                        "Invalid color chosen for Wild. Must be Red, Yellow, Green, or Blue.",
                        ActionType.CHOOSE_COLOR,
                    )

                # Check if this CHOOSE_COLOR is for a Wild played via Rank 6
                if self.action_data.get("is_for_rank_6_wild"):
                    rank_6_card_idx_that_was_wild = self.action_data.pop(
                        "rank_6_card_idx_pending_color"
                    )
                    self.action_data.pop("is_for_rank_6_wild")  # Clear the flag
                    # original_player_idx for Rank 6 initiator should still be in action_data
                    player_for_rank_6_effect = self.players[
                        self.action_data.get("original_player_idx")
                    ]

                    message_parts.append(
                        f"{player_for_rank_6_effect.name} chose {chosen_color_input.name} for their Rank 6 Wild card."
                    )
                    # Re-enter play_turn to complete the Rank 6 PLAY_ANY_AND_DRAW_ONE, now with color.
                    self.pending_action = GameAction(
                        ActionType.PLAY_ANY_AND_DRAW_ONE
                    )  # Set pending back to Rank 6
                    return self.play_turn(  # Recursive call to handle rest of Rank 6
                        player_for_rank_6_effect,
                        card_index=rank_6_card_idx_that_was_wild,
                        action_input={
                            "chosen_color_for_rank_6_wild": chosen_color_input
                        },
                    )
                else:  # Standard Wild card color choice (or Wild from Rank 9)
                    card_that_was_wild = self.action_data.get(
                        "card_played"
                    )  # The Wild/WD4 card object
                    player_who_chose_idx = self.action_data.get(
                        "player_idx", self.players.index(actor_for_pending)
                    )
                    player_who_chose = self.players[player_who_chose_idx]

                    if actor_for_pending != player_who_chose:
                        return (
                            False,
                            f"Waiting for {player_who_chose.name} to choose color.",
                            ActionType.CHOOSE_COLOR,
                        )
                    if not card_that_was_wild or not card_that_was_wild.is_wild():
                        return (
                            False,
                            "Error: CHOOSE_COLOR context is missing or card is not Wild.",
                            None,
                        )

                    self.current_wild_color = chosen_color_input
                    card_that_was_wild.active_color = (
                        chosen_color_input  # Update card on discard pile
                    )
                    message_parts.append(
                        f"{player_who_chose.name} chose {chosen_color_input.name} for {card_that_was_wild}."
                    )

                    remaining_actions_after_color_choice = self.action_data.pop(
                        "remaining_actions", []
                    )
                    self.pending_action = None
                    self.action_data.clear()

                    skip_after_wild_effects = False
                    for sub_action in (
                        remaining_actions_after_color_choice
                    ):  # Process WD4 effects etc.
                        if sub_action.message_override:
                            message_parts.append(sub_action.message_override)
                        if sub_action.type == ActionType.DRAW_CARDS:
                            target_offset = (
                                sub_action.target_player_offset
                                if sub_action.target_player_offset is not None
                                else 1
                            )
                            victim = self._get_player_at_offset(
                                player_who_chose_idx,
                                self.play_direction * target_offset,
                            )
                            drawn = self.player_draws_card(victim, sub_action.value)
                            message_parts.append(
                                f"{victim.name} draws {len(drawn)} card(s)."
                            )
                        if sub_action.type == ActionType.SKIP_PLAYER:
                            skip_after_wild_effects = True

                    self.current_player_index = (
                        player_who_chose_idx  # Turn was for player who chose color
                    )
                    self._advance_turn_marker()  # Advance turn
                    if skip_after_wild_effects:
                        message_parts.append(
                            f"{self.get_current_player().name} is skipped."
                        )
                        self._advance_turn_marker()
                    return True, " ".join(filter(None, message_parts)), None

        # --- Part 2: Standard card play (if no pending_action was handled above) ---
        # 'player' here is current_turn_player_obj for a new card play.
        if card_index is None:  # Must provide a card to play if no pending action
            return False, "No card selected to play and no pending action.", None
        if not (0 <= card_index < player.hand_size()):
            return False, f"Invalid card index: {card_index}.", None

        card_to_play_peek = player.hand[card_index]  # Peek first for validation
        top_discard = self.get_top_card()
        if not top_discard:  # Should not happen in a normal game after setup
            return False, "Error: No card on discard pile to play on.", None

        # Validate if the chosen card can be played
        if not card_to_play_peek.matches(top_discard, self.current_wild_color):
            return (
                False,
                f"Cannot play {card_to_play_peek} on {top_discard} (Active color: {self.current_wild_color if self.current_wild_color else 'None'}).",
                None,
            )

        # Card is playable, now actually play it
        played_card = player.play_card(card_index)  # Removes from hand
        if not played_card:
            return (
                False,
                "Error: Failed to retrieve card from hand after validation.",
                None,
            )  # Should not happen

        shouted_uno = (
            player.hand_size() == 1
        )  # Check if UNO should be shouted (1 card *left* after this play)
        message_parts.append(
            GameAction.card_played_message(player.name, str(played_card), shouted_uno)
        )

        # --- Handle Rank 2 duplicate play rule ---
        # This checks if the `played_card` is an exact duplicate of the card *now under it* on discard.
        card_underneath_played_one = (
            self.deck.get_top_discard_card()
        )  # Get card that was top
        self.deck.add_to_discard(played_card)  # Now, played_card is on top

        if (
            card_underneath_played_one
            and played_card.rank == card_underneath_played_one.rank
            and played_card.color == card_underneath_played_one.color
            and not played_card.is_wild()
        ):  # Duplicate rule typically for non-Wilds
            twos_in_hand = [c for c in player.hand if c.rank == Rank.TWO]
            if twos_in_hand:
                message_parts.append(
                    f"{player.name} played a duplicate {played_card}! Discarding all their Rank 2 cards."
                )
                for two_card_to_discard in list(
                    twos_in_hand
                ):  # Iterate over a copy if modifying hand
                    player.remove_card_from_hand(two_card_to_discard)
                    self.deck.add_to_discard(two_card_to_discard)
                    message_parts.append(
                        f"{player.name} discards {two_card_to_discard} due to duplicate rule."
                    )

                if (
                    player.is_hand_empty()
                ):  # Win by discarding last 2s due to duplicate rule
                    self.game_over = True
                    self.winner = player
                    message_parts.append(
                        f" {player.name} wins by discarding all cards (including 2s) after duplicate play!"
                    )
                    return True, " ".join(filter(None, message_parts)), None

        # Update game state after card is on discard pile
        if not played_card.is_wild():
            self.current_wild_color = (
                None  # Clear chosen Wild color if previous was Wild
            )

        self._award_color_counters(player, played_card)

        # Special Yellow 4 storage logic (if player played a Yellow 4)
        if played_card.color == Color.YELLOW and played_card.rank == Rank.FOUR:
            # This rule is a bit ambiguous: "Each Yellow 4 played can be moved to a 'get out of jail free' pile."
            # Does it mean the one *just played*? Or it enables storing *another* Y4 from hand?
            # Current Player.store_yellow_4... takes a card. If it's the one just played, it's problematic.
            # Let's assume for now it means the player gets the *option* to store THIS Yellow 4
            # instead of it just staying on discard. This would need a UI prompt.
            # For simulation, let's assume player *chooses* to store it if possible.
            # This means it does NOT stay on discard pile.
            if player.get_out_of_jail_yellow_4 is None:  # Can only store one
                # self.deck.discard_pile.pop() # Remove it from discard, as it's being stored
                # Storing it means it's not the top_card for next player. This needs care.
                # For simplicity, let's say the played Y4 goes to discard, and separately
                # the player can use a Y4 from their *hand* for the jail pile.
                # The current `player.store_yellow_4_get_out_of_jail` is for a card *from hand*.
                # Let's assume playing a Y4 gives a coin, and the "get out of jail" is a separate passive ability.
                # The `if player.store_yellow_4_get_out_of_jail(card)` in old __main__ implies the played card.
                # This is complex. Let's stick to: it gives a coin. Storing is a separate action not tied to *this specific play*.
                # However, the original main loop simulation for UnoGame directly calls player.store_yellow_4_get_out_of_jail(played_card)
                # This would mean it's taken off the discard. This affects next player.
                # Let's follow the main loop's interpretation for now, which is:
                # If a Yellow 4 is played, and player *can* store one, they do. The card is then not the top_discard.
                # This is a bit strange. A safer rule: "Playing a Yellow 4 gives a coin. You may also (if you have one)
                # set aside a Yellow 4 from your hand into your jail pile."
                # For now, to match the `__main__` behavior:
                # if player.store_yellow_4_get_out_of_jail(played_card):
                #    message_parts.append(f"{player.name}'s played Yellow 4 moved to 'get out of jail free' pile instead of discard.")
                #    # Top card of discard is now what was underneath. This is tricky.
                #    # For now, let's assume the game's example __main__ had a simplified interpretation.
                #    # I will NOT implement moving the *played* card to the jail pile here, as it complicates discard logic immensely.
                #    # It will just award a coin. Player.store_... is for cards from hand.
                pass  # The Yellow 4 counter awarding is done. Storage is separate.

        # Get actions for the played card (standard effects or CHOOSE_COLOR if Wild and no color given)
        actions_to_process = self._get_card_actions(
            played_card,
            player,
            chosen_color_for_wild if played_card.is_wild() else None,
        )

        # Check for win condition if hand is empty
        if player.is_hand_empty() and not any(
            a.type == ActionType.GAME_WIN for a in actions_to_process
        ):
            actions_to_process = [
                GameAction(ActionType.GAME_WIN)
            ]  # Override other actions if win

        # --- Part 3: Process actions generated by the played card ---
        skip_next_player_flag = False
        advance_turn_normally = (
            True  # Assume turn advances unless an action says otherwise
        )

        action_idx = 0
        while action_idx < len(actions_to_process):
            action = actions_to_process[action_idx]
            action_idx += 1  # Increment at start to allow modification of list during iteration (e.g. for Rank 9)

            if action.message_override:
                message_parts.append(action.message_override)

            if action.type == ActionType.GAME_WIN:
                self.game_over = True
                self.winner = player
                message_parts.append(f" {player.name} wins the game!")
                return (
                    True,
                    " ".join(filter(None, message_parts)),
                    None,
                )  # Game ends immediately

            elif action.type == ActionType.CHOOSE_COLOR:
                if (
                    action.value
                ):  # Color was already provided (e.g. for AI, or if UI pre-collects)
                    self.current_wild_color = action.value
                    if played_card and played_card.is_wild():
                        played_card.active_color = action.value
                    # Message for chosen color already added by _get_card_actions if action.value exists
                else:  # Color needs to be chosen now
                    self.pending_action = action
                    self.action_data = {
                        "card_played": played_card,  # The Wild card that needs a color
                        "remaining_actions": actions_to_process[
                            action_idx:
                        ],  # e.g., Draw 4 + Skip for WD4
                        "player_idx": self.players.index(player),  # Who needs to choose
                        "original_player_idx": self.players.index(
                            player
                        ),  # Who played the card
                    }
                    # Message for needing to choose color added by _get_card_actions
                    return (
                        True,
                        " ".join(filter(None, message_parts)),
                        ActionType.CHOOSE_COLOR,
                    )

            elif action.type == ActionType.DRAW_CARDS:
                target_offset = (
                    action.target_player_offset
                    if action.target_player_offset is not None
                    else 1
                )
                victim = self._get_player_at_offset(
                    self.players.index(player), self.play_direction * target_offset
                )
                drawn_count = len(self.player_draws_card(victim, action.value))
                # Message for drawing already added by _get_card_actions or will be generic like "X draws Y cards"
                if not action.message_override:  # Add a generic if none specific
                    message_parts.append(f"{victim.name} draws {drawn_count} card(s).")

            elif action.type == ActionType.SKIP_PLAYER:
                skip_next_player_flag = (
                    True  # Actual skip happens when advancing turn marker
                )
                # Message already added by _get_card_actions

            elif action.type == ActionType.REVERSE_DIRECTION:
                self.play_direction *= -1
                # Message already added by _get_card_actions

            # --- Handle initiations of multi-step custom actions ---
            elif action.type in [
                ActionType.SWAP_CARD_RIGHT,
                ActionType.SWAP_CARD_ANY,
                ActionType.DISCARD_FROM_PLAYER_HAND,
                ActionType.PLAY_ANY_AND_DRAW_ONE,
            ]:
                self.pending_action = action
                self.action_data = {
                    "original_card": played_card,  # Card that triggered this
                    "remaining_actions": actions_to_process[
                        action_idx:
                    ],  # Any standard actions that might follow
                    "original_player_idx": self.players.index(
                        player
                    ),  # Player who initiated
                }
                # Specific additional data for some pending actions:
                if action.type == ActionType.DISCARD_FROM_PLAYER_HAND:
                    # Player to the left of Blue3 player is the chooser.
                    chooser_offset = (
                        -self.play_direction
                    )  # Offset from Blue3 player to chooser
                    self.action_data["chooser_idx"] = self.players.index(
                        self._get_player_at_offset(
                            self.players.index(player), chooser_offset
                        )
                    )
                    self.action_data["victim_idx"] = self.players.index(
                        player
                    )  # Blue3 player is victim of card choice
                    self.action_data["count"] = (
                        action.value["count"] if action.value else 2
                    )

                next_action_needed = action.type
                advance_turn_normally = (
                    False  # Turn doesn't advance until pending action is resolved
                )
                message_parts.append(
                    f"{player.name} initiated {action.type.name}. Further input required."
                )
                break  # Stop processing further actions from original card; wait for pending action input

            elif action.type == ActionType.PLAYER_DRAWS_FOUR_UNLESS_LAST:  # Red 8
                # Check hand size *now*. Player has already played the Red 8.
                if player.hand_size() > 0:  # Not their last card
                    drawn_red8 = self.player_draws_card(player, 4)
                    message_parts.append(
                        f"{player.name} (Red 8) was not their last card, draws {len(drawn_red8)} cards."
                    )
                else:  # Was their last card
                    message_parts.append(
                        f"{player.name} played Red 8 as their last card. No draw effect."
                    )

            elif action.type == ActionType.TAKE_RANDOM_FROM_PREVIOUS:  # Green 5
                prev_player_offset = -self.play_direction
                previous_player = self._get_player_at_offset(
                    self.players.index(player), prev_player_offset
                )
                if not previous_player.is_hand_empty():
                    card_to_take_idx = random.randint(
                        0, previous_player.hand_size() - 1
                    )
                    card_taken = previous_player.play_card(
                        card_to_take_idx
                    )  # play_card removes
                    if card_taken:
                        player.add_card_to_hand(card_taken)
                        message_parts.append(
                            f"{player.name} (Green 5) took {card_taken} from {previous_player.name}."
                        )
                    else:  # Should not happen if hand not empty and index valid
                        message_parts.append(
                            f"Error taking card from {previous_player.name} for Green 5 effect."
                        )
                else:
                    message_parts.append(
                        f"{previous_player.name}'s hand is empty; {player.name} (Green 5) takes no card."
                    )

            elif action.type == ActionType.PLACE_TOP_DRAW_PILE_CARD:  # Rank 9
                if not self._handle_draw_pile_empty(
                    player
                ):  # Checks shuffle counters if needed
                    message_parts.append(
                        "Rank 9: Draw pile empty or cannot be reshuffled, no card to place."
                    )
                else:
                    new_top_card_from_draw = self.deck.draw_card()
                    if new_top_card_from_draw:
                        message_parts.append(
                            f"{player.name} (Rank 9) places {new_top_card_from_draw} from draw pile onto discard."
                        )
                        self.deck.add_to_discard(new_top_card_from_draw)

                        if not new_top_card_from_draw.is_wild():
                            self.current_wild_color = None  # Clear if previous was Wild

                        # Process effects of this newly placed card.
                        # Player who played Rank 9 is considered the 'player' for these sub-effects
                        # (e.g., if it's a Wild, they choose the color).
                        sub_actions = self._get_card_actions(
                            new_top_card_from_draw, player, None
                        )

                        # Prepend sub_actions to the current actions_to_process list
                        # This allows effects of Rank 9's card to resolve before normal turn progression.
                        actions_to_process = (
                            sub_actions + actions_to_process[action_idx:]
                        )
                        action_idx = 0  # Reset index to process these new sub-actions from the start

                        # If Rank 9 card *doesn't* cause a skip/draw on next or need color choice,
                        # and current player can play on it, they get to continue.
                        # This is complex. Let's simplify: if the new card doesn't end turn immediately
                        # (like Draw2, Skip, Reverse, Wild needing color), check if current player can play.
                        can_player_play_on_rank9_card = False
                        if not any(
                            a.type
                            in [
                                ActionType.DRAW_CARDS,
                                ActionType.SKIP_PLAYER,
                                ActionType.REVERSE_DIRECTION,
                            ]
                            or (a.type == ActionType.CHOOSE_COLOR and not a.value)
                            for a in sub_actions
                        ):
                            if player.has_playable_card(
                                new_top_card_from_draw,
                                (
                                    self.current_wild_color
                                    if new_top_card_from_draw.is_wild()
                                    else None
                                ),
                            ):
                                can_player_play_on_rank9_card = True

                        if can_player_play_on_rank9_card:
                            message_parts.append(
                                f"{player.name} may play again on the {new_top_card_from_draw} from Rank 9."
                            )
                            advance_turn_normally = False  # Player's turn continues
                        # If it needs color choice, that will set pending_action and stop normal advance.
                        # If it skips/draws on next, normal advance will happen then skip.

                    else:  # Should not happen if _handle_draw_pile_empty was true
                        message_parts.append(
                            "Rank 9: Failed to draw card from pile after check."
                        )

            elif action.type == ActionType.NOP:
                pass  # No operation, message already handled by _get_card_actions or card play message

        # After processing all actions from the card
        if self.game_over:  # Win condition might have been met by an action
            return True, " ".join(filter(None, message_parts)), None
        if next_action_needed:  # A multi-step action was initiated
            return True, " ".join(filter(None, message_parts)), next_action_needed

        # Advance turn if not overridden by an action (like Rank 9 continue, or pending action)
        if advance_turn_normally:
            # current_player_index is still the player who just played.
            # Advance based on *their* index.
            # self.current_player_index = self.players.index(player) # No, this is already correct.
            self._advance_turn_marker()  # Move to next logical player
            if skip_next_player_flag:
                message_parts.append(
                    f"{self.get_current_player().name}'s turn is skipped."
                )
                self._advance_turn_marker()  # Skip that player by advancing again

        return True, " ".join(filter(None, message_parts)), None

    def player_cannot_play_action(self, player: Player) -> Tuple[bool, str]:
        """
        Handles the scenario where the current player cannot play any card from their hand
        and chooses to draw a card instead.

        The player draws one card. If this drawn card is playable, standard Uno rules
        (often house rules) might allow them to play it immediately. This implementation
        simulates auto-playing a drawable card. If not playable, the turn passes.
        Handles shuffle counter mechanics for drawing if the draw pile is empty.

        Args:
            player: The Player who cannot play and is drawing.

        Returns:
            A tuple (success, message):
            - success (bool): True if the action was processed.
            - message (str): A descriptive message of what happened.
        """
        current_turn_player = self.get_current_player()
        if (
            player != current_turn_player
        ):  # Ensure it's the correct player taking this action
            return False, "It's not your turn to draw."
        if self.game_over:
            return False, "The game is already over."

        # Check for pending actions that must be resolved first
        # This logic is simplified; a robust system would check which player is expected for pending_action
        if self.pending_action:
            # Determine who is expected to act for the pending action
            # original_initiator assignment was unused here.
            # current_turn_player_obj was not defined in this scope, should be current_turn_player
            expected_actor_for_pending = self.players[
                self.action_data.get(
                    "original_player_idx", self.players.index(current_turn_player)
                )
            ]
            if (
                self.pending_action.type == ActionType.DISCARD_FROM_PLAYER_HAND
            ):  # Chooser acts
                expected_actor_for_pending = self.players[
                    self.action_data.get("chooser_idx")
                ]
            elif (
                self.pending_action.type == ActionType.CHOOSE_COLOR
            ):  # Player who played Wild/Rank9 acts
                expected_actor_for_pending = self.players[
                    self.action_data.get(
                        "player_idx", self.action_data.get("original_player_idx")
                    )
                ]

            if player == expected_actor_for_pending:
                return (
                    False,
                    f"You have a pending action ({self.pending_action.type.name}) to resolve before drawing.",
                )
            # If player is NOT the one for pending action, but it IS their turn somehow (e.g. after pending resolved to them)
            # then drawing is fine. This state should be rare.

        message_parts: List[str] = [f"{player.name} cannot play any card from hand."]

        # Attempt to use "Get Out of Jail Free" Yellow 4 first, if applicable & desired by player (simulated choice)
        # This part is complex due to player choice. For now, assume if they have it and it's playable, they use it.
        if player.has_get_out_of_jail_card():
            y4_card = player.get_out_of_jail_yellow_4  # Peek
            top_card_on_discard = self.get_top_card()
            if (
                y4_card
                and top_card_on_discard
                and y4_card.matches(top_card_on_discard, self.current_wild_color)
            ):
                # Player *could* play this. Assume they do.
                player.use_get_out_of_jail_card()  # Removes from storage
                self.deck.add_to_discard(y4_card)
                message_parts.append(
                    f"{player.name} uses their stored 'Get Out of Jail Free' Yellow 4 ({y4_card})!"
                )

                if not y4_card.is_wild():
                    self.current_wild_color = None  # Should be Yellow
                self._award_color_counters(player, y4_card)  # Yellow 4 gives a coin

                if (
                    player.is_hand_empty() and player.get_out_of_jail_yellow_4 is None
                ):  # Check actual hand now
                    self.game_over = True
                    self.winner = player
                    message_parts.append(
                        f" {player.name} wins by playing their stored Yellow 4 as their last card!"
                    )
                    return True, " ".join(filter(None, message_parts))

                # Process actions of this Yellow 4 (standard card, no special game actions beyond being played)
                # Standard Yellow 4 has no further game actions like skip/draw.
                self._advance_turn_marker()  # Turn ends after playing the Y4
                return True, " ".join(filter(None, message_parts))
            else:
                message_parts.append(
                    f"{player.name} has a stored Yellow 4, but it's not playable now (or chooses not to use it)."
                )

        # Proceed to draw a card
        message_parts.append(f"{player.name} draws a card.")
        drawn_cards = self.player_draws_card(
            player, 1
        )  # Handles shuffle counters if needed

        if not drawn_cards:  # Could not draw (e.g., pile empty, no shuffles)
            message_parts.append("No card could be drawn. Turn passes.")
            self._advance_turn_marker()
            return True, " ".join(message_parts)

        drawn_card = drawn_cards[0]
        message_parts.append(f"{player.name} drew: {drawn_card}.")

        # Check if the drawn card is immediately playable
        top_card_on_discard_after_draw = (
            self.get_top_card()
        )  # Re-fetch, might have changed if reshuffle happened
        if top_card_on_discard_after_draw and drawn_card.matches(
            top_card_on_discard_after_draw, self.current_wild_color
        ):
            message_parts.append(
                f"The drawn card ({drawn_card}) is playable! {player.name} plays it."
            )

            # Simulate playing this drawn card
            player.remove_card_from_hand(
                drawn_card
            )  # Already added by player_draws_card, now remove for playing

            shouted_uno_on_drawn = (
                player.hand_size() == 1
            )  # 1 card left *after* this play
            message_parts.append(
                GameAction.card_played_message(
                    player.name, f"drawn {drawn_card}", shouted_uno_on_drawn
                )
            )

            self.deck.add_to_discard(drawn_card)

            chosen_color_for_drawn_wild_card = None
            if drawn_card.is_wild():
                # For simulation, auto-choose color for a drawn Wild. UI would prompt.
                chosen_color_for_drawn_wild_card = random.choice(
                    [c for c in Color if c != Color.WILD]
                )
                self.current_wild_color = chosen_color_for_drawn_wild_card
                drawn_card.active_color = chosen_color_for_drawn_wild_card
                message_parts.append(
                    f"{player.name} chose {chosen_color_for_drawn_wild_card.name} for the drawn Wild."
                )
            else:
                self.current_wild_color = None

            self._award_color_counters(player, drawn_card)

            if player.is_hand_empty():  # Won by playing the drawn card
                self.game_over = True
                self.winner = player
                message_parts.append(
                    f" {player.name} played their drawn card ({drawn_card}) and wins!"
                )
                return True, " ".join(filter(None, message_parts))

            # Process actions of the drawn-and-played card
            actions_from_drawn_card = self._get_card_actions(
                drawn_card, player, chosen_color_for_drawn_wild_card
            )
            skip_after_drawn_card_play = False
            for action_item in actions_from_drawn_card:
                if action_item.message_override:
                    message_parts.append(action_item.message_override)
                # Simplified processing for drawn card, primarily looking for game end / skips / reverse
                if (
                    action_item.type == ActionType.GAME_WIN
                ):  # Should be caught by hand_empty above
                    self.game_over = True
                    self.winner = player
                    break
                if (
                    action_item.type == ActionType.DRAW_CARDS
                ):  # e.g. drew a Draw Two and played it
                    target_offset_dc = (
                        action_item.target_player_offset
                        if action_item.target_player_offset is not None
                        else 1
                    )
                    victim_dc = self._get_player_at_offset(
                        self.players.index(player),
                        self.play_direction * target_offset_dc,
                    )
                    drawn_dc = self.player_draws_card(victim_dc, action_item.value)
                    if not action_item.message_override:
                        message_parts.append(
                            f"{victim_dc.name} draws {len(drawn_dc)} card(s)."
                        )
                if action_item.type == ActionType.SKIP_PLAYER:
                    skip_after_drawn_card_play = True
                if action_item.type == ActionType.REVERSE_DIRECTION:
                    self.play_direction *= -1
                    if not action_item.message_override:
                        message_parts.append("Play direction reversed.")

            if self.game_over:
                return True, " ".join(filter(None, message_parts))

            # Turn advances after playing the drawn card
            # self.current_player_index is still 'player's index at this point
            self._advance_turn_marker()
            if skip_after_drawn_card_play:
                message_parts.append(
                    f"{self.get_current_player().name}'s turn is skipped."
                )
                self._advance_turn_marker()
            return True, " ".join(filter(None, message_parts))
        else:  # Drawn card is not playable
            message_parts.append(
                f"The drawn card ({drawn_card}) is not playable. Turn ends."
            )
            self._advance_turn_marker()  # Turn passes to next player
            return True, " ".join(filter(None, message_parts))

    def get_game_status(self) -> str:
        """
        Provides a string summary of the current game state.

        Includes:
        - Game over status and winner (if applicable).
        - Top card on the discard pile (and active color if it's a Wild).
        - Current player whose turn it is.
        - Any pending action requiring input.
        - Direction of play.
        - Summary for each player (hand size, counters).
        - Size of the draw pile.

        Returns:
            A multi-line string describing the current game status.
        """
        if self.game_over:
            return f"Game Over! Winner: {self.winner.name if self.winner else 'None (Game ended prematurely?)'}"

        status_parts: List[str] = []
        top_card_obj = self.get_top_card()
        active_color_display = ""
        if self.current_wild_color and top_card_obj and top_card_obj.is_wild():
            active_color_display = (
                f" (Active Wild Color: {self.current_wild_color.name})"
            )
        status_parts.append(
            f"Top Card on Discard: {top_card_obj}{active_color_display}"
        )

        current_player_obj = self.get_current_player()
        status_parts.append(f"Current Player to Act: {current_player_obj.name}")

        if self.pending_action:
            # Determine who is expected to provide input for the pending action
            actor_for_pending_display = current_player_obj.name  # Default
            if self.pending_action.type == ActionType.DISCARD_FROM_PLAYER_HAND:
                chooser_idx = self.action_data.get("chooser_idx")
                if chooser_idx is not None:
                    actor_for_pending_display = self.players[chooser_idx].name
            elif (
                "original_player_idx" in self.action_data
                and self.pending_action.type not in [ActionType.CHOOSE_COLOR]
            ):  # For swaps, Rank6
                actor_for_pending_display = self.players[
                    self.action_data["original_player_idx"]
                ].name
            elif (
                "player_idx" in self.action_data
                and self.pending_action.type == ActionType.CHOOSE_COLOR
            ):  # For Wild color choice
                actor_for_pending_display = self.players[
                    self.action_data["player_idx"]
                ].name

            status_parts.append(
                f"Pending Action: {self.pending_action.type.name} (waiting for input from {actor_for_pending_display})"
            )

        status_parts.append(
            f"Play Direction: {'Clockwise (Forward)' if self.play_direction == 1 else 'Counter-Clockwise (Backward)'}"
        )
        status_parts.append("Players:")
        for p_info in self.players:
            counters_display_list = []
            if p_info.coins > 0:
                counters_display_list.append(f"Coins:{p_info.coins}")
            if p_info.shuffle_counters > 0:
                counters_display_list.append(f"Shuffles:{p_info.shuffle_counters}")
            if p_info.lunar_mana > 0:
                counters_display_list.append(f"Lunar:{p_info.lunar_mana}")
            if p_info.solar_mana > 0:
                counters_display_list.append(f"Solar:{p_info.solar_mana}")
            if p_info.get_out_of_jail_yellow_4:
                counters_display_list.append("Stored Y4")

            counters_str = (
                f" ({', '.join(counters_display_list)})"
                if counters_display_list
                else ""
            )
            status_parts.append(
                f"  - {p_info.name}: Hand[{p_info.hand_size()}]{counters_str}"
            )

        status_parts.append(f"Draw pile size: {len(self.deck.cards)} cards")
        return "\n".join(status_parts)


if __name__ == "__main__":
    # Docstrings added, no functional change to __main__
    game = UnoGame(["Alice", "Bob", "Charlie", "Dave"])
    print("Initial game state:")
    print(game.get_game_status())

    max_turns = 250  # Increased for more complex games
    for turn_num in range(max_turns):
        if game.game_over:
            print(f"\n--- Game Over on Turn {turn_num + 1} ---")
            break

        # Determine who is providing input for this step of the turn
        actor_player = game.get_current_player()  # Default actor is whose turn it is
        if game.pending_action:
            if game.pending_action.type == ActionType.DISCARD_FROM_PLAYER_HAND:
                actor_player = game.players[game.action_data.get("chooser_idx")]
            elif (
                game.pending_action.type == ActionType.CHOOSE_COLOR
                and game.action_data.get("is_for_rank_6_wild")
            ):
                actor_player = game.players[game.action_data.get("original_player_idx")]
            elif (
                "player" in game.action_data
            ):  # SWAP_CARD_RIGHT, SWAP_CARD_ANY store player object
                actor_player = game.action_data.get("player")
            elif (
                "player_idx" in game.action_data
            ):  # CHOOSE_COLOR (normal), PLAY_ANY_AND_DRAW_ONE
                actor_player = game.players[game.action_data.get("player_idx")]
            # If original_player_idx is present, it's the one who initiated the multi-step action
            elif "original_player_idx" in game.action_data:
                actor_player = game.players[game.action_data.get("original_player_idx")]

        print(
            f"\n--- Turn {turn_num + 1}: Main turn for {game.get_current_player().name}, Input from {actor_player.name} ---"
        )
        print(f"{actor_player.name}'s Hand: {actor_player.get_hand_display()}")

        turn_message = ""
        action_input_sim = {}
        card_idx_sim = None

        if game.pending_action:
            print(
                f"Sim: Handling pending action {game.pending_action.type.name} for {actor_player.name}."
            )

            if game.pending_action.type == ActionType.SWAP_CARD_RIGHT:
                if not actor_player.is_hand_empty():
                    action_input_sim["card_to_give_idx"] = random.randint(
                        0, actor_player.hand_size() - 1
                    )
                else:
                    action_input_sim["card_to_give_idx"] = 0
                player_to_right_idx = (
                    game.players.index(actor_player) + game.play_direction
                ) % len(game.players)
                player_to_right = game.players[player_to_right_idx]
                if not player_to_right.is_hand_empty():
                    action_input_sim["card_to_take_idx"] = random.randint(
                        0, player_to_right.hand_size() - 1
                    )
                else:
                    action_input_sim["card_to_take_idx"] = 0

            elif game.pending_action.type == ActionType.SWAP_CARD_ANY:
                if "target_player_idx" not in game.action_data:
                    possible_targets = [
                        i
                        for i, p in enumerate(game.players)
                        if i != game.players.index(actor_player)
                    ]
                    action_input_sim["target_player_idx"] = (
                        random.choice(possible_targets)
                        if possible_targets
                        else (game.players.index(actor_player) + 1) % len(game.players)
                    )
                else:
                    target_player = game.players[game.action_data["target_player_idx"]]
                    if not actor_player.is_hand_empty():
                        action_input_sim["card_to_give_idx"] = random.randint(
                            0, actor_player.hand_size() - 1
                        )
                    else:
                        action_input_sim["card_to_give_idx"] = 0
                    if not target_player.is_hand_empty():
                        action_input_sim["card_to_take_idx"] = random.randint(
                            0, target_player.hand_size() - 1
                        )
                    else:
                        action_input_sim["card_to_take_idx"] = 0

            elif game.pending_action.type == ActionType.DISCARD_FROM_PLAYER_HAND:
                victim = game.players[game.action_data["victim_idx"]]
                num_to_pick = min(victim.hand_size(), game.action_data.get("count", 2))
                if victim.hand_size() > 0:
                    action_input_sim["chosen_indices_from_victim"] = random.sample(
                        range(victim.hand_size()), num_to_pick
                    )
                else:
                    action_input_sim["chosen_indices_from_victim"] = []

            elif game.pending_action.type == ActionType.PLAY_ANY_AND_DRAW_ONE:
                if not actor_player.is_hand_empty():
                    card_idx_sim = random.randint(0, actor_player.hand_size() - 1)
                    chosen_card_for_rank6 = actor_player.hand[card_idx_sim]
                    if chosen_card_for_rank6.is_wild():
                        action_input_sim["chosen_color_for_rank_6_wild"] = (
                            random.choice([c for c in Color if c != Color.WILD])
                        )
                else:
                    card_idx_sim = (
                        0  # Will fail if hand empty, game logic should handle
                    )

            elif game.pending_action.type == ActionType.CHOOSE_COLOR:
                action_input_sim["chosen_color"] = random.choice(
                    [c for c in Color if c != Color.WILD]
                )

            print(
                f"Sim input for {game.pending_action.type.name}: card_idx={card_idx_sim}, action_input={action_input_sim}"
            )
            success, message_pending, next_action_prompt = game.play_turn(
                actor_player, card_idx_sim, action_input_sim
            )
            turn_message = message_pending
            if not success:
                print(f"Error completing pending action: {message_pending}")
            if next_action_prompt:
                print(
                    f"SIM: Pending action for {actor_player.name} resulted in new prompt: {next_action_prompt}"
                )

        else:  # No pending action, normal play by current_turn_player_obj
            playable_cards_indices = [
                i
                for i, card in enumerate(actor_player.hand)
                if card.matches(game.get_top_card(), game.current_wild_color)
            ]

            if playable_cards_indices:
                card_idx_sim = random.choice(playable_cards_indices)
                card_being_played = actor_player.hand[card_idx_sim]
                chosen_color_sim_val = None
                if card_being_played.is_wild():
                    chosen_color_sim_val = random.choice(
                        [c for c in Color if c != Color.WILD]
                    )

                success, message_play, next_action_prompt = game.play_turn(
                    actor_player,
                    card_idx_sim,
                    chosen_color_for_wild=chosen_color_sim_val,
                )
                turn_message = message_play
                if not success:
                    print(f"Play failed: {message_play}")
                if next_action_prompt:
                    print(
                        f"SIM: Normal play by {actor_player.name} resulted in prompt: {next_action_prompt}"
                    )
            else:
                if actor_player.has_get_out_of_jail_card():
                    y4 = actor_player.get_out_of_jail_yellow_4
                    if y4 and y4.matches(game.get_top_card(), game.current_wild_color):
                        actor_player.use_get_out_of_jail_card()
                        game.deck.add_to_discard(y4)
                        game.current_wild_color = None
                        game._award_color_counters(actor_player, y4)
                        turn_message = (
                            f"{actor_player.name} uses 'Get Out of Jail Free' Yellow 4."
                        )
                        if actor_player.is_hand_empty():
                            game.game_over = True
                            game.winner = actor_player
                            turn_message += " And WINS!"
                        else:
                            game.current_player_index = game.players.index(actor_player)
                            game._advance_turn_marker()
                    else:
                        if y4:
                            actor_player.store_yellow_4_get_out_of_jail(y4)
                        success, message_draw = game.player_cannot_play_action(
                            actor_player
                        )
                        turn_message = message_draw
                else:
                    success, message_draw = game.player_cannot_play_action(actor_player)
                    turn_message = message_draw

        print(turn_message.strip())
        print(game.get_game_status())

    print("\n--- Final Game Status ---")
    print(game.get_game_status())
    if not game.game_over:
        print(f"\nGame ended due to max turns ({max_turns}).")
    elif game.winner:
        print(f"\nWinner: {game.winner.name}")
    else:
        print("\nGame over, but winner not set.")

    print("\nFinal Player Hands & Counters:")
    for p_final in game.players:
        counters_list_final = []
        if p_final.coins > 0:
            counters_list_final.append(f"C:{p_final.coins}")
        if p_final.shuffle_counters > 0:
            counters_list_final.append(f"S:{p_final.shuffle_counters}")
        if p_final.lunar_mana > 0:
            counters_list_final.append(f"L:{p_final.lunar_mana}")
        if p_final.solar_mana > 0:
            counters_list_final.append(f"Sol:{p_final.solar_mana}")
        if p_final.get_out_of_jail_yellow_4:
            counters_list_final.append("Y4Jail")
        counter_str_final = ", ".join(counters_list_final)
        hand_str_final = (
            p_final.get_hand_display(show_indices=False)
            if p_final.hand_size() > 0
            else "Empty"
        )
        print(
            f"{p_final.name}: {hand_str_final} --- Counters: [{counter_str_final if counter_str_final else 'None'}]"
        )
