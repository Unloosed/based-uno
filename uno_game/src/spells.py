"""
Defines the Spell systems (Lunar and Solar) for the Uno game.

Players can use mana (earned from Blue and Red cards) to cast spells that
provide various tactical advantages or affect other players. This module
includes base classes for spells and specific managers for Lunar and Solar spells.
"""

from typing import TYPE_CHECKING, Tuple, Dict, Optional  # Any was unused

if TYPE_CHECKING:
    from .player import Player
    from .game import (
        UnoGame,
    )  # For spells that might affect game state or other players
from enum import Enum


class LunarSpellId(Enum):
    """Unique identifiers for Lunar spells."""
    MOONBEAM_DRAW = "moonbeam_draw"
    LUNAR_SHIELD = "lunar_shield"
    SHADOW_SWAP_PEEK = "shadow_swap_peek"
    # TIDAL_DISRUPTION = "tidal_disruption"


class SolarSpellId(Enum):
    """Unique identifiers for Solar spells."""
    SUN_FLARE_DISCARD = "sun_flare_discard"
    SOLAR_BOOST = "solar_boost"
    # BURNING_RESOLVE = "burning_resolve"


class Spell:
    """
    Represents a generic spell that can be cast by a player.

    Attributes:
        name (str): The display name of the spell.
        mana_cost (int): The amount of mana (Lunar or Solar) required to cast the spell.
        description (str): A brief description of what the spell does.
        spell_id (str): A unique identifier for the spell, used by game logic.
        targetable (bool): True if the spell requires a target player, False otherwise.
    """

    def __init__(
        self,
        name: str,
        mana_cost: int,
        description: str,
        spell_id: str,
        targetable: bool = False,
    ):
        """
        Initializes a Spell.

        Args:
            name: The name of the spell.
            mana_cost: The mana cost.
            description: A description of its effect.
            spell_id: A unique string identifier for the spell.
            targetable: Whether the spell requires a target. Defaults to False.
        """
        self.name: str = name
        self.mana_cost: int = mana_cost
        self.description: str = description
        self.spell_id: str = spell_id
        self.targetable: bool = targetable

    def __str__(self) -> str:
        """Returns a string representation of the spell."""
        target_info = " (Targetable)" if self.targetable else ""
        return f"{self.name}{target_info} (Cost: {self.mana_cost} mana) - {self.description}"


class LunarSpells:
    """
    Manages the collection of Lunar spells available in the game.

    Lunar spells are typically associated with Blue cards and Lunar Mana.
    This class provides methods to initialize, display, and attempt to cast Lunar spells.

    Attributes:
        spells (Dict[LunarSpellId, Spell]): A dictionary mapping Lunar spell IDs to Spell objects.
    """

    def __init__(self):
        """Initializes the LunarSpells manager and populates it with default spells."""
        self.spells: Dict[LunarSpellId, Spell] = {}
        self._initialize_spells()

    def _initialize_spells(self) -> None:
        """
        Populates with a predefined list of Lunar spells.
        Called during initialization.
        """
        self.spells[LunarSpellId.MOONBEAM_DRAW] = Spell(
            name="Moonbeam Draw",
            mana_cost=3,
            description="Force a target player to draw 1 card.",
            spell_id=LunarSpellId.MOONBEAM_DRAW.value, # Keep spell_id in Spell as str for now
            targetable=True,
        )
        self.spells[LunarSpellId.LUNAR_SHIELD] = Spell(
            name="Lunar Shield",
            mana_cost=5,
            description="Protect yourself from the next 'draw' effect (e.g., Draw 2, Wild Draw 4) played against you.",
            spell_id=LunarSpellId.LUNAR_SHIELD.value,
            targetable=False,  # Typically self-cast implicitly
        )
        self.spells[LunarSpellId.SHADOW_SWAP_PEEK] = Spell(
            name="Shadow Swap Peek",
            mana_cost=4,
            description="Peek at one card from a target player's hand, then you may choose to swap it with one of yours.",
            spell_id=LunarSpellId.SHADOW_SWAP_PEEK.value,
            targetable=True,
        )
        # Example: Add more Lunar spells here
        # self.spells[LunarSpellId.TIDAL_DISRUPTION] = Spell(
        #     name="Tidal Disruption",
        #     mana_cost=6,
        #     description="Reverse the play order and skip the next two players.",
        #     spell_id=LunarSpellId.TIDAL_DISRUPTION.value,
        # )

    def display_spells(self) -> str:
        """
        Returns a string listing all available Lunar spells.

        Returns:
            A formatted string of Lunar spells, or a message if none are known.
        """
        if not self.spells:
            return "No Lunar spells are currently known."
        display = ["Available Lunar Spells:"]
        for spell_id, spell_data in self.spells.items():  # Corrected variable name
            display.append(f"  [{spell_id}] {str(spell_data)}")  # Use str()
        return "\n".join(display)

    def cast_spell(
        self,
        caster: "Player",
        spell_id_enum: LunarSpellId, # Changed to LunarSpellId
        game_context: "UnoGame",  # Context for affecting game state
        target_player: Optional["Player"] = None,
    ) -> Tuple[bool, str]:
        """
        Attempts to cast a Lunar spell by the `caster`.

        Checks for mana cost and target validity. If successful, deducts mana.
        The actual application of the spell's effect is intended to be handled
        by the main game logic based on the `spell_id` and context.

        Args:
            caster: The Player attempting to cast the spell.
            spell_id_enum: The LunarSpellId of the spell to cast.
            game_context: The current UnoGame instance, providing context for effects.
            target_player: The targeted Player, if the spell is targetable.

        Returns:
            A tuple (success, message):
            - success (bool): True if the spell casting prerequisites are met, False otherwise.
            - message (str): A message describing the outcome of the casting attempt.
        """
        spell_to_cast = self.spells.get(spell_id_enum)
        if not spell_to_cast:
            # This case should ideally not happen if spell_id_enum is enforced as LunarSpellId
            return False, f"Unknown Lunar spell ID: '{spell_id_enum.value}'."

        if caster.lunar_mana < spell_to_cast.mana_cost:
            return (
                False,
                f"Not enough Lunar Mana for {spell_to_cast.name}. You have {caster.lunar_mana}, need {spell_to_cast.mana_cost}.",
            )

        if spell_to_cast.targetable and target_player is None:
            return (
                False,
                f"Spell '{spell_to_cast.name}' requires a target player, but none was provided.",
            )

        if (
            spell_to_cast.targetable
            and target_player == caster
            and spell_id_enum not in [] # Example: [LunarSpellId.SELF_TARGET_SPELL]
        ):
            # Depending on the spell, self-targeting might be invalid.
            # For now, assume most targetable spells are for others.
            # Add specific spell_id_enum checks if some allow self-targeting.
            # return False, f"Spell '{spell_to_cast.name}' cannot target self."
            pass  # Allow self-targeting for now unless explicitly forbidden by a spell's design

        caster.lunar_mana -= spell_to_cast.mana_cost
        message = f"{caster.name} casts {spell_to_cast.name} (cost {spell_to_cast.mana_cost} Lunar Mana)."

        # Placeholder for spell effects:
        # In a full implementation, this might queue an action for the game loop,
        # or directly modify `game_context` or `target_player` states.
        if spell_id_enum == LunarSpellId.MOONBEAM_DRAW and target_player:
            message += f" Targeting {target_player.name}."
            # Example: game_context.apply_effect(caster, target_player, "force_draw", 1)
            message += f" (Game logic should make {target_player.name} draw 1 card)."
            print(
                f"Info: {target_player.name} targeted by Moonbeam Draw from {caster.name}."
            )

        elif spell_id_enum == LunarSpellId.LUNAR_SHIELD:
            # Example: caster.status_effects.add("lunar_shield")
            message += f" {caster.name} is now shielded from the next draw effect (game logic to apply)."
            print(f"Info: {caster.name} gained Lunar Shield effect.")

        elif spell_id_enum == LunarSpellId.SHADOW_SWAP_PEEK and target_player:
            message += f" Targeting {target_player.name} for Shadow Swap Peek."
            # Example: game_context.initiate_peek_and_swap(caster, target_player)
            message += f" (Game logic to handle peek and optional swap with {target_player.name})."
            print(
                f"Info: {caster.name} initiated Shadow Swap Peek on {target_player.name}."
            )

        else:  # Default message for other spells
            message += f" (The effect '{spell_to_cast.spell_id}' should now be processed by game rules)." # spell_to_cast.spell_id is str
            print(
                f"Info: Lunar spell '{spell_to_cast.spell_id}' cast by {caster.name}."
            )

        return True, message


class SolarSpells:
    """
    Manages the collection of Solar spells available in the game.

    Solar spells are typically associated with Red cards and Solar Mana.
    This class provides methods to initialize, display, and attempt to cast Solar spells.

    Attributes:
        spells (Dict[SolarSpellId, Spell]): A dictionary mapping Solar spell IDs to Spell objects.
    """

    def __init__(self):
        """Initializes the SolarSpells manager and populates it with default spells."""
        self.spells: Dict[SolarSpellId, Spell] = {}
        self._initialize_spells()

    def _initialize_spells(self) -> None:
        """
        Populates with a predefined list of Solar spells.
        Called during initialization.
        """
        self.spells[SolarSpellId.SUN_FLARE_DISCARD] = Spell(
            name="Sun Flare Discard",
            mana_cost=3,
            description="Force a target player to discard a random card from their hand.",
            spell_id=SolarSpellId.SUN_FLARE_DISCARD.value, # Keep spell_id in Spell as str
            targetable=True,
        )
        self.spells[SolarSpellId.SOLAR_BOOST] = Spell(
            name="Solar Boost",
            mana_cost=4,
            description="Your next played number card counts as +2 towards its numerical value for specific objectives or effects (if applicable).",
            spell_id=SolarSpellId.SOLAR_BOOST.value,
            targetable=False,  # Implicitly self-cast
        )
        # Example: Add more Solar spells here
        # self.spells[SolarSpellId.BURNING_RESOLVE] = Spell(
        #     name="Burning Resolve",
        #     mana_cost=5,
        #     description="Ignore the color requirement for the next card you play this turn.",
        #     spell_id=SolarSpellId.BURNING_RESOLVE.value,
        # )

    def display_spells(self) -> str:
        """
        Returns a string listing all available Solar spells.

        Returns:
            A formatted string of Solar spells, or a message if none are known.
        """
        if not self.spells:
            return "No Solar spells are currently known."
        display = ["Available Solar Spells:"]
        for spell_id, spell_data in self.spells.items():  # Corrected variable name
            display.append(f"  [{spell_id}] {str(spell_data)}")  # Use str()
        return "\n".join(display)

    def cast_spell(
        self,
        caster: "Player",
        spell_id_enum: SolarSpellId, # Changed to SolarSpellId
        game_context: "UnoGame",  # Context for affecting game state
        target_player: Optional["Player"] = None,
    ) -> Tuple[bool, str]:
        """
        Attempts to cast a Solar spell by the `caster`.

        Checks for mana cost and target validity. If successful, deducts mana.
        The actual application of the spell's effect is intended to be handled
        by the main game logic based on the `spell_id` and context.

        Args:
            caster: The Player attempting to cast the spell.
            spell_id_enum: The SolarSpellId of the spell to cast.
            game_context: The current UnoGame instance, providing context for effects.
            target_player: The targeted Player, if the spell is targetable.

        Returns:
            A tuple (success, message):
            - success (bool): True if the spell casting prerequisites are met, False otherwise.
            - message (str): A message describing the outcome of the casting attempt.
        """
        spell_to_cast = self.spells.get(spell_id_enum)
        if not spell_to_cast:
            return False, f"Unknown Solar spell ID: '{spell_id_enum.value}'."

        if caster.solar_mana < spell_to_cast.mana_cost:
            return (
                False,
                f"Not enough Solar Mana for {spell_to_cast.name}. You have {caster.solar_mana}, need {spell_to_cast.mana_cost}.",
            )

        if spell_to_cast.targetable and target_player is None:
            return (
                False,
                f"Spell '{spell_to_cast.name}' requires a target player, but none was provided.",
            )

        # Similar self-target check as in LunarSpells, if needed
        # if spell_to_cast.targetable and target_player == caster and spell_id_enum not in []:
        #     pass

        caster.solar_mana -= spell_to_cast.mana_cost
        message = f"{caster.name} casts {spell_to_cast.name} (cost {spell_to_cast.mana_cost} Solar Mana)."

        # Placeholder for spell effects:
        if spell_id_enum == SolarSpellId.SUN_FLARE_DISCARD and target_player:
            message += f" Targeting {target_player.name}."
            # Example: game_context.apply_effect(caster, target_player, "force_discard_random", 1)
            message += (
                f" (Game logic should make {target_player.name} discard 1 random card)."
            )
            print(
                f"Info: {target_player.name} targeted by Sun Flare Discard from {caster.name}."
            )
        elif spell_id_enum == SolarSpellId.SOLAR_BOOST:
            # Example: caster.status_effects.add("solar_boost_active")
            message += f" {caster.name}'s next number card will be boosted (game logic to apply)."
            print(f"Info: {caster.name} gained Solar Boost effect.")
        else:  # Default message for other spells
            message += f" (The effect '{spell_to_cast.spell_id}' should now be processed by game rules)." # spell_to_cast.spell_id is str
            print(
                f"Info: Solar spell '{spell_to_cast.spell_id}' cast by {caster.name}."
            )

        return True, message


if __name__ == "__main__":
    # Docstrings added, no functional change to __main__
    lunar_magic = LunarSpells()
    solar_magic = SolarSpells()

    print(lunar_magic.display_spells())
    print("\n" + solar_magic.display_spells())

    # Dummy player and game for testing
    class DummyPlayer:
        def __init__(self, name, lunar=5, solar=5):
            self.name = name
            self.lunar_mana = lunar
            self.solar_mana = solar

    class DummyGame:  # Placeholder for UnoGame context
        pass

    player_merlin = DummyPlayer("Merlin", lunar=10, solar=10)
    player_morgana = DummyPlayer("Morgana")
    dummy_game = DummyGame()

    print("\n--- Merlin's Casts ---")
    success, msg = lunar_magic.cast_spell(
        player_merlin, LunarSpellId.MOONBEAM_DRAW, dummy_game, target_player=player_morgana
    )
    print(msg)
    print(f"Merlin's Lunar Mana: {player_merlin.lunar_mana}")

    success, msg = solar_magic.cast_spell(
        player_merlin, SolarSpellId.SUN_FLARE_DISCARD, dummy_game, target_player=player_morgana
    )
    print(msg)
    print(f"Merlin's Solar Mana: {player_merlin.solar_mana}")

    # To test an invalid ID, we'd need to pass a raw string or a different enum,
    # but the method now expects LunarSpellId/SolarSpellId.
    # This kind of error would ideally be caught by static type checking if `spell_id_enum` was strictly typed.
    # For runtime check with current .get(spell_id_enum), this test is harder to make fail cleanly.
    # Let's assume the type hint itself guides correct usage.
    # If we wanted to test the "Unknown" path, we might need to cast a string:
    # success, msg = lunar_magic.cast_spell(player_merlin, "bad_spell_id", dummy_game) # This would now be a type error
    # print(msg)

    player_arthur = DummyPlayer("Arthur", lunar=1, solar=1)
    success, msg = lunar_magic.cast_spell(player_arthur, LunarSpellId.LUNAR_SHIELD, dummy_game)
    print(msg)  # Not enough mana
