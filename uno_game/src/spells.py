# Placeholder for Lunar and Solar Spells

from typing import TYPE_CHECKING, Tuple, Dict, Any

if TYPE_CHECKING:
    from .player import Player
    from .game import UnoGame # For spells that might affect game state or other players

class Spell:
    def __init__(self, name: str, mana_cost: int, description: str, spell_id: str, targetable: bool = False):
        self.name = name
        self.mana_cost = mana_cost
        self.description = description
        self.spell_id = spell_id
        self.targetable = targetable # Does the spell require a target player?

    def __str__(self):
        return f"{self.name} (Cost: {self.mana_cost} mana) - {self.description}"

class LunarSpells:
    def __init__(self):
        self.spells: Dict[str, Spell] = {}
        self._initialize_spells()

    def _initialize_spells(self):
        # Placeholder Lunar Spells
        self.spells["moonbeam_draw"] = Spell(
            name="Moonbeam Draw",
            mana_cost=3,
            description="Force a target player to draw 1 card.",
            spell_id="moonbeam_draw",
            targetable=True
        )
        self.spells["lunar_shield"] = Spell(
            name="Lunar Shield",
            mana_cost=5,
            description="Protect yourself from the next 'draw' effect (e.g., Draw 2, Draw 4) played against you.",
            spell_id="lunar_shield"
        )
        self.spells["shadow_swap_peek"] = Spell(
            name="Shadow Swap Peek",
            mana_cost=4,
            description="Peek at one card from a target player's hand, then you may swap it with one of yours.",
            spell_id="shadow_swap_peek",
            targetable=True
        )
        # More spells

    def display_spells(self) -> str:
        if not self.spells:
            return "No Lunar spells known."
        display = ["Available Lunar Spells:"]
        for spell_id, spell in self.spells.items():
            display.append(f"  [{spell_id}] {spell}")
        return "\n".join(display)

    def cast_spell(self, caster: 'Player', spell_id: str, game_context: 'UnoGame', target_player: Optional['Player'] = None) -> Tuple[bool, str]:
        """
        Casts a lunar spell.
        Returns (success, message).
        Actual application of spell effect is handled by game logic.
        """
        spell_to_cast = self.spells.get(spell_id)
        if not spell_to_cast:
            return False, "Unknown Lunar spell."

        if caster.lunar_mana < spell_to_cast.mana_cost:
            return False, f"Not enough Lunar Mana. You have {caster.lunar_mana}, need {spell_to_cast.mana_cost}."

        if spell_to_cast.targetable and target_player is None:
            return False, f"Spell '{spell_to_cast.name}' requires a target player."

        if spell_to_cast.targetable and target_player == caster:
            # Some targetable spells might allow self-targeting, others not. Add specific checks if needed.
             pass


        caster.lunar_mana -= spell_to_cast.mana_cost

        message = f"{caster.name} casts {spell_to_cast.name} (cost {spell_to_cast.mana_cost} Lunar Mana)."

        # Placeholder for spell effects - these would modify game_context or players
        if spell_to_cast.spell_id == "moonbeam_draw" and target_player:
            message += f" Targeting {target_player.name}."
            # game_context.player_draws_card(target_player, 1) # Example of direct effect
            # In reality, this might return an action for the game loop to process.
            message += f" ({target_player.name} should draw 1 card - effect needs full game logic integration)."
            print(f"Debug: {target_player.name} targeted by Moonbeam Draw.")

        elif spell_to_cast.spell_id == "lunar_shield":
            # caster.add_status_effect("lunar_shield_active") # Example
            message += f" {caster.name} is now shielded from the next draw effect (effect needs game logic)."
            print(f"Debug: {caster.name} gained Lunar Shield.")

        else:
            message += f" (Effect '{spell_to_cast.spell_id}' needs to be applied by game logic)."
            print(f"Debug: Spell '{spell_to_cast.spell_id}' cast by {caster.name}.")


        return True, message

class SolarSpells:
    def __init__(self):
        self.spells: Dict[str, Spell] = {}
        self._initialize_spells()

    def _initialize_spells(self):
        # Placeholder Solar Spells
        self.spells["sun_flare_discard"] = Spell(
            name="Sun Flare Discard",
            mana_cost=3,
            description="Force a target player to discard a random card.",
            spell_id="sun_flare_discard",
            targetable=True
        )
        self.spells["solar_boost"] = Spell(
            name="Solar Boost",
            mana_cost=4,
            description="Your next played number card counts as +2 to its value for stacking (if applicable) or a game objective.",
            spell_id="solar_boost"
        )
        # More spells

    def display_spells(self) -> str:
        if not self.spells:
            return "No Solar spells known."
        display = ["Available Solar Spells:"]
        for spell_id, spell in self.spells.items():
            display.append(f"  [{spell_id}] {spell}")
        return "\n".join(display)

    def cast_spell(self, caster: 'Player', spell_id: str, game_context: 'UnoGame', target_player: Optional['Player'] = None) -> Tuple[bool, str]:
        """
        Casts a solar spell.
        Returns (success, message).
        """
        spell_to_cast = self.spells.get(spell_id)
        if not spell_to_cast:
            return False, "Unknown Solar spell."

        if caster.solar_mana < spell_to_cast.mana_cost:
            return False, f"Not enough Solar Mana. You have {caster.solar_mana}, need {spell_to_cast.mana_cost}."

        if spell_to_cast.targetable and target_player is None:
            return False, f"Spell '{spell_to_cast.name}' requires a target player."

        caster.solar_mana -= spell_to_cast.mana_cost
        message = f"{caster.name} casts {spell_to_cast.name} (cost {spell_to_cast.mana_cost} Solar Mana)."

        # Placeholder for spell effects
        if spell_to_cast.spell_id == "sun_flare_discard" and target_player:
            message += f" Targeting {target_player.name}."
            # if not target_player.is_hand_empty():
            #     discarded = target_player.remove_card_from_hand(random.choice(target_player.hand)) # Needs better removal
            #     game_context.deck.add_to_discard(discarded)
            #     message += f" {target_player.name} discards {discarded}."
            # else: message += f" {target_player.name} has no cards to discard."
            message += f" ({target_player.name} should discard a random card - effect needs full game logic integration)."
            print(f"Debug: {target_player.name} targeted by Sun Flare Discard.")
        else:
            message += f" (Effect '{spell_to_cast.spell_id}' needs to be applied by game logic)."
            print(f"Debug: Spell '{spell_to_cast.spell_id}' cast by {caster.name}.")

        return True, message

if __name__ == '__main__':
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

    class DummyGame: # Placeholder for UnoGame context
        pass

    player_merlin = DummyPlayer("Merlin", lunar=10, solar=10)
    player_morgana = DummyPlayer("Morgana")
    dummy_game = DummyGame()

    print("\n--- Merlin's Casts ---")
    success, msg = lunar_magic.cast_spell(player_merlin, "moonbeam_draw", dummy_game, target_player=player_morgana)
    print(msg)
    print(f"Merlin's Lunar Mana: {player_merlin.lunar_mana}")

    success, msg = solar_magic.cast_spell(player_merlin, "sun_flare_discard", dummy_game, target_player=player_morgana)
    print(msg)
    print(f"Merlin's Solar Mana: {player_merlin.solar_mana}")

    success, msg = lunar_magic.cast_spell(player_merlin, "bad_spell_id", dummy_game)
    print(msg) # Unknown

    player_arthur = DummyPlayer("Arthur", lunar=1, solar=1)
    success, msg = lunar_magic.cast_spell(player_arthur, "lunar_shield", dummy_game)
    print(msg) # Not enough mana
