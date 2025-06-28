from typing import List, Optional, Tuple
import random

from .card import Card, Color, Rank
from .deck import Deck
from .player import Player
from .actions import ActionType, GameAction

class UnoGame:
    def __init__(self, player_names: List[str], initial_hand_size: int = 7):
        if not 2 <= len(player_names) <= 4:
            raise ValueError("UnoGame requires 2 to 4 players.")
        if initial_hand_size <= 0:
            raise ValueError("Initial hand size must be positive.")

        self.deck = Deck()
        self.players: List[Player] = [Player(name) for name in player_names]
        self.initial_hand_size = initial_hand_size

        self.current_player_index: int = 0
        self.game_over: bool = False
        self.winner: Optional[Player] = None
        self.play_direction: int = 1

        self.current_wild_color: Optional[Color] = None
        self.pending_action: Optional[GameAction] = None
        self.action_data: dict = {}

        self._setup_game()

    def _setup_game(self):
        for _ in range(self.initial_hand_size):
            for player in self.players:
                card = self.deck.draw_card()
                if card:
                    player.add_card_to_hand(card)
                else:
                    raise RuntimeError("Deck ran out of cards during initial deal.")

        first_discard = self.deck.draw_card()
        while first_discard is None or first_discard.rank == Rank.WILD_DRAW_FOUR:
            if first_discard:
                self.deck.cards.append(first_discard)
                self.deck.shuffle()
            first_discard = self.deck.draw_card()
            if first_discard is None and self.deck.needs_reshuffle():
                 self.deck.reshuffle_discard_pile_into_deck(keep_top_card=False)
                 first_discard = self.deck.draw_card()
            elif first_discard is None:
                 raise RuntimeError("Deck ran out of cards setting up discard pile.")

        self.deck.add_to_discard(first_discard)
        self.current_wild_color = None

        self.current_player_index = random.randint(0, len(self.players) - 1)

        if first_discard.is_wild():
            chosen_color = random.choice([c for c in Color if c != Color.WILD])
            self.current_wild_color = chosen_color
            first_discard.active_color = chosen_color
            print(f"Game starts with a Wild card. System chose {chosen_color.name} as the active color.")

        # Note: Effects of the very first card (like Draw 2, Skip, Reverse) on the first player
        # are complex and typically subject to house rules. This basic setup doesn't fully enact them.
        # A robust implementation would handle this state before the first player's actual turn.
        if first_discard.rank in [Rank.DRAW_TWO, Rank.SKIP, Rank.REVERSE] and not first_discard.is_wild():
             print(f"Warning: Game started with an action card: {first_discard}. Its effect on the first player is not fully implemented in this basic setup phase.")

    def get_current_player(self) -> Player:
        return self.players[self.current_player_index]

    def get_top_card(self) -> Optional[Card]:
        return self.deck.get_top_discard_card()

    def _get_player_at_offset(self, base_player_idx: int, offset: int) -> Player:
        # Calculates player index considering play direction and offset.
        # Note: offset is usually 1 for next, -1 for previous *in current direction*.
        # If offset is an absolute direction (e.g. -1 always means left), then play_direction isn't used here.
        # For GameActions, target_player_offset often implies direction already.
        target_idx = (base_player_idx + offset + len(self.players)) % len(self.players)
        return self.players[target_idx]

    def _advance_turn_marker(self, steps=1):
        self.current_player_index = (self.current_player_index + self.play_direction * steps) % len(self.players)

    def _handle_draw_pile_empty(self, drawing_player: Player) -> bool:
        if self.deck.needs_reshuffle():
            if drawing_player.shuffle_counters > 0:
                drawing_player.shuffle_counters -= 1
                print(f"{drawing_player.name} uses a shuffle counter ({drawing_player.shuffle_counters} remaining). Reshuffling discard pile...")
                self.deck.reshuffle_discard_pile_into_deck()
                if self.deck.is_empty():
                    print("Draw pile is still empty after reshuffle. No cards to draw.")
                    return False
            else:
                print(f"{drawing_player.name} needs to draw, draw pile empty, but has no shuffle counters. Draw is skipped.")
                return False
        elif self.deck.is_empty():
            print("Draw pile is empty and no cards in discard to reshuffle. No cards to draw.")
            return False
        return True

    def player_draws_card(self, player: Player, count: int = 1) -> List[Card]:
        drawn_cards: List[Card] = []
        for i in range(count):
            can_draw = self._handle_draw_pile_empty(player)
            if not can_draw: break
            card = self.deck.draw_card()
            if card: player.add_card_to_hand(card); drawn_cards.append(card)
            else: print(f"Warning: {player.name} tried to draw, but no card was available after check."); break
        return drawn_cards

    def _get_card_actions(self, card: Card, playing_player: Player, chosen_color_for_wild: Optional[Color] = None) -> List[GameAction]:
        actions: List[GameAction] = []
        player_name = playing_player.name
        player_idx = self.players.index(playing_player)

        if card.rank == Rank.SEVEN:
            actions.append(GameAction(ActionType.SWAP_CARD_RIGHT, message=f"{player_name} plays {card}, triggers card swap with player to the right."))
        elif card.rank == Rank.ZERO:
            actions.append(GameAction(ActionType.SWAP_CARD_ANY, message=f"{player_name} plays {card}, triggers card swap with any player."))
        elif card.color == Color.BLUE and card.rank == Rank.THREE:
            actions.append(GameAction(ActionType.DISCARD_FROM_PLAYER_HAND, target_player_offset=-self.play_direction,
                                      value={'count': 2, 'from_player_idx': player_idx}, # from_player_idx is who played Blue3
                                      message=f"{player_name} plays {card}. Player to the left must discard 2 cards from {player_name}'s hand."))
        elif card.color == Color.RED and card.rank == Rank.EIGHT:
            # Hand size check is for player who played the card, *after* it's played.
            # If hand_size > 0 means Red 8 was not their last card.
            if playing_player.hand_size() > 0:
                actions.append(GameAction(ActionType.PLAYER_DRAWS_FOUR_UNLESS_LAST, target_player_offset=0, # Target is self
                                           message=f"{player_name} plays {card} and draws 4 cards."))
            else:
                actions.append(GameAction(ActionType.NOP, message=f"{player_name} plays {card} as their last card. No draw effect."))
        elif card.rank == Rank.SIX:
            actions.append(GameAction(ActionType.PLAY_ANY_AND_DRAW_ONE, target_player_offset=0,
                                       message=f"{player_name} plays {card}. They can play any card next, then draw one."))
        elif card.color == Color.GREEN and card.rank == Rank.FIVE:
            actions.append(GameAction(ActionType.TAKE_RANDOM_FROM_PREVIOUS, target_player_offset=-self.play_direction,
                                       message=f"{player_name} plays {card} and takes a random card from the previous player."))
        elif card.rank == Rank.NINE:
            actions.append(GameAction(ActionType.PLACE_TOP_DRAW_PILE_CARD, message=f"{player_name} plays {card}. Top card from draw pile will be played."))

        # Rank 2 (discard all 2s on duplicate) is handled in play_turn directly, not as a GameAction from here.

        is_custom_effect_handled = any(a.type not in [ActionType.NOP, ActionType.CHOOSE_COLOR] for a in actions)

        if not is_custom_effect_handled: # Standard Uno actions if not overridden
            if card.is_wild():
                # If chosen_color_for_wild is already provided (e.g. by AI or UI), use it.
                # Otherwise, CHOOSE_COLOR action signals the need for input.
                if chosen_color_for_wild:
                     actions.append(GameAction(ActionType.CHOOSE_COLOR, value=chosen_color_for_wild,
                                               message_override=f"{player_name} chose {chosen_color_for_wild.name}."))
                else:
                     actions.append(GameAction(ActionType.CHOOSE_COLOR, value=None, message_override="Wild played, color must be chosen."))

                if card.rank == Rank.WILD_DRAW_FOUR:
                    actions.append(GameAction(ActionType.DRAW_CARDS, value=4, target_player_offset=1, message=f"Next player draws 4 cards."))
                    actions.append(GameAction(ActionType.SKIP_PLAYER, target_player_offset=1, message="and is skipped."))
            elif card.rank == Rank.DRAW_TWO:
                actions.append(GameAction(ActionType.DRAW_CARDS, value=2, target_player_offset=1, message=f"Next player draws 2 cards."))
                actions.append(GameAction(ActionType.SKIP_PLAYER, target_player_offset=1, message="and is skipped."))
            elif card.rank == Rank.SKIP:
                actions.append(GameAction(ActionType.SKIP_PLAYER, target_player_offset=1, message=f"Next player is skipped."))
            elif card.rank == Rank.REVERSE:
                actions.append(GameAction(ActionType.REVERSE_DIRECTION, message="Play direction reversed."))
                if len(self.players) == 2: actions.append(GameAction(ActionType.SKIP_PLAYER, target_player_offset=0, message="Acts like a Skip in a 2-player game."))

        if not actions: actions.append(GameAction(ActionType.NOP, message=""))
        return actions

    def _award_color_counters(self, player: Player, card: Card):
        if card.color == Color.RED: player.solar_mana += 1; print(f"{player.name} gained 1 Solar Mana (Total: {player.solar_mana}).")
        elif card.color == Color.YELLOW:
            player.coins += 1; print(f"{player.name} gained 1 Coin (Total: {player.coins}).")
            if card.rank == Rank.FOUR:
                if player.store_yellow_4_get_out_of_jail(card): print(f"{player.name}'s Yellow 4 moved to 'get out of jail free' pile.")
                else: print(f"{player.name} already has Yellow 4 stored.")
        elif card.color == Color.GREEN: player.shuffle_counters += 1; print(f"{player.name} gained 1 Shuffle Counter (Total: {player.shuffle_counters}).")
        elif card.color == Color.BLUE: player.lunar_mana += 1; print(f"{player.name} gained 1 Lunar Mana (Total: {player.lunar_mana}).")

    def play_turn(self, player: Player, card_index: Optional[int],
                  action_input: Optional[dict] = None,
                  chosen_color_for_wild: Optional[Color] = None) -> Tuple[bool, str, Optional[ActionType]]:
        current_turn_player_obj = self.get_current_player()

        if self.pending_action is None and player != current_turn_player_obj:
            return False, "It's not your turn.", None
        if self.game_over:
            return False, "The game is already over.", None

        message_parts = []
        next_action_needed: Optional[ActionType] = None

        # --- Part 1: Handle pending multi-step actions ---
        if self.pending_action:
            actor_for_pending = player # Player passed to this call is the one acting on the pending item.
            original_initiator_idx = self.action_data.get('original_player_idx', self.players.index(current_turn_player_obj))
            original_initiator = self.players[original_initiator_idx]

            if self.pending_action.type == ActionType.SWAP_CARD_RIGHT:
                if actor_for_pending != original_initiator: return False, "Not your turn for SWAP_CARD_RIGHT.", None
                # ... (SWAP_CARD_RIGHT logic as before, using actor_for_pending and original_initiator_idx for context) ...
                player_to_right = self._get_player_at_offset(original_initiator_idx, self.play_direction)
                card_to_give_idx = action_input.get('card_to_give_idx') if action_input else None
                card_to_take_idx = action_input.get('card_to_take_idx') if action_input else None
                if card_to_give_idx is None or card_to_take_idx is None: return False, "Card choices missing for swap.", ActionType.SWAP_CARD_RIGHT
                if not (0 <= card_to_give_idx < actor_for_pending.hand_size()): return False, f"Invalid card index to give.", ActionType.SWAP_CARD_RIGHT
                if player_to_right.is_hand_empty(): message_parts.append(f"{player_to_right.name}'s hand empty, swap cancelled.")
                elif not (0 <= card_to_take_idx < player_to_right.hand_size()): return False, f"Invalid card index to take.", ActionType.SWAP_CARD_RIGHT
                else:
                    card_given = actor_for_pending.play_card(card_to_give_idx)
                    card_taken = player_to_right.play_card(card_to_take_idx)
                    if card_given and card_taken:
                        actor_for_pending.add_card_to_hand(card_taken); player_to_right.add_card_to_hand(card_given)
                        message_parts.append(f"{actor_for_pending.name} gave {card_given} to {player_to_right.name}, took {card_taken}.")
                    else:
                        if card_given: actor_for_pending.add_card_to_hand(card_given)
                        if card_taken: player_to_right.add_card_to_hand(card_taken)
                        message_parts.append("Error in Rank 7 swap.")
                self.pending_action = None; self.action_data.clear(); self.current_player_index = original_initiator_idx; self._advance_turn_marker()
                return True, " ".join(filter(None, message_parts)), None

            elif self.pending_action.type == ActionType.SWAP_CARD_ANY:
                if actor_for_pending != original_initiator: return False, "Not your turn for SWAP_CARD_ANY.", None
                if 'target_player_idx' not in self.action_data:
                    target_idx_input = action_input.get('target_player_idx') if action_input else None
                    if target_idx_input is None or not (0 <= target_idx_input < len(self.players)) or target_idx_input == original_initiator_idx:
                        return False, "Invalid target player for Rank 0 swap.", ActionType.SWAP_CARD_ANY
                    self.action_data['target_player_idx'] = target_idx_input
                    message_parts.append(f"{actor_for_pending.name} targets {self.players[target_idx_input].name}.")
                    return True, " ".join(filter(None, message_parts)) + " Now choose cards.", ActionType.SWAP_CARD_ANY

                target_player = self.players[self.action_data['target_player_idx']]
                card_to_give_idx = action_input.get('card_to_give_idx') if action_input else None
                card_to_take_idx = action_input.get('card_to_take_idx') if action_input else None
                if card_to_give_idx is None or card_to_take_idx is None: return False, "Card choices missing.", ActionType.SWAP_CARD_ANY
                if not (0 <= card_to_give_idx < actor_for_pending.hand_size()): return False, f"Invalid card idx to give.", ActionType.SWAP_CARD_ANY
                if target_player.is_hand_empty(): message_parts.append(f"{target_player.name} hand empty, swap cancelled.")
                elif not (0 <= card_to_take_idx < target_player.hand_size()): return False, f"Invalid card idx to take.", ActionType.SWAP_CARD_ANY
                else:
                    card_given = actor_for_pending.play_card(card_to_give_idx); card_taken = target_player.play_card(card_to_take_idx)
                    if card_given and card_taken:
                        actor_for_pending.add_card_to_hand(card_taken); target_player.add_card_to_hand(card_given)
                        message_parts.append(f"{actor_for_pending.name} gave {card_given} to {target_player.name}, took {card_taken}.")
                    else:
                        if card_given: actor_for_pending.add_card_to_hand(card_given)
                        if card_taken: target_player.add_card_to_hand(card_taken)
                        message_parts.append("Error in Rank 0 swap.")
                self.pending_action = None; self.action_data.clear(); self.current_player_index = original_initiator_idx; self._advance_turn_marker()
                return True, " ".join(filter(None, message_parts)), None

            elif self.pending_action.type == ActionType.DISCARD_FROM_PLAYER_HAND:
                chooser = actor_for_pending
                victim_idx = self.action_data.get('victim_idx')
                expected_chooser_idx = self.action_data.get('chooser_idx')
                num_to_discard = self.action_data.get('count', 2)
                original_blue3_player_idx = self.action_data.get('original_player_idx', victim_idx)

                if victim_idx is None or expected_chooser_idx is None or self.players.index(chooser) != expected_chooser_idx:
                    return False, "Error: Mismatch in DISCARD_FROM_PLAYER_HAND context.", None
                victim = self.players[victim_idx]
                chosen_indices = action_input.get('chosen_indices_from_victim', []) if action_input else []

                actual_to_discard_count = min(num_to_discard, victim.hand_size())
                if not isinstance(chosen_indices, list) or len(set(chosen_indices)) != actual_to_discard_count:
                     return False, f"{chooser.name} must choose {actual_to_discard_count} distinct cards.", ActionType.DISCARD_FROM_PLAYER_HAND

                chosen_indices.sort(reverse=True)
                discarded_cards_str = []
                actually_discarded_cards_objects = []
                valid_indices = True
                for idx_to_pop in chosen_indices:
                    if not (0 <= idx_to_pop < victim.hand_size()): valid_indices=False; break
                    card_obj = victim.play_card(idx_to_pop)
                    if card_obj: actually_discarded_cards_objects.append(card_obj)
                    else: valid_indices = False; break

                if not valid_indices:
                    for c_obj in actually_discarded_cards_objects: victim.add_card_to_hand(c_obj) # Rollback
                    return False, "Error processing chosen discard indices.", ActionType.DISCARD_FROM_PLAYER_HAND

                for card_obj in actually_discarded_cards_objects:
                     self.deck.add_to_discard(card_obj); discarded_cards_str.append(str(card_obj))
                message_parts.append(f"{chooser.name} made {victim.name} discard: {', '.join(discarded_cards_str)}.")

                self.pending_action = None; self.action_data.clear()
                self.current_player_index = original_blue3_player_idx
                self._advance_turn_marker()
                return True, " ".join(filter(None, message_parts)), None

            elif self.pending_action.type == ActionType.PLAY_ANY_AND_DRAW_ONE:
                player_of_rank_6 = original_initiator
                if actor_for_pending != player_of_rank_6: return False, "Not your turn for Rank 6 effect.", None
                card_idx_for_effect = card_index
                color_for_wild_effect = action_input.get('chosen_color_for_rank_6_wild') if action_input else None

                if card_idx_for_effect is None: return False, "Must choose card for Rank 6.", ActionType.PLAY_ANY_AND_DRAW_ONE
                if not (0 <= card_idx_for_effect < player_of_rank_6.hand_size()): return False, "Invalid card index for Rank 6.", ActionType.PLAY_ANY_AND_DRAW_ONE

                card_to_play_freely = player_of_rank_6.hand[card_idx_for_effect]
                if card_to_play_freely.is_wild() and color_for_wild_effect is None:
                    self.action_data['is_for_rank_6_wild'] = True
                    self.action_data['rank_6_card_idx_pending_color'] = card_idx_for_effect
                    self.action_data['original_player_idx'] = self.players.index(player_of_rank_6)
                    self.pending_action = GameAction(ActionType.CHOOSE_COLOR)
                    return True, f"{player_of_rank_6.name} chose Wild {card_to_play_freely} for Rank 6. Choose color.", ActionType.CHOOSE_COLOR

                played_card_for_rank_6 = player_of_rank_6.play_card(card_idx_for_effect)
                message_parts.append(f"{player_of_rank_6.name} (Rank 6) plays {played_card_for_rank_6} freely.")
                self.deck.add_to_discard(played_card_for_rank_6)

                active_color_for_effects = None
                if played_card_for_rank_6.is_wild():
                    if color_for_wild_effect is None: return False, "Logic Error: Rank 6 Wild color missing.", None
                    self.current_wild_color = color_for_wild_effect; played_card_for_rank_6.active_color = color_for_wild_effect
                    active_color_for_effects = color_for_wild_effect; message_parts.append(f"Color chosen: {color_for_wild_effect.name}.")
                else: self.current_wild_color = None; active_color_for_effects = played_card_for_rank_6.color

                self._award_color_counters(player_of_rank_6, played_card_for_rank_6)
                actions_from_freely_played = self._get_card_actions(played_card_for_rank_6, player_of_rank_6, active_color_for_effects)

                skip_after_freely_played = False
                for item_action in actions_from_freely_played:
                    if item_action.message_override: message_parts.append(item_action.message_override)
                    if item_action.type == ActionType.GAME_WIN: self.game_over=True; self.winner=player_of_rank_6; break
                    if item_action.type == ActionType.DRAW_CARDS:
                        t_offset = item_action.target_player_offset if item_action.target_player_offset is not None else 1
                        victim = self._get_player_at_offset(original_initiator_idx, self.play_direction * t_offset)
                        self.player_draws_card(victim, item_action.value)
                    if item_action.type == ActionType.SKIP_PLAYER: skip_after_freely_played = True
                    if item_action.type == ActionType.REVERSE_DIRECTION: self.play_direction *= -1
                if self.game_over: return True, " ".join(filter(None,message_parts)), None

                message_parts.append(f"{player_of_rank_6.name} draws 1 card (Rank 6).")
                self.player_draws_card(player_of_rank_6, 1)
                self.pending_action = None; self.action_data.clear()
                self.current_player_index = original_initiator_idx; self._advance_turn_marker()
                if skip_after_freely_played: message_parts.append(f"{self.get_current_player().name} skipped."); self._advance_turn_marker()
                return True, " ".join(filter(None,message_parts)), None

            elif self.pending_action.type == ActionType.CHOOSE_COLOR:
                chosen_color_input = action_input.get('chosen_color') if action_input else None
                if not isinstance(chosen_color_input, Color) or chosen_color_input == Color.WILD:
                    return False, "Invalid color for Wild.", ActionType.CHOOSE_COLOR

                if self.action_data.get('is_for_rank_6_wild'):
                    rank_6_card_idx = self.action_data.pop('rank_6_card_idx_pending_color')
                    self.action_data.pop('is_for_rank_6_wild')
                    player_for_rank_6_idx = self.action_data.get('original_player_idx', self.players.index(actor_for_pending))
                    player_for_rank_6 = self.players[player_for_rank_6_idx]
                    message_parts.append(f"{player_for_rank_6.name} chose {chosen_color_input.name} for Rank 6 Wild.")
                    self.pending_action = GameAction(ActionType.PLAY_ANY_AND_DRAW_ONE)
                    return self.play_turn(player_for_rank_6, card_index=rank_6_card_idx, action_input={'chosen_color_for_rank_6_wild': chosen_color_input})
                else:
                    card_that_was_wild = self.action_data.get('card_played')
                    player_who_chose_idx = self.action_data.get('player_idx', self.players.index(actor_for_pending))
                    player_who_chose = self.players[player_who_chose_idx]
                    if not card_that_was_wild: return False, "Error: CHOOSE_COLOR context missing.", None

                    self.current_wild_color = chosen_color_input; card_that_was_wild.active_color = chosen_color_input
                    message_parts.append(f"{player_who_chose.name} chose {chosen_color_input.name} for {card_that_was_wild}.")
                    remaining_actions = self.action_data.pop('remaining_actions', [])
                    self.pending_action = None; self.action_data.clear()
                    skip_after_wild = False
                    for rem_action in remaining_actions:
                        if rem_action.message_override: message_parts.append(rem_action.message_override)
                        if rem_action.type == ActionType.DRAW_CARDS:
                            t_offset = rem_action.target_player_offset if rem_action.target_player_offset is not None else 1
                            victim = self._get_player_at_offset(player_who_chose_idx, self.play_direction * t_offset)
                            self.player_draws_card(victim, rem_action.value)
                        if rem_action.type == ActionType.SKIP_PLAYER: skip_after_wild = True

                    self.current_player_index = player_who_chose_idx; self._advance_turn_marker()
                    if skip_after_wild: message_parts.append(f"{self.get_current_player().name} skipped."); self._advance_turn_marker()
                    return True, " ".join(filter(None,message_parts)), None

        # --- Part 2: Standard card play (if no pending_action was handled) ---
        # Player here is current_turn_player_obj for a new play.
        if card_index is None: return False, "No card played or pending action.", None
        if not (0 <= card_index < player.hand_size()): return False, "Invalid card index.", None

        card_to_play_peek = player.hand[card_index]
        top_discard = self.get_top_card()
        if not top_discard: return False, "Error: No card on discard pile.", None

        if not card_to_play_peek.matches(top_discard, self.current_wild_color):
            return False, f"Cannot play {card_to_play_peek} on {top_discard} (Active: {self.current_wild_color}).", None

        played_card = player.play_card(card_index)
        if not played_card: return False, "Error retrieving card.", None

        message_parts.append(GameAction.card_played_message(player.name, str(played_card), player.hand_size() == 1))

        # --- Handle Rank 2 duplicate rule ---
        # This check happens *after* card is played and *before* its own actions are fetched.
        card_underneath = self.deck.get_top_discard_card() # Card that was top before this play
        self.deck.add_to_discard(played_card) # Now played_card is on top

        if card_underneath and \
           played_card.rank == card_underneath.rank and \
           played_card.color == card_underneath.color: # It's a duplicate play
            twos_in_hand = [c for c in player.hand if c.rank == Rank.TWO]
            if twos_in_hand:
                message_parts.append(f"{player.name} played a duplicate {played_card}! Discarding all 2s.")
                for two_card in twos_in_hand:
                    player.remove_card_from_hand(two_card)
                    self.deck.add_to_discard(two_card) # 2s go to discard
                    message_parts.append(f"{player.name} discards {two_card}.")
                if player.is_hand_empty(): # Win by discarding last 2s
                    self.game_over = True; self.winner = player
                    message_parts.append(f" {player.name} wins by discarding last 2s after duplicate play!")
                    return True, " ".join(filter(None, message_parts)), None

        if not played_card.is_wild(): self.current_wild_color = None
        self._award_color_counters(player, played_card)

        # If chosen_color_for_wild was None for a Wild card, _get_card_actions will return CHOOSE_COLOR action.
        actions_to_process = self._get_card_actions(played_card, player, chosen_color_for_wild if played_card.is_wild() else None)

        if player.is_hand_empty() and not any(a.type == ActionType.GAME_WIN for a in actions_to_process):
            actions_to_process = [GameAction(ActionType.GAME_WIN)]

        # --- Part 3: Process actions from the just-played card ---
        skip_next_player_flag = False
        advance_turn_normally = True
        action_idx = 0
        while action_idx < len(actions_to_process):
            action = actions_to_process[action_idx]; action_idx +=1
            if action.message_override: message_parts.append(action.message_override)

            if action.type == ActionType.GAME_WIN:
                self.game_over = True; self.winner = player
                message_parts.append(f" {player.name} wins the game!")
                return True, " ".join(filter(None, message_parts)), None
            elif action.type == ActionType.CHOOSE_COLOR:
                if action.value:
                    self.current_wild_color = action.value
                    if played_card and played_card.is_wild(): played_card.active_color = action.value
                else:
                    self.pending_action = action
                    self.action_data = {'card_played': played_card, 'remaining_actions': actions_to_process[action_idx:], 'player_idx': self.players.index(player), 'original_player_idx': self.players.index(player)}
                    return True, " ".join(filter(None, message_parts)) + f" {player.name} needs to choose color.", ActionType.CHOOSE_COLOR
            elif action.type == ActionType.DRAW_CARDS:
                t_offset = action.target_player_offset if action.target_player_offset is not None else 1
                victim = self._get_player_at_offset(self.players.index(player), self.play_direction * t_offset)
                self.player_draws_card(victim, action.value)
            elif action.type == ActionType.SKIP_PLAYER: skip_next_player_flag = True
            elif action.type == ActionType.REVERSE_DIRECTION: self.play_direction *= -1
            elif action.type in [ActionType.SWAP_CARD_RIGHT, ActionType.SWAP_CARD_ANY, ActionType.DISCARD_FROM_PLAYER_HAND, ActionType.PLAY_ANY_AND_DRAW_ONE]:
                self.pending_action = action
                self.action_data = {'original_card': played_card, 'remaining_actions': actions_to_process[action_idx:], 'original_player_idx': self.players.index(player)}
                # Specific data for each type
                if action.type == ActionType.DISCARD_FROM_PLAYER_HAND:
                    self.action_data['chooser_idx'] = self.players.index(self._get_player_at_offset(self.players.index(player), self.play_direction * action.target_player_offset))
                    self.action_data['victim_idx'] = self.players.index(player) # Who played Blue 3
                    self.action_data['count'] = action.value['count']
                # For SWAP_CARD_RIGHT/ANY, PLAY_ANY_AND_DRAW_ONE, 'original_player_idx' is who initiated.
                next_action_needed = action.type
                advance_turn_normally = False; break
            elif action.type == ActionType.PLAYER_DRAWS_FOUR_UNLESS_LAST:
                self.player_draws_card(player, 4)
            elif action.type == ActionType.TAKE_RANDOM_FROM_PREVIOUS:
                prev_player_idx = (self.players.index(player) - self.play_direction + len(self.players)) % len(self.players)
                previous_player = self.players[prev_player_idx]
                if not previous_player.is_hand_empty():
                    card_to_take = random.choice(previous_player.hand)
                    removed_card = previous_player.remove_card_from_hand(card_to_take)
                    if removed_card: player.add_card_to_hand(removed_card); message_parts.append(f"{player.name} took {removed_card} from {previous_player.name} (Green 5).")
                    else: message_parts.append(f"Error taking card from {previous_player.name} for Green 5.")
                else: message_parts.append(f"{previous_player.name}'s hand is empty for Green 5.")
            elif action.type == ActionType.PLACE_TOP_DRAW_PILE_CARD: # Rank 9
                if not self._handle_draw_pile_empty(player):
                    message_parts.append("Rank 9: Draw pile empty, no card to place.")
                else:
                    new_top_card = self.deck.draw_card()
                    if new_top_card:
                        message_parts.append(f"Rank 9 places {new_top_card} from draw pile.")
                        self.deck.add_to_discard(new_top_card)
                        if not new_top_card.is_wild(): self.current_wild_color = None

                        new_card_sub_actions = self._get_card_actions(new_top_card, player, None) # Player who played 9 chooses color if new is Wild
                        temp_skip_for_rank9_card = False
                        rank9_card_ends_turn = False

                        for sub_a in new_card_sub_actions: # Process sub-actions
                            if sub_a.message_override: message_parts.append(f"({new_top_card}): {sub_a.message_override}")
                            if sub_a.type == ActionType.CHOOSE_COLOR:
                                if sub_a.value: self.current_wild_color = sub_a.value; new_top_card.active_color = sub_a.value
                                else: # Rank 9 placed a Wild, current player needs to choose
                                    self.pending_action = sub_a
                                    self.action_data = {'card_played': new_top_card, 'player_idx': self.players.index(player), 'original_player_idx': self.players.index(player)}
                                    next_action_needed = ActionType.CHOOSE_COLOR; advance_turn_normally=False; rank9_card_ends_turn=True; break
                            elif sub_a.type == ActionType.DRAW_CARDS:
                                t_offset_sub = sub_a.target_player_offset if sub_a.target_player_offset is not None else 1
                                victim_sub = self._get_player_at_offset(self.players.index(player), self.play_direction * t_offset_sub)
                                self.player_draws_card(victim_sub, sub_a.value)
                                if t_offset_sub == 1: rank9_card_ends_turn = True # If it's a Draw affecting next player
                            elif sub_a.type == ActionType.SKIP_PLAYER: temp_skip_for_rank9_card = True; rank9_card_ends_turn = True
                            elif sub_a.type == ActionType.REVERSE_DIRECTION:
                                self.play_direction *= -1
                                if len(self.players) == 2: temp_skip_for_rank9_card = True; rank9_card_ends_turn = True
                                # else, for >2p, if player can play on new card, turn might not end.

                        if next_action_needed == ActionType.CHOOSE_COLOR: break # Break outer loop for CHOOSE_COLOR

                        if rank9_card_ends_turn:
                            skip_next_player_flag = temp_skip_for_rank9_card # If Rank 9 card caused skip
                        elif player.has_playable_card(new_top_card, self.current_wild_color): # Player can play on new card
                            message_parts.append(f"{player.name} may play again on {new_top_card}.")
                            advance_turn_normally = False # Player's turn continues
                        else: # Cannot play on new card
                             message_parts.append(f"{player.name} cannot play on {new_top_card}. Turn ends.")
                             advance_turn_normally = True # Ensure turn advances
                    else: message_parts.append("Rank 9: Failed to draw card.")
            elif action.type == ActionType.NOP: pass

        if self.game_over: return True, " ".join(filter(None, message_parts)), None
        if next_action_needed: return True, " ".join(filter(None, message_parts)), next_action_needed

        if advance_turn_normally:
            self.current_player_index = self.players.index(player)
            self._advance_turn_marker()
            if skip_next_player_flag:
                message_parts.append(f"{self.get_current_player().name}'s turn is skipped.")
                self._advance_turn_marker()
        return True, " ".join(filter(None, message_parts)), None

    def player_cannot_play_action(self, player: Player) -> Tuple[bool, str]:
        # ... (rest of the class and __main__ block remains the same as the last successful overwrite)
        # This method needs to be robust to pending actions too.
        current_turn_player = self.get_current_player()
        if player != current_turn_player: return False, "It's not your turn."
        if self.game_over: return False, "The game is already over."

        actor_for_pending_input = player # By default, current player
        if self.pending_action:
            if self.pending_action.type == ActionType.DISCARD_FROM_PLAYER_HAND:
                actor_for_pending_input = self.players[self.action_data.get('chooser_idx', self.players.index(player))]
            elif self.pending_action.type in [ActionType.SWAP_CARD_RIGHT, ActionType.SWAP_CARD_ANY, ActionType.PLAY_ANY_AND_DRAW_ONE, ActionType.CHOOSE_COLOR]:
                 actor_idx = self.action_data.get('original_player_idx', self.action_data.get('player_idx', self.players.index(player)))
                 actor_for_pending_input = self.players[actor_idx]

        if self.pending_action and actor_for_pending_input == player :
             return False, f"Cannot 'draw card' while pending action '{self.pending_action.type.name}' requires your input."

        message_parts = [f"{player.name} cannot play, so they draw a card."]
        drawn_cards = self.player_draws_card(player, 1)

        if not drawn_cards:
            message_parts.append("No card was drawn. Turn passes.")
            self.current_player_index = self.players.index(player)
            self._advance_turn_marker()
            return True, " ".join(message_parts)

        drawn_card = drawn_cards[0]
        message_parts.append(f"{player.name} drew {drawn_card}.")

        top_discard = self.get_top_card()
        # Player may play the drawn card if it's playable (standard Uno).
        if top_discard and drawn_card.matches(top_discard, self.current_wild_color):
            message_parts.append(f"The drawn card ({drawn_card}) is playable.")
            # Simulate auto-playing it for now
            player.remove_card_from_hand(drawn_card)

            chosen_color_for_drawn_wild = None
            active_color_after_drawn_play = None
            if drawn_card.is_wild():
                chosen_color_for_drawn_wild = random.choice([c for c in Color if c != Color.WILD])
                message_parts.append(f"{player.name} chose {chosen_color_for_drawn_wild.name} for the drawn Wild.")
                active_color_after_drawn_play = chosen_color_for_drawn_wild
            else:
                active_color_after_drawn_play = drawn_card.color

            message_parts.append(GameAction.card_played_message(player.name, f"drawn {drawn_card}", player.hand_size() == 1))

            self.deck.add_to_discard(drawn_card)
            if not drawn_card.is_wild(): self.current_wild_color = None
            elif chosen_color_for_drawn_wild:
                self.current_wild_color = chosen_color_for_drawn_wild
                drawn_card.active_color = chosen_color_for_drawn_wild

            self._award_color_counters(player, drawn_card)

            if player.is_hand_empty():
                self.game_over = True; self.winner = player
                message_parts.append(f" {player.name} played their last card ({drawn_card}) and wins!")
                return True, " ".join(filter(None, message_parts))

            actions_from_drawn = self._get_card_actions(drawn_card, player, active_color_after_drawn_play)
            skip_after_drawn = False
            for action in actions_from_drawn:
                if action.message_override: message_parts.append(action.message_override)
                if action.type == ActionType.GAME_WIN: self.game_over=True; self.winner=player; break
                if action.type == ActionType.DRAW_CARDS:
                    t_offset = action.target_player_offset if action.target_player_offset is not None else 1
                    victim = self._get_player_at_offset(self.players.index(player), self.play_direction * t_offset)
                    self.player_draws_card(victim, action.value)
                if action.type == ActionType.SKIP_PLAYER: skip_after_drawn = True
                if action.type == ActionType.REVERSE_DIRECTION: self.play_direction *= -1

            if self.game_over: return True, " ".join(filter(None, message_parts))
            self.current_player_index = self.players.index(player)
            self._advance_turn_marker()
            if skip_after_drawn:
                message_parts.append(f"{self.get_current_player().name}'s turn is skipped.")
                self._advance_turn_marker()
            return True, " ".join(filter(None, message_parts))
        else:
            message_parts.append(f"The drawn card ({drawn_card}) is not playable. Turn ends.")
            self.current_player_index = self.players.index(player)
            self._advance_turn_marker()
            return True, " ".join(filter(None, message_parts))

    def get_game_status(self):
        if self.game_over:
            return f"Game Over! Winner: {self.winner.name if self.winner else 'None'}"
        status = []
        top_card = self.get_top_card()
        active_color_str = f"(Active: {self.current_wild_color.name})" if self.current_wild_color and top_card and top_card.is_wild() else ""
        status.append(f"Top Card: {top_card} {active_color_str}")

        current_player_obj = self.get_current_player()
        actor_display_name = current_player_obj.name
        pending_action_for_whom = current_player_obj.name

        if self.pending_action:
            actor_idx = self.action_data.get('original_player_idx', # For Rank 6, etc.
                             self.action_data.get('player_idx', # For CHOOSE_COLOR (non-Rank 6)
                             self.action_data.get('victim_idx'))) # For DISCARD (victim is original Blue3 player)

            if self.pending_action.type == ActionType.DISCARD_FROM_PLAYER_HAND:
                actor_idx = self.action_data.get('chooser_idx') # Chooser is the actor

            if actor_idx is not None:
                pending_action_for_whom = self.players[actor_idx].name
            elif 'player' in self.action_data: # For SWAP actions
                pending_action_for_whom = self.action_data['player'].name


        status.append(f"Current Player: {current_player_obj.name}")
        if self.pending_action:
            status.append(f"Pending Action: {self.pending_action.type.name} (requiring input from {pending_action_for_whom})")

        status.append(f"Play Direction: {'Forward' if self.play_direction == 1 else 'Backward'}")
        status.append("Players:")
        for p in self.players:
            details = f"{p.hand_size()} cards"
            counters_list = []
            if p.coins > 0: counters_list.append(f"C:{p.coins}")
            if p.shuffle_counters > 0: counters_list.append(f"S:{p.shuffle_counters}")
            if p.lunar_mana > 0: counters_list.append(f"L:{p.lunar_mana}")
            if p.solar_mana > 0: counters_list.append(f"Sol:{p.solar_mana}")
            if p.get_out_of_jail_yellow_4: counters_list.append("Y4Jail")
            if counters_list: details += " (" + ", ".join(counters_list) + ")"
            status.append(f"  - {p.name}: {details}")
        status.append(f"Draw pile size: {len(self.deck.cards)}")
        return "\n".join(status)

if __name__ == '__main__':
    game = UnoGame(["Alice", "Bob", "Charlie", "Dave"])
    print("Initial game state:")
    print(game.get_game_status())

    max_turns = 250 # Increased for more complex games
    for turn_num in range(max_turns):
        if game.game_over:
            print(f"\n--- Game Over on Turn {turn_num + 1} ---")
            break

        # Determine who is providing input for this step of the turn
        actor_player = game.get_current_player() # Default actor is whose turn it is
        if game.pending_action:
            if game.pending_action.type == ActionType.DISCARD_FROM_PLAYER_HAND:
                 actor_player = game.players[game.action_data.get('chooser_idx')]
            elif game.pending_action.type == ActionType.CHOOSE_COLOR and game.action_data.get('is_for_rank_6_wild'):
                 actor_player = game.players[game.action_data.get('original_player_idx')]
            elif 'player' in game.action_data: # SWAP_CARD_RIGHT, SWAP_CARD_ANY store player object
                 actor_player = game.action_data.get('player')
            elif 'player_idx' in game.action_data: # CHOOSE_COLOR (normal), PLAY_ANY_AND_DRAW_ONE
                 actor_player = game.players[game.action_data.get('player_idx')]
            # If original_player_idx is present, it's the one who initiated the multi-step action
            elif 'original_player_idx' in game.action_data:
                 actor_player = game.players[game.action_data.get('original_player_idx')]


        print(f"\n--- Turn {turn_num + 1}: Main turn for {game.get_current_player().name}, Input from {actor_player.name} ---")
        print(f"{actor_player.name}'s Hand: {actor_player.get_hand_display()}")

        turn_message = ""
        action_input_sim = {}
        card_idx_sim = None

        if game.pending_action:
            print(f"Sim: Handling pending action {game.pending_action.type.name} for {actor_player.name}.")

            if game.pending_action.type == ActionType.SWAP_CARD_RIGHT :
                if not actor_player.is_hand_empty(): action_input_sim['card_to_give_idx'] = random.randint(0, actor_player.hand_size()-1)
                else: action_input_sim['card_to_give_idx'] = 0
                player_to_right_idx = (game.players.index(actor_player) + game.play_direction) % len(game.players)
                player_to_right = game.players[player_to_right_idx]
                if not player_to_right.is_hand_empty(): action_input_sim['card_to_take_idx'] = random.randint(0, player_to_right.hand_size()-1)
                else: action_input_sim['card_to_take_idx'] = 0

            elif game.pending_action.type == ActionType.SWAP_CARD_ANY:
                if 'target_player_idx' not in game.action_data:
                    possible_targets = [i for i, p in enumerate(game.players) if i != game.players.index(actor_player)]
                    action_input_sim['target_player_idx'] = random.choice(possible_targets) if possible_targets else (game.players.index(actor_player) + 1) % len(game.players)
                else:
                    target_player = game.players[game.action_data['target_player_idx']]
                    if not actor_player.is_hand_empty(): action_input_sim['card_to_give_idx'] = random.randint(0, actor_player.hand_size()-1)
                    else: action_input_sim['card_to_give_idx'] = 0
                    if not target_player.is_hand_empty(): action_input_sim['card_to_take_idx'] = random.randint(0, target_player.hand_size()-1)
                    else: action_input_sim['card_to_take_idx'] = 0

            elif game.pending_action.type == ActionType.DISCARD_FROM_PLAYER_HAND:
                victim = game.players[game.action_data['victim_idx']]
                num_to_pick = min(victim.hand_size(), game.action_data.get('count',2))
                if victim.hand_size() > 0: action_input_sim['chosen_indices_from_victim'] = random.sample(range(victim.hand_size()), num_to_pick)
                else: action_input_sim['chosen_indices_from_victim'] = []

            elif game.pending_action.type == ActionType.PLAY_ANY_AND_DRAW_ONE:
                if not actor_player.is_hand_empty():
                    card_idx_sim = random.randint(0, actor_player.hand_size() -1)
                    chosen_card_for_rank6 = actor_player.hand[card_idx_sim]
                    if chosen_card_for_rank6.is_wild():
                        action_input_sim['chosen_color_for_rank_6_wild'] = random.choice([c for c in Color if c != Color.WILD])
                else: card_idx_sim = 0 # Will fail if hand empty, game logic should handle

            elif game.pending_action.type == ActionType.CHOOSE_COLOR:
                action_input_sim['chosen_color'] = random.choice([c for c in Color if c != Color.WILD])

            print(f"Sim input for {game.pending_action.type.name}: card_idx={card_idx_sim}, action_input={action_input_sim}")
            success, message_pending, next_action_prompt = game.play_turn(actor_player, card_idx_sim, action_input_sim)
            turn_message = message_pending
            if not success: print(f"Error completing pending action: {message_pending}")
            if next_action_prompt: print(f"SIM: Pending action for {actor_player.name} resulted in new prompt: {next_action_prompt}")

        else: # No pending action, normal play by current_turn_player_obj
            playable_cards_indices = [i for i, card in enumerate(actor_player.hand)
                                      if card.matches(game.get_top_card(), game.current_wild_color)]

            if playable_cards_indices:
                card_idx_sim = random.choice(playable_cards_indices)
                card_being_played = actor_player.hand[card_idx_sim]
                chosen_color_sim_val = None
                if card_being_played.is_wild():
                    chosen_color_sim_val = random.choice([c for c in Color if c != Color.WILD])

                success, message_play, next_action_prompt = game.play_turn(actor_player, card_idx_sim, chosen_color_for_wild=chosen_color_sim_val)
                turn_message = message_play
                if not success: print(f"Play failed: {message_play}")
                if next_action_prompt: print(f"SIM: Normal play by {actor_player.name} resulted in prompt: {next_action_prompt}")
            else:
                if actor_player.has_get_out_of_jail_card():
                    y4 = actor_player.get_out_of_jail_yellow_4
                    if y4 and y4.matches(game.get_top_card(), game.current_wild_color):
                        actor_player.use_get_out_of_jail_card()
                        game.deck.add_to_discard(y4)
                        game.current_wild_color = None
                        game._award_color_counters(actor_player, y4)
                        turn_message = f"{actor_player.name} uses 'Get Out of Jail Free' Yellow 4."
                        if actor_player.is_hand_empty(): game.game_over=True; game.winner=actor_player; turn_message+= " And WINS!"
                        else: game.current_player_index = game.players.index(actor_player); game._advance_turn_marker()
                    else:
                        if y4: actor_player.store_yellow_4_get_out_of_jail(y4)
                        success, message_draw = game.player_cannot_play_action(actor_player)
                        turn_message = message_draw
                else:
                    success, message_draw = game.player_cannot_play_action(actor_player)
                    turn_message = message_draw

        print(turn_message.strip())
        print(game.get_game_status())

    print("\n--- Final Game Status ---")
    print(game.get_game_status())
    if not game.game_over: print(f"\nGame ended due to max turns ({max_turns}).")
    elif game.winner: print(f"\nWinner: {game.winner.name}")
    else: print("\nGame over, but winner not set.")

    print("\nFinal Player Hands & Counters:")
    for p_final in game.players:
        counters_list_final = []
        if p_final.coins > 0: counters_list_final.append(f"C:{p_final.coins}")
        if p_final.shuffle_counters > 0: counters_list_final.append(f"S:{p_final.shuffle_counters}")
        if p_final.lunar_mana > 0: counters_list_final.append(f"L:{p_final.lunar_mana}")
        if p_final.solar_mana > 0: counters_list_final.append(f"Sol:{p_final.solar_mana}")
        if p_final.get_out_of_jail_yellow_4: counters_list_final.append("Y4Jail")
        counter_str_final = ", ".join(counters_list_final)
        hand_str_final = p_final.get_hand_display(show_indices=False) if p_final.hand_size() > 0 else "Empty"
        print(f"{p_final.name}: {hand_str_final} --- Counters: [{counter_str_final if counter_str_final else 'None'}]")
