# Placeholder for the Shop system

from typing import TYPE_CHECKING, Dict, Any, Optional

if TYPE_CHECKING:
    from .player import Player # To avoid circular import if Player needs Shop or vice-versa

class ShopItem:
    def __init__(self, name: str, cost: int, description: str, effect_id: str):
        self.name = name
        self.cost = cost
        self.description = description
        self.effect_id = effect_id # An identifier to apply the effect

    def __str__(self):
        return f"{self.name} (Cost: {self.cost} coins) - {self.description}"

class Shop:
    def __init__(self):
        self.items: Dict[str, ShopItem] = {}
        self._initialize_items()

    def _initialize_items(self):
        # Placeholder items - these would be defined with actual game effects
        self.items["draw_one_less"] = ShopItem(
            name="Lucky Charm",
            cost=5,
            description="Next time you're forced to draw multiple cards (e.g., Draw 2, Draw 4), draw one less.",
            effect_id="draw_one_less"
        )
        self.items["extra_shuffle_token"] = ShopItem(
            name="Shuffle Token",
            cost=3,
            description="Gain an extra shuffle token.",
            effect_id="gain_shuffle_token"
        )
        self.items["peek_opponent_hand"] = ShopItem(
            name="Spyglass",
            cost=7,
            description="Briefly peek at one opponent's hand (e.g., 3 cards randomly).",
            effect_id="peek_hand"
        )
        # More items can be added here

    def display_items(self) -> str:
        if not self.items:
            return "The shop is currently empty."
        display = ["Welcome to the Shop! Available items:"]
        for item_id, item in self.items.items():
            display.append(f"  [{item_id}] {item}")
        return "\n".join(display)

    def purchase_item(self, player: 'Player', item_id: str) -> Tuple[bool, str]:
        """
        Allows a player to purchase an item.
        Returns (success, message).
        Actual application of item effect is handled by game logic based on player's inventory/status.
        """
        item_to_buy = self.items.get(item_id)
        if not item_to_buy:
            return False, "Invalid item ID."

        if player.coins < item_to_buy.cost:
            return False, f"Not enough coins. You have {player.coins}, need {item_to_buy.cost}."

        player.coins -= item_to_buy.cost

        # Placeholder for adding item to player's inventory or applying immediate effect
        # This would depend on how item effects are managed (e.g., player status flags, inventory list)
        message = f"{player.name} purchased {item_to_buy.name} for {item_to_buy.cost} coins."

        if item_to_buy.effect_id == "gain_shuffle_token":
            player.shuffle_counters += 1
            message += f" Gained 1 shuffle token (Total: {player.shuffle_counters})."
        else:
            # For other items, the game would need to track that the player owns this item/effect.
            # e.g., player.active_shop_effects.append(item_to_buy.effect_id)
            # Or player.inventory.append(item_to_buy)
            message += f" (Effect '{item_to_buy.effect_id}' needs to be applied by game logic)."
            print(f"Debug: Player {player.name} now has effect '{item_to_buy.effect_id}' pending.")


        return True, message

if __name__ == '__main__':
    # Basic test
    shop = Shop()
    print(shop.display_items())

    # Dummy player for testing
    class DummyPlayer:
        def __init__(self, name, coins=10):
            self.name = name
            self.coins = coins
            self.shuffle_counters = 0
            # In a real game, player would have an inventory or status effects list
            # self.inventory = []
            # self.active_effects = []

    player_alice = DummyPlayer("Alice", 10)

    success, msg = shop.purchase_item(player_alice, "extra_shuffle_token")
    print(msg) # Alice purchased Shuffle Token... Gained 1 shuffle token...
    print(f"Alice's coins: {player_alice.coins}, Shuffles: {player_alice.shuffle_counters}")

    success, msg = shop.purchase_item(player_alice, "draw_one_less")
    print(msg) # Alice purchased Lucky Charm... (Effect needs to be applied...)
    print(f"Alice's coins: {player_alice.coins}")

    success, msg = shop.purchase_item(player_alice, "non_existent_item")
    print(msg) # Invalid item ID

    player_bob = DummyPlayer("Bob", 2)
    success, msg = shop.purchase_item(player_bob, "extra_shuffle_token")
    print(msg) # Not enough coins...
    print(f"Bob's coins: {player_bob.coins}")
