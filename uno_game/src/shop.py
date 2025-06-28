# Placeholder for the Shop system

from typing import TYPE_CHECKING, Dict, Tuple  # Added Tuple
from enum import Enum

if TYPE_CHECKING:
    from .player import (
        Player,
    )  # To avoid circular import if Player needs Shop or vice-versa


class ShopEffectId(Enum):
    """Unique identifiers for shop item effects."""

    DRAW_ONE_LESS = "draw_one_less"
    GAIN_SHUFFLE_TOKEN = "gain_shuffle_token"
    PEEK_HAND = "peek_hand"


class ShopItem:
    def __init__(self, name: str, cost: int, description: str, effect_id: ShopEffectId):
        self.name = name
        self.cost = cost
        self.description = description
        self.effect_id: ShopEffectId = effect_id  # An identifier to apply the effect

    def __str__(self):
        return f"{self.name} (Cost: {self.cost} coins) - {self.description}"


class Shop:
    def __init__(self):
        self.items: Dict[ShopEffectId, ShopItem] = {}  # Keyed by Enum now
        self._initialize_items()

    def _initialize_items(self):
        # Placeholder items - these would be defined with actual game effects
        self.items[ShopEffectId.DRAW_ONE_LESS] = ShopItem(
            name="Lucky Charm",
            cost=5,
            description="Next time you're forced to draw multiple cards (e.g., Draw 2, Draw 4), draw one less.",
            effect_id=ShopEffectId.DRAW_ONE_LESS,
        )
        self.items[ShopEffectId.GAIN_SHUFFLE_TOKEN] = ShopItem(
            name="Shuffle Token",
            cost=3,
            description="Gain an extra shuffle token.",
            effect_id=ShopEffectId.GAIN_SHUFFLE_TOKEN,
        )
        self.items[ShopEffectId.PEEK_HAND] = ShopItem(
            name="Spyglass",
            cost=7,
            description="Briefly peek at one opponent's hand (e.g., 3 cards randomly).",
            effect_id=ShopEffectId.PEEK_HAND,
        )
        # More items can be added here

    def display_items(self) -> str:
        if not self.items:
            return "The shop is currently empty."
        display = ["Welcome to the Shop! Available items:"]
        for item_effect_id, item in self.items.items():  # item_id is now an Enum member
            display.append(f"  [{item_effect_id.name}] {item}")  # Display Enum name
        return "\n".join(display)

    def purchase_item(
        self, player: "Player", item_id_enum: ShopEffectId
    ) -> Tuple[bool, str]:
        """
        Allows a player to purchase an item.
        Returns (success, message).
        Actual application of item effect is handled by game logic based on player's inventory/status.
        """
        item_to_buy = self.items.get(item_id_enum)
        if not item_to_buy:
            # This should ideally not happen if item_id_enum is enforced as ShopEffectId by type checker
            return False, f"Invalid item ID: {item_id_enum}."

        if player.coins < item_to_buy.cost:
            return (
                False,
                f"Not enough coins. You have {player.coins}, need {item_to_buy.cost}.",
            )

        player.coins -= item_to_buy.cost

        # Placeholder for adding item to player's inventory or applying immediate effect
        # This would depend on how item effects are managed (e.g., player status flags, inventory list)
        message = (
            f"{player.name} purchased {item_to_buy.name} for {item_to_buy.cost} coins."
        )

        if item_to_buy.effect_id == ShopEffectId.GAIN_SHUFFLE_TOKEN:
            player.shuffle_counters += 1
            message += f" Gained 1 shuffle token (Total: {player.shuffle_counters})."
        else:
            # For other items, the game would need to track that the player owns this item/effect.
            # e.g., player.active_shop_effects.append(item_to_buy.effect_id.value)
            # Or player.inventory.append(item_to_buy)
            message += f" (Effect '{item_to_buy.effect_id.name}' needs to be applied by game logic)."
            print(
                f"Debug: Player {player.name} now has effect '{item_to_buy.effect_id.name}' pending."
            )

        return True, message


if __name__ == "__main__":
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

    success, msg = shop.purchase_item(player_alice, ShopEffectId.GAIN_SHUFFLE_TOKEN)
    print(msg)
    print(
        f"Alice's coins: {player_alice.coins}, Shuffles: {player_alice.shuffle_counters}"
    )

    success, msg = shop.purchase_item(player_alice, ShopEffectId.DRAW_ONE_LESS)
    print(msg)
    print(f"Alice's coins: {player_alice.coins}")

    # Test purchasing a non-existent item (type error if trying to pass a string directly)
    # success, msg = shop.purchase_item(player_alice, "non_existent_item") # This would be a type error
    # To test the "Invalid item ID" path, one might try to pass an enum value not in shop.items
    # For now, we assume valid Enum members are passed.

    player_bob = DummyPlayer("Bob", 2)
    success, msg = shop.purchase_item(player_bob, ShopEffectId.GAIN_SHUFFLE_TOKEN)
    print(msg)
    print(f"Bob's coins: {player_bob.coins}")
