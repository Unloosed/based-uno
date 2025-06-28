"""
Defines the Shop system for the Uno game.

Players can use coins (earned from Yellow cards) to purchase items from the shop
that provide various in-game advantages or effects. This module includes
classes for shop items and the shop itself.
"""

from typing import (
    TYPE_CHECKING,
    Dict,
    Tuple,
)
from enum import Enum  # Added Enum

if TYPE_CHECKING:
    from .player import Player  # For type hinting to avoid circular imports


class ShopEffectId(Enum):
    """Unique identifiers for shop item effects."""

    DRAW_ONE_LESS = "draw_one_less"
    GAIN_SHUFFLE_TOKEN = "gain_shuffle_token"
    PEEK_HAND = "peek_hand"
    # Example: TEMPORARY_COLOR_SHIELD = "color_shield_wd4"


class ShopItem:
    """
    Represents an item available for purchase in the shop.

    Attributes:
        name (str): The display name of the item.
        cost (int): The number of coins required to purchase the item.
        description (str): A brief description of the item's effect.
        effect_id (ShopEffectId): A unique identifier used by the game logic to apply
                                  the item's effect.
    """

    def __init__(self, name: str, cost: int, description: str, effect_id: ShopEffectId):
        """
        Initializes a ShopItem.

        Args:
            name: The name of the item.
            cost: The cost in coins.
            description: A description of its effect.
            effect_id: A ShopEffectId for the effect.
        """
        self.name: str = name
        self.cost: int = cost
        self.description: str = description
        self.effect_id: ShopEffectId = effect_id

    def __str__(self) -> str:
        """Returns a string representation of the shop item."""
        return f"{self.name} (Cost: {self.cost} coins) - {self.description}"


class Shop:
    """
    Manages the collection of items available in the game's shop.

    The Shop allows players to view available items and purchase them using coins.
    The application of item effects is typically handled by the main game logic,
    triggered by the `effect_id` of the purchased item.

    Attributes:
        items (Dict[str, ShopItem]): A dictionary mapping item IDs to ShopItem objects.
    """

    def __init__(self):
        """Initializes the Shop and populates it with default items."""
        self.items: Dict[str, ShopItem] = {}
        self._initialize_items()

    def _initialize_items(self) -> None:
        """
        Populates the shop with a predefined list of items.
        This method is called during the shop's initialization.
        """
        # Placeholder items - these would be defined with actual game effects
        # and potentially loaded from a configuration file in a more complex system.
        self.items[ShopEffectId.DRAW_ONE_LESS.value] = ShopItem(
            name="Lucky Charm",
            cost=5,
            description="Next time you're forced to draw multiple cards (e.g., Draw 2, Wild Draw 4), draw one less.",
            effect_id=ShopEffectId.DRAW_ONE_LESS,
        )
        self.items[ShopEffectId.GAIN_SHUFFLE_TOKEN.value] = ShopItem(
            name="Shuffle Token",
            cost=3,
            description="Gain an extra shuffle token.",
            effect_id=ShopEffectId.GAIN_SHUFFLE_TOKEN,
        )
        self.items[ShopEffectId.PEEK_HAND.value] = ShopItem(
            name="Spyglass",
            cost=7,
            description="Briefly peek at a few cards from one opponent's hand (e.g., 3 random cards).",
            effect_id=ShopEffectId.PEEK_HAND,
        )
        # Example: Add more items here
        # self.items[ShopEffectId.TEMPORARY_COLOR_SHIELD.value] = ShopItem(
        # name="Color Shield",
        # cost=4,
        # description="For your next turn, you cannot be challenged on playing a Wild Draw Four.",
        # effect_id=ShopEffectId.TEMPORARY_COLOR_SHIELD,
        # )

    def display_items(self) -> str:
        """
        Returns a string listing all items available in the shop.

        Returns:
            A formatted string of shop items, or a message if the shop is empty.
        """
        if not self.items:
            return "The shop is currently empty."
        display = ["Welcome to the Shop! Available items:"]
        for (
            item_id,
            item_data,
        ) in self.items.items():  # Corrected variable name from item to item_data
            display.append(f"  [{item_id}] {str(item_data)}")  # Use str(item_data)
        return "\n".join(display)

    def purchase_item(self, player: "Player", item_id: str) -> Tuple[bool, str]:
        """
        Allows a player to attempt to purchase an item from the shop.

        If the purchase is successful, the player's coins are deducted, and an
        effect might be applied directly (like gaining a shuffle token) or flagged
        for the game logic to handle.

        Args:
            player: The Player object attempting the purchase.
            item_id: The unique identifier of the item to purchase.

        Returns:
            A tuple (success, message):
            - success (bool): True if the purchase was successful, False otherwise.
            - message (str): A message describing the outcome of the purchase attempt.
        """
        item_to_buy = self.items.get(item_id)
        if not item_to_buy:
            return False, f"Invalid item ID: '{item_id}'. No such item in shop."

        if player.coins < item_to_buy.cost:
            return (
                False,
                f"Not enough coins to buy {item_to_buy.name}. You have {player.coins}, but it costs {item_to_buy.cost}.",
            )

        player.coins -= item_to_buy.cost
        message = (
            f"{player.name} purchased {item_to_buy.name} for {item_to_buy.cost} coins."
        )

        # Apply direct effects or log pending effects
        if item_to_buy.effect_id == ShopEffectId.GAIN_SHUFFLE_TOKEN:
            player.shuffle_counters += 1
            message += f" Gained 1 shuffle token (Total: {player.shuffle_counters})."
        # Add more direct effect handling here if needed for other items
        # else if item_to_buy.effect_id == ShopEffectId.SOME_OTHER_DIRECT_EFFECT:
        #    ... apply it ...
        else:
            # For items with effects that are not immediate or are conditional,
            # the game logic needs to track that the player owns this item/effect.
            # This might involve adding to a player's list of active effects or inventory.
            # Example: player.active_effects.append(item_to_buy.effect_id.value)
            message += f" (The effect '{item_to_buy.effect_id.name}' will be active or applied by game rules)."
            # For debugging or simple systems, a print statement can indicate this:
            print(
                f"Info: Player {player.name} now has effect '{item_to_buy.effect_id.name}' from purchased item '{item_to_buy.name}'."
            )

        return True, message


if __name__ == "__main__":
    # Docstrings added, no functional change to __main__
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

    success, msg = shop.purchase_item(
        player_alice, ShopEffectId.GAIN_SHUFFLE_TOKEN.value
    )
    print(msg)  # Alice purchased Shuffle Token... Gained 1 shuffle token...
    print(
        f"Alice's coins: {player_alice.coins}, Shuffles: {player_alice.shuffle_counters}"
    )

    success, msg = shop.purchase_item(player_alice, ShopEffectId.DRAW_ONE_LESS.value)
    print(msg)  # Alice purchased Lucky Charm... (Effect needs to be applied...)
    print(f"Alice's coins: {player_alice.coins}")

    success, msg = shop.purchase_item(
        player_alice, "non_existent_item"
    )  # Test with a raw string for invalid
    print(msg)  # Invalid item ID

    player_bob = DummyPlayer("Bob", 2)
    success, msg = shop.purchase_item(player_bob, ShopEffectId.GAIN_SHUFFLE_TOKEN.value)
    print(msg)  # Not enough coins...
    print(f"Bob's coins: {player_bob.coins}")
