# Placeholder for Lunar and Solar Spells

from typing import TYPE_CHECKING, Tuple, Dict, Optional  # Added Optional
from enum import Enum  # Added Enum

if TYPE_CHECKING:
    from .player import Player
    from .game import (
        UnoGame,
    )  # For spells that might affect game state or other players


class LunarSpellId(Enum):
    """Unique identifiers for Lunar spells."""

    MOONBEAM_DRAW = "moonbeam_draw"
    LUNAR_SHIELD = "lunar_shield"
    SHADOW_SWAP_PEEK = "shadow_swap_peek"


class SolarSpellId(Enum):
    """Unique identifiers for Solar spells."""

    SUN_FLARE_DISCARD = "sun_flare_discard"
    SOLAR_BOOST = "solar_boost"


class Spell:
    def __init__(
        self,
        name: str,
        mana_cost: int,
        description: str,
        spell_id: str,
        targetable: bool = False,
    ):
        self.name = name
        self.mana_cost = mana_cost
        self.description = description
        self.spell_id = spell_id
        self.targetable = targetable  # Does the spell require a target player?

    def __str__(self):
        return f"{self.name} (Cost: {self.mana_cost} mana) - {self.description}"


class LunarSpells:
    def __init__(self):
        self.spells: Dict[LunarSpellId, Spell] = {}  # Use Enum as key
        self._initialize_spells()

    def _initialize_spells(self) -> None:
        # Placeholder Lunar Spells
        self.spells[LunarSpellId.MOONBEAM_DRAW] = Spell(
            name="Moonbeam Draw",
            mana_cost=3,
            description="Force a target player to draw 1 card.",
            spell_id=LunarSpellId.MOONBEAM_DRAW.value,  # Store string value in Spell obj
            targetable=True,
        )
        self.spells[LunarSpellId.LUNAR_SHIELD] = Spell(
            name="Lunar Shield",
            mana_cost=5,
            description="Protect yourself from the next 'draw' effect (e.g., Draw 2, Draw 4) played against you.",
            spell_id=LunarSpellId.LUNAR_SHIELD.value,
        )
        self.spells[LunarSpellId.SHADOW_SWAP_PEEK] = Spell(
            name="Shadow Swap Peek",
            mana_cost=4,
            description="Peek at one card from a target player's hand, then you may swap it with one of yours.",
            spell_id=LunarSpellId.SHADOW_SWAP_PEEK.value,
            targetable=True,
        )
        # More spells

    def display_spells(self) -> str:
        if not self.spells:
            return "No Lunar spells known."
        display = ["Available Lunar Spells:"]
        for spell_id_enum, spell in self.spells.items():  # Iterate with Enum
            display.append(f"  [{spell_id_enum.name}] {spell}")  # Display Enum name
        return "\n".join(display)

    def cast_spell(
        self,
        caster: "Player",
        spell_id_enum: LunarSpellId,  # Expect Enum member
        game_context: "UnoGame",
        target_player: Optional["Player"] = None,
    ) -> Tuple[bool, str]:
        """
        Casts a lunar spell.
        Returns (success, message).
        Actual application of spell effect is handled by game logic.
        """
        spell_to_cast = self.spells.get(spell_id_enum)
        if not spell_to_cast:
            return (
                False,
                f"Unknown Lunar spell: {spell_id_enum}.",
            )  # Should not happen if called with Enum

        if caster.lunar_mana < spell_to_cast.mana_cost:
            return (
                False,
                f"Not enough Lunar Mana. You have {caster.lunar_mana}, need {spell_to_cast.mana_cost}.",
            )

        if spell_to_cast.targetable and target_player is None:
            return False, f"Spell '{spell_to_cast.name}' requires a target player."

        if spell_to_cast.targetable and target_player == caster:
            # Some targetable spells might allow self-targeting, others not. Add specific checks if needed.
            pass

        caster.lunar_mana -= spell_to_cast.mana_cost

        message = f"{caster.name} casts {spell_to_cast.name} (cost {spell_to_cast.mana_cost} Lunar Mana)."

        # Placeholder for spell effects - these would modify game_context or players
        if spell_id_enum == LunarSpellId.MOONBEAM_DRAW and target_player:
            message += f" Targeting {target_player.name}."
            # game_context.player_draws_card(target_player, 1) # Example of direct effect
            # In reality, this might return an action for the game loop to process.
            message += f" ({target_player.name} should draw 1 card - effect needs full game logic integration)."
            print(f"Debug: {target_player.name} targeted by Moonbeam Draw.")

        elif spell_id_enum == LunarSpellId.LUNAR_SHIELD:
            # caster.add_status_effect("lunar_shield_active") # Example
            message += f" {caster.name} is now shielded from the next draw effect (effect needs game logic)."
            print(f"Debug: {caster.name} gained Lunar Shield.")

        else:  # Covers SHADOW_SWAP_PEEK and any others
            message += f" (Effect '{spell_to_cast.spell_id}' needs to be applied by game logic)."
            print(f"Debug: Spell '{spell_to_cast.spell_id}' cast by {caster.name}.")

        return True, message


class SolarSpells:
    def __init__(self):
        self.spells: Dict[SolarSpellId, Spell] = {}  # Use Enum as key
        self._initialize_spells()

    def _initialize_spells(self) -> None:
        # Placeholder Solar Spells
        self.spells[SolarSpellId.SUN_FLARE_DISCARD] = Spell(
            name="Sun Flare Discard",
            mana_cost=3,
            description="Force a target player to discard a random card.",
            spell_id=SolarSpellId.SUN_FLARE_DISCARD.value,  # Store string value
            targetable=True,
        )
        self.spells[SolarSpellId.SOLAR_BOOST] = Spell(
            name="Solar Boost",
            mana_cost=4,
            description="Your next played number card counts as +2 to its value for stacking (if applicable) or a game objective.",
            spell_id=SolarSpellId.SOLAR_BOOST.value,
        )
        # More spells

    def display_spells(self) -> str:
        if not self.spells:
            return "No Solar spells known."
        display = ["Available Solar Spells:"]
        for spell_id_enum, spell in self.spells.items():  # Iterate with Enum
            display.append(f"  [{spell_id_enum.name}] {spell}")  # Display Enum name
        return "\n".join(display)

    def cast_spell(
        self,
        caster: "Player",
        spell_id_enum: SolarSpellId,  # Expect Enum member
        game_context: "UnoGame",
        target_player: Optional["Player"] = None,
    ) -> Tuple[bool, str]:
        """
        Casts a solar spell.
        Returns (success, message).
        """
        spell_to_cast = self.spells.get(spell_id_enum)
        if not spell_to_cast:
            return False, f"Unknown Solar spell: {spell_id_enum}."

        if caster.solar_mana < spell_to_cast.mana_cost:
            return (
                False,
                f"Not enough Solar Mana. You have {caster.solar_mana}, need {spell_to_cast.mana_cost}.",
            )

        if spell_to_cast.targetable and target_player is None:
            return False, f"Spell '{spell_to_cast.name}' requires a target player."

        caster.solar_mana -= spell_to_cast.mana_cost
        message = f"{caster.name} casts {spell_to_cast.name} (cost {spell_to_cast.mana_cost} Solar Mana)."

        # Placeholder for spell effects
        if spell_id_enum == SolarSpellId.SUN_FLARE_DISCARD and target_player:
            message += f" Targeting {target_player.name}."
            # if not target_player.is_hand_empty():
            #     discarded = target_player.remove_card_from_hand(random.choice(target_player.hand)) # Needs better removal
            #     game_context.deck.add_to_discard(discarded)
            #     message += f" {target_player.name} discards {discarded}."
            # else: message += f" {target_player.name} has no cards to discard."
            message += f" ({target_player.name} should discard a random card - effect needs full game logic integration)."
            print(f"Debug: {target_player.name} targeted by Sun Flare Discard.")
        else:  # Covers SOLAR_BOOST and any others
            message += f" (Effect '{spell_to_cast.spell_id}' needs to be applied by game logic)."
            print(f"Debug: Spell '{spell_to_cast.spell_id}' cast by {caster.name}.")

        return True, message


if __name__ == "__main__":
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
        player_merlin,  # type: ignore
        LunarSpellId.MOONBEAM_DRAW,
        dummy_game,  # type: ignore
        target_player=player_morgana,  # type: ignore
    )
    print(msg)
    print(f"Merlin's Lunar Mana: {player_merlin.lunar_mana}")

    success, msg = solar_magic.cast_spell(
        player_merlin,  # type: ignore
        SolarSpellId.SUN_FLARE_DISCARD,
        dummy_game,  # type: ignore
        target_player=player_morgana,  # type: ignore
    )
    print(msg)
    print(f"Merlin's Solar Mana: {player_merlin.solar_mana}")

    # Test invalid spell ID (would be a type error if strict typing on cast_spell's spell_id_enum was fully enforced by caller)
    # For now, this demonstrates the .get() returning None and the "Unknown" message path.
    # To truly test this, we'd need to pass a value not in the LunarSpellId enum.
    # Example of how one might try to test an invalid string if the method accepted strings:
    # success, msg = lunar_magic.cast_spell(player_merlin, "invalid_spell_string_id", dummy_game)
    # print(msg)

    player_arthur = DummyPlayer("Arthur", lunar=1, solar=1)
    success, msg = lunar_magic.cast_spell(
        player_arthur,  # type: ignore
        LunarSpellId.LUNAR_SHIELD,
        dummy_game,  # type: ignore
    )
    print(msg)  # Not enough mana
