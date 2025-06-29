from flask import Flask, jsonify, request
from uno_game.src.game import UnoGame
from uno_game.src.player import Player
from uno_game.src.card import Color
from uno_game.src.actions import ActionType

app = Flask(__name__)

# Initialize a global game instance for simplicity
# In a real application, you'd manage game instances differently (e.g., sessions, database)

# मानव_खिलाड़ी_का_नाम will be determined by the player with type "HUMAN" in player_configurations
# Defaulting to "Player 1" if none are explicitly set as HUMAN during configuration.

try:
    # Using a default set of players for now. This could be configurable.
    player_configurations = [
        ("Player 1", "HUMAN"), # Explicitly set the first player as HUMAN
        ("CPU 1", "CPU"),
        ("CPU 2", "CPU"),
        ("CPU 3", "CPU"),
    ]
    # Filter out None or empty names, adjust as needed for your setup
    active_players = [p for p in player_configurations if p[0]]

    # Ensure there's at least one human and some CPUs, or however you want to define min players
    if not any(p[1] == "HUMAN" for p in active_players):
        # Fallback or error if no human player is configured
        print("Warning: No human player configured. Defaulting to first player as human.")
        if not active_players: # e.g. if all names were empty
             active_players = [("Player 1", "HUMAN"), ("CPU 1", "CPU")] # Default if empty
        elif active_players[0][1] != "HUMAN": # If first player is not human, make them
            active_players[0] = (active_players[0][0], "HUMAN")

    game = UnoGame(player_info=active_players)
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

    if player.player_type != "CPU": # Ensure it's a CPU player
         return jsonify({"error": "This endpoint is for CPU players only."}), 400

    if game.game_over:
        return jsonify({"error": "Game is already over."}), 400

    # Get CPU's action from the game logic
    cpu_card_index, cpu_chosen_color, cpu_action_input = game.get_cpu_action(player)

    success: bool = False
    message: str = ""
    next_action_prompt: Optional[ActionType] = None

    if cpu_card_index is not None: # CPU wants to play a card (or take action involving a card from hand for pending)
        success, message, next_action_prompt = game.play_turn(
            player,
            card_index=cpu_card_index,
            action_input=cpu_action_input, # This will have specific inputs for pending actions like SWAP, DISCARD etc.
            chosen_color_for_wild=cpu_chosen_color # For regular wild plays or wild part of Rank 6
        )
    elif cpu_action_input is not None: # CPU has input for a pending action that doesn't involve playing a card from hand now (e.g. CHOOSE_COLOR)
        success, message, next_action_prompt = game.play_turn(
            player,
            card_index=None, # No card is being played from hand in this step of the pending action
            action_input=cpu_action_input,
            chosen_color_for_wild=cpu_chosen_color # This might be set if action_input includes a color choice
        )
    else: # CPU chooses to draw (or no other action determined by get_cpu_action)
        # This can also be the case if get_cpu_action returns (None, None, None) for a complex pending action it can't handle.
        # player_cannot_play_action will then try to draw a card for the CPU.
        # If even drawing is not possible (e.g. pending action blocks it), it will return success=False.
        success, message = game.player_cannot_play_action(player)

    if not success and not game.game_over : # game.game_over might be true if CPU drew last card and won
        # If the action failed and game not over, return error
        # message already contains the reason from play_turn or player_cannot_play_action
        return jsonify({"error": message, "game_state": game.to_dict(), "next_action_prompt": next_action_prompt.name if next_action_prompt else None}), 400

    return jsonify({
        "message": message,
        "game_state": game.to_dict(),
        "next_action_prompt": next_action_prompt.name if next_action_prompt else None
    })


# Need to import random for CPU logic
import random

# मानव_खिलाड़ी_का_नाम is no longer needed here, it's part of player_info

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
