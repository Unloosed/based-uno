from flask import Flask, jsonify, request
from uno_game.src.game import UnoGame
from uno_game.src.player import Player
from uno_game.src.card import Color
from uno_game.src.actions import ActionType

app = Flask(__name__)

# Initialize a global game instance for simplicity
# In a real application, you'd manage game instances differently (e.g., sessions, database)
try:
    # Using a default set of players for now. This could be configurable.
    game = UnoGame(player_names=["Player 1", "CPU 1", "CPU 2", "CPU 3"])
except ValueError as e:
    print(f"Error initializing game: {e}")
    game = None

def get_player_by_name(player_name: str) -> Player | None:
    if not game:
        return None
    for p in game.players:
        if p.name == player_name:
            return p
    return None

@app.route('/api/game_state', methods=['GET'])
def get_game_state():
    if game:
        return jsonify(game.to_dict())
    else:
        return jsonify({"error": "Game not initialized"}), 500

@app.route('/api/play_card', methods=['POST'])
def play_card():
    if not game:
        return jsonify({"error": "Game not initialized"}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400

    player_name = data.get('player_name')
    card_index_str = data.get('card_index')
    chosen_color_str = data.get('chosen_color') # e.g., "RED", "BLUE"

    if not player_name or card_index_str is None:
        return jsonify({"error": "Missing player_name or card_index"}), 400

    try:
        card_index = int(card_index_str)
    except ValueError:
        return jsonify({"error": "Invalid card_index format"}), 400

    player = get_player_by_name(player_name)
    if not player:
        return jsonify({"error": f"Player {player_name} not found"}), 404

    current_player_obj = game.get_current_player()
    actor_player = current_player_obj # Default actor

    # Determine if this play is for a pending action or a new turn action
    is_pending_action_play = False
    if game.pending_action:
        # If the pending action is PLAY_ANY_AND_DRAW_ONE (Rank 6),
        # this endpoint is used to play the "any card".
        # The actor for Rank 6 is the one who played the Rank 6 card.
        if game.pending_action.type == ActionType.PLAY_ANY_AND_DRAW_ONE:
            original_player_idx = game.action_data.get("original_player_idx")
            if original_player_idx is not None and game.players[original_player_idx] == player:
                actor_player = player
                is_pending_action_play = True
            else: # Not the correct player for this pending action
                 return jsonify({"error": f"Player {player_name} is not the one to act on pending {game.pending_action.type.name}"}), 403
        # Other pending actions that might involve playing a card would need similar checks.
        # For now, play_card is primarily for standard plays or the Rank 6 specific case.

    if not is_pending_action_play and player != current_player_obj and game.pending_action is None:
        return jsonify({"error": f"It's not {player_name}'s turn. Current player: {current_player_obj.name}"}), 403

    # This actor_player will be passed to play_turn.
    # If it's a normal turn, actor_player == player == current_player_obj.
    # If it's for Rank 6, actor_player is the player who played Rank 6.

    chosen_color_enum: Color | None = None
    if chosen_color_str:
        try:
            chosen_color_enum = Color[chosen_color_str.upper()]
            if chosen_color_enum == Color.WILD:
                return jsonify({"error": "Cannot choose WILD as an active color"}), 400
        except KeyError:
            return jsonify({"error": f"Invalid color string: {chosen_color_str}"}), 400

    # If this play is for a pending Rank 6, the action_input needs to be structured correctly
    action_input_for_rank6 = None
    if is_pending_action_play and game.pending_action and game.pending_action.type == ActionType.PLAY_ANY_AND_DRAW_ONE:
        # The card_index is the card being played for Rank 6.
        # If that card is wild, chosen_color_enum is its chosen color.
        action_input_for_rank6 = {}
        peek_card = actor_player.hand[card_index] # card_index already validated by play_turn
        if peek_card.is_wild():
            if not chosen_color_enum:
                 # If the card played for Rank 6 is Wild, a color must be provided now or it will prompt.
                 # For API, better to require it if the card is Wild.
                 # However, game.play_turn handles prompting if chosen_color_for_wild is None.
                 # We will pass chosen_color_enum (which might be None) and let play_turn manage.
                pass # chosen_color_enum might be None, play_turn will handle CHOOSE_COLOR if needed
            action_input_for_rank6["chosen_color_for_rank_6_wild"] = chosen_color_enum


    success, message, next_action_prompt = game.play_turn(
        actor_player, # The player making the move (could be for their turn, or for Rank 6)
        card_index,
        action_input=action_input_for_rank6, # Only for Rank 6 pending action
        chosen_color_for_wild=chosen_color_enum if not is_pending_action_play else None # For regular wild plays
    )

    if not success:
        return jsonify({"error": message, "game_state": game.to_dict(), "next_action_prompt": next_action_prompt.name if next_action_prompt else None}), 400

    response = {
        "message": message,
        "game_state": game.to_dict(),
        "next_action_prompt": next_action_prompt.name if next_action_prompt else None
    }
    return jsonify(response)

@app.route('/api/provide_action_input', methods=['POST'])
def provide_action_input():
    if not game:
        return jsonify({"error": "Game not initialized"}), 500
    if not game.pending_action:
        return jsonify({"error": "No pending action requiring input"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400

    player_name = data.get('player_name')
    action_input_data = data.get('action_input') # This is expected to be a dict

    if not player_name or action_input_data is None:
        return jsonify({"error": "Missing player_name or action_input"}), 400
    if not isinstance(action_input_data, dict):
        return jsonify({"error": "action_input must be a dictionary"}), 400


    player = get_player_by_name(player_name)
    if not player:
        return jsonify({"error": f"Player {player_name} not found"}), 404

    # Determine the actual actor for the pending action based on game.action_data
    # This is crucial because the 'player_name' in the request must match the player
    # the game expects to provide input for the current pending_action.
    expected_actor = None
    pending_action_type = game.pending_action.type

    if pending_action_type == ActionType.CHOOSE_COLOR:
        # For CHOOSE_COLOR, the actor could be the one who played a normal Wild,
        # or the one who played a Rank 6 that resulted in playing a Wild.
        if game.action_data.get("is_for_rank_6_wild"):
            original_player_idx = game.action_data.get("original_player_idx")
            if original_player_idx is not None:
                expected_actor = game.players[original_player_idx]
        else: # Standard wild card play
            player_idx = game.action_data.get("player_idx")
            if player_idx is not None:
                expected_actor = game.players[player_idx]
    elif pending_action_type in [ActionType.SWAP_CARD_RIGHT, ActionType.SWAP_CARD_ANY, ActionType.PLAY_ANY_AND_DRAW_ONE]:
        # These actions are typically continued by the player who initiated them.
        original_player_idx = game.action_data.get("original_player_idx")
        if original_player_idx is not None:
            expected_actor = game.players[original_player_idx]
    elif pending_action_type == ActionType.DISCARD_FROM_PLAYER_HAND:
        # The 'chooser' makes the decision.
        chooser_idx = game.action_data.get("chooser_idx")
        if chooser_idx is not None:
            expected_actor = game.players[chooser_idx]

    if not expected_actor: # Fallback or error if logic above doesn't set it
        # This might indicate an issue with action_data setup or a new pending action type
        current_game_player = game.get_current_player()
        # A rough guess, but play_turn will ultimately validate
        expected_actor_idx_guess = game.action_data.get("original_player_idx", game.action_data.get("player_idx", game.players.index(current_game_player)))
        if isinstance(expected_actor_idx_guess, int):
            expected_actor = game.players[expected_actor_idx_guess]
        else: # Should not happen if action_data is well-formed
             return jsonify({"error": "Could not determine expected player for pending action from game state."}), 500


    if player != expected_actor:
        return jsonify({"error": f"Player {player_name} is not the one expected to provide input for {pending_action_type.name}. Expected {expected_actor.name}."}), 403

    # Sanitize/transform inputs from action_input_data if necessary
    # e.g., string "RED" to Color.RED for "chosen_color"
    if 'chosen_color' in action_input_data and isinstance(action_input_data['chosen_color'], str):
        try:
            color_str = action_input_data['chosen_color'].upper()
            action_input_data['chosen_color'] = Color[color_str]
            if action_input_data['chosen_color'] == Color.WILD:
                 return jsonify({"error": "Cannot choose WILD as an active color"}), 400
        except KeyError:
            return jsonify({"error": f"Invalid color string in action_input: {action_input_data['chosen_color']}"}), 400

    # For PLAY_ANY_AND_DRAW_ONE (Rank 6) part 2 (choosing color for the wild played by Rank 6)
    # The `play_card` endpoint handles the initial play of Rank 6 and the card played by its effect.
    # This `provide_action_input` is for *other* pending actions.
    # If CHOOSE_COLOR is pending due to Rank 6 playing a wild, action_input_data should contain 'chosen_color'.
    # The `game.play_turn` method's `action_input` parameter is used for the actual data.
    # `card_index` would be None unless the pending action itself involves selecting another card from hand *now*.
    # Most pending actions processed here (like CHOOSE_COLOR, SWAP choices) don't use card_index from the current player's hand *again*
    # unless it's the specific card_index for PLAY_ANY_AND_DRAW_ONE's first part, which is handled by /api/play_card.

    # The `play_turn` method expects `card_index` to be `None` if we are only providing `action_input`
    # for a pending action that doesn't involve playing a new card from hand at this specific step.
    # However, if the pending action was PLAY_ANY_AND_DRAW_ONE and it's waiting for the *card to be played*,
    # that's handled by `/api/play_card`. This endpoint is for inputs like color choice, swap choices etc.

    card_idx_for_pending = None # Default for most pending actions
    # If the pending action was CHOOSE_COLOR that originated from a Rank 6 playing a wild,
    # the `play_turn` call needs to be "re-entrant" for the PLAY_ANY_AND_DRAW_ONE logic.
    # The `game.play_turn` itself manages this re-entrancy if `action_data` is set up correctly
    # (e.g., with `is_for_rank_6_wild` and `rank_6_card_idx_pending_color`).
    # The API just needs to pass the `action_input_data` (which would contain `chosen_color`).
    # `card_index` for the `play_turn` call should be the `rank_6_card_idx_pending_color` if that's the context.

    if pending_action_type == ActionType.CHOOSE_COLOR and game.action_data.get("is_for_rank_6_wild"):
        card_idx_for_pending = game.action_data.get("rank_6_card_idx_pending_color")
        # The action_input_data should contain "chosen_color" which will be used by play_turn.
        # To ensure play_turn routes correctly for Rank 6's CHOOSE_COLOR,
        # we need to ensure the `action_input` passed to `play_turn` is structured
        # as expected by the Rank 6 CHOOSE_COLOR handling logic within `play_turn`.
        # `play_turn` expects `chosen_color_for_rank_6_wild` within its `action_input` parameter.
        if 'chosen_color' in action_input_data:
            action_input_data["chosen_color_for_rank_6_wild"] = action_input_data.pop('chosen_color')


    success, message, next_action_prompt = game.play_turn(
        player, # The player providing the input
        card_index=card_idx_for_pending, # None for most, or specific index for Rank 6 wild color choice continuation
        action_input=action_input_data
    )

    if not success:
        return jsonify({"error": message, "game_state": game.to_dict(), "next_action_prompt": next_action_prompt.name if next_action_prompt else None}), 400

    response = {
        "message": message,
        "game_state": game.to_dict(),
        "next_action_prompt": next_action_prompt.name if next_action_prompt else None
    }
    return jsonify(response)

@app.route('/api/draw_card', methods=['POST'])
def draw_card():
    if not game:
        return jsonify({"error": "Game not initialized"}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400

    player_name = data.get('player_name')
    if not player_name:
        return jsonify({"error": "Missing player_name"}), 400

    player = get_player_by_name(player_name)
    if not player:
        return jsonify({"error": f"Player {player_name} not found"}), 404

    # Verify it's the player's turn and no critical pending action for them that blocks drawing.
    # game.player_cannot_play_action() itself has checks for turn and some pending actions.
    current_player_obj = game.get_current_player()
    if player != current_player_obj:
        # Allow draw only if no other player is expected to act on a pending action.
        # Or if the pending action is for this player but it's a type where drawing is still an option (e.g. CHOOSE_COLOR before drawing).
        # player_cannot_play_action handles the nuances of pending_action for the current player.
        # If it's not the current player's turn at all, it's an error.
        is_actor_for_pending = False
        if game.pending_action:
            actor_idx = game.action_data.get("original_player_idx", game.action_data.get("player_idx"))
            if actor_idx is not None and game.players[actor_idx] == player:
                is_actor_for_pending = True
            if game.pending_action.type == ActionType.DISCARD_FROM_PLAYER_HAND:
                chooser_idx = game.action_data.get("chooser_idx")
                if chooser_idx is not None and game.players[chooser_idx] == player:
                    is_actor_for_pending = True

        if not is_actor_for_pending and game.pending_action is not None :
             # If there's a pending action and the current player is not the designated actor for it,
             # they shouldn't be able to trigger a draw that advances the turn.
             # However, player_cannot_play_action also checks this.
             # The main check is: if player != current_player_obj AND no pending action that makes 'player' the current actor.
             pass # Let player_cannot_play_action handle the detailed logic

    success, message = game.player_cannot_play_action(player)

    if not success:
        # player_cannot_play_action might return success=False if it's not player's turn OR
        # if a pending action for *this* player prevents drawing (e.g. must complete SWAP_CARD).
        return jsonify({"error": message, "game_state": game.to_dict()}), 400

    response = {
        "message": message,
        "game_state": game.to_dict()
    }
    return jsonify(response)

@app.route('/api/cpu_play_turn', methods=['POST'])
def cpu_play_turn():
    if not game:
        return jsonify({"error": "Game not initialized"}), 500

    data = request.get_json()
    player_name = data.get('player_name')

    if not player_name:
        return jsonify({"error": "Missing player_name for CPU turn"}), 400

    player = get_player_by_name(player_name)
    if not player:
        return jsonify({"error": f"Player {player_name} not found"}), 404

    current_player_obj = game.get_current_player()
    if player != current_player_obj:
        return jsonify({"error": f"It's not {player_name}'s turn (CPU). Current player: {current_player_obj.name}"}), 403

    if मानव_खिलाड़ी_का_नाम is not None and player_name.lower() == मानव_खिलाड़ी_का_नाम.lower() : # A safeguard, though client should prevent this
         return jsonify({"error": "This endpoint is for CPU players."}), 400


    # Simulate CPU playing a turn.
    # This logic is adapted from the __main__ block of uno_game/src/game.py
    # It's a simplified version for API context.
    # A more robust solution would involve moving CPU decision logic into Player or Game class.
    message = f"CPU {player.name} is thinking..."
    action_taken = False

    if game.pending_action:
        # Simplified: If CPU has a pending action, it's complex.
        # For now, assume CPU doesn't get into complex pending states or auto-resolves simple ones.
        # A real CPU AI would need to handle these.
        # Example: If CHOOSE_COLOR is pending for a CPU.
        if game.pending_action.type == ActionType.CHOOSE_COLOR:
            # Check if this CPU is the one to choose color
            expected_actor_idx = game.action_data.get("player_idx", game.action_data.get("original_player_idx"))
            if expected_actor_idx is not None and game.players[expected_actor_idx] == player:
                chosen_color = random.choice([c for c in Color if c != Color.WILD])
                card_idx_for_pending = None
                if game.action_data.get("is_for_rank_6_wild"):
                    card_idx_for_pending = game.action_data.get("rank_6_card_idx_pending_color")

                success_cpu_pending, msg_cpu_pending, next_prompt_cpu_pending = game.play_turn(
                    player,
                    card_index=card_idx_for_pending,
                    action_input={"chosen_color": chosen_color,
                                  "chosen_color_for_rank_6_wild": chosen_color if game.action_data.get("is_for_rank_6_wild") else None}
                )
                message = msg_cpu_pending
                action_taken = success_cpu_pending
            else:
                message = f"CPU {player.name} has a pending action ({game.pending_action.type.name}) but is not the designated actor, or it's too complex to auto-resolve."
        else:
            message = f"CPU {player.name} has a pending action ({game.pending_action.type.name}) that cannot be auto-resolved by this simple API."
            # To prevent getting stuck, we might advance turn if no action taken, but that's risky.
            # For now, it will just return this message. The game state won't change.

    else: # No pending action, normal CPU turn
        top_card_sim = game.get_top_card()
        playable_cards_indices = []
        if top_card_sim:
            playable_cards_indices = [
                i for i, card_obj in enumerate(player.hand)
                if card_obj.matches(top_card_sim, game.current_wild_color)
            ]

        if playable_cards_indices:
            card_idx_sim = random.choice(playable_cards_indices)
            card_being_played = player.hand[card_idx_sim]
            chosen_color_sim_val = None
            if card_being_played.is_wild():
                chosen_color_sim_val = random.choice([c for c in Color if c != Color.WILD])

            success_cpu, msg_cpu, _ = game.play_turn(
                player, card_idx_sim, chosen_color_for_wild=chosen_color_sim_val
            )
            message = msg_cpu
            action_taken = success_cpu
        else:
            # CPU tries to use Yellow 4 if applicable
            played_y4 = False
            if player.has_get_out_of_jail_card():
                y4 = player.get_out_of_jail_yellow_4
                top_card_for_y4_check = game.get_top_card()
                if y4 and top_card_for_y4_check and y4.matches(top_card_for_y4_check, game.current_wild_color):
                    player.use_get_out_of_jail_card()
                    game.deck.add_to_discard(y4)
                    game.current_wild_color = None # Yellow 4 is not wild
                    game._award_color_counters(player, y4) # Award for Yellow
                    message = f"CPU {player.name} used 'Get Out of Jail Free' Yellow 4."
                    if player.is_hand_empty():
                        game.game_over = True
                        game.winner = player
                        message += " And WINS!"
                    else:
                        # Advance turn after playing Y4
                        game.current_player_index = game.players.index(player)
                        game._advance_turn_marker()
                    action_taken = True
                    played_y4 = True
                # else: # Cannot play Y4, put it back (already handled by has_get_out_of_jail_card logic)
                #    player.store_yellow_4_get_out_of_jail(y4) # this is wrong, store is for initial acquisition

            if not played_y4:
                success_cpu_draw, msg_cpu_draw = game.player_cannot_play_action(player)
                message = msg_cpu_draw
                action_taken = success_cpu_draw

    if not action_taken and not game.game_over:
        # If CPU somehow failed to make a move (e.g. complex pending action it couldn't handle)
        # and game isn't over, log this. The turn technically doesn't advance here.
        # A more sophisticated CPU might try something else or this indicates a game state issue.
        message += " (CPU took no conclusive action this turn via API)"


    return jsonify({"message": message, "game_state": game.to_dict()})


# Need to import random for CPU logic
import random

# Placeholder for human player name, can be set by client if necessary
मानव_खिलाड़ी_का_नाम = "Player 1"

# Serve static files (HTML, CSS, JS)
from flask import send_from_directory

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    # This will serve style.css, script.js, etc.
    # Ensure these files are in the same directory as app.py (root)
    # or adjust the first argument of send_from_directory if they are elsewhere (e.g., 'frontend')
    return send_from_directory('.', filename)

if __name__ == '__main__':
    if game:
        print("Starting Flask server with UnoGame initialized. Open http://localhost:5000/ in your browser.")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Flask server cannot start, UnoGame failed to initialize.")
