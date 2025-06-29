from flask import Flask, jsonify
from uno_game.src.game import UnoGame
from uno_game.src.player import Player

app = Flask(__name__)

# Initialize a global game instance for simplicity
# In a real application, you'd manage game instances differently (e.g., sessions, database)
try:
    game = UnoGame(player_names=["Player 1", "CPU 1", "CPU 2"])
except ValueError as e:
    print(f"Error initializing game: {e}")
    # Fallback or exit, depending on desired behavior
    game = None

@app.route('/api/game_state', methods=['GET'])
def get_game_state():
    if game:
        return jsonify(game.to_dict())
    else:
        return jsonify({"error": "Game not initialized"}), 500

if __name__ == '__main__':
    if game:
        print("Starting Flask server with UnoGame initialized.")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Flask server cannot start, UnoGame failed to initialize.")
