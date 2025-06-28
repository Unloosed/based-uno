import unittest
from src.card import Card, Color, Rank # Corrected import path relative to project root

class TestCard(unittest.TestCase):

    def test_card_creation(self):
        card = Card(Color.RED, Rank.FIVE)
        self.assertEqual(card.color, Color.RED)
        self.assertEqual(card.rank, Rank.FIVE)
        self.assertEqual(card.active_color, Color.RED) # Should be same as color initially

    def test_wild_card_creation(self):
        wild_card = Card(Color.WILD, Rank.WILD)
        self.assertEqual(wild_card.color, Color.WILD)
        self.assertEqual(wild_card.rank, Rank.WILD)
        self.assertEqual(wild_card.active_color, Color.WILD) # Active color starts as WILD

        wd4 = Card(Color.WILD, Rank.WILD_DRAW_FOUR)
        self.assertEqual(wd4.color, Color.WILD)
        self.assertEqual(wd4.rank, Rank.WILD_DRAW_FOUR)

    def test_wild_card_auto_color_correction(self):
        # If a color like RED is passed with Rank.WILD, it should be corrected to Color.WILD
        card = Card(Color.RED, Rank.WILD)
        self.assertEqual(card.color, Color.WILD)
        self.assertEqual(card.rank, Rank.WILD)

    def test_invalid_card_creation(self):
        with self.assertRaises(TypeError):
            Card("RED", Rank.FIVE)  # Invalid color type
        with self.assertRaises(TypeError):
            Card(Color.RED, "FIVE") # Invalid rank type
        with self.assertRaises(ValueError):
            # Non-wild ranks cannot have WILD color
            Card(Color.WILD, Rank.ONE)

    def test_card_string_representation(self):
        red_five = Card(Color.RED, Rank.FIVE)
        self.assertEqual(str(red_five), "RED FIVE")

        blue_skip = Card(Color.BLUE, Rank.SKIP)
        self.assertEqual(str(blue_skip), "BLUE SKIP")

        wild = Card(Color.WILD, Rank.WILD)
        self.assertEqual(str(wild), "WILD") # Before color is chosen
        wild.active_color = Color.GREEN
        self.assertEqual(str(wild), "WILD (GREEN)") # After color is chosen

        wd4 = Card(Color.WILD, Rank.WILD_DRAW_FOUR)
        self.assertEqual(str(wd4), "WILD_DRAW_FOUR")
        wd4.active_color = Color.BLUE
        self.assertEqual(str(wd4), "WILD (BLUE)") # Note: WD4 str might also show (BLUE)

    def test_card_equality(self):
        card1 = Card(Color.RED, Rank.ONE)
        card2 = Card(Color.RED, Rank.ONE)
        card3 = Card(Color.BLUE, Rank.ONE)
        card4 = Card(Color.RED, Rank.TWO)

        self.assertEqual(card1, card2)
        self.assertNotEqual(card1, card3)
        self.assertNotEqual(card1, card4)
        self.assertNotEqual(card1, "RED ONE") # Test against different type

    def test_card_hash(self):
        # Test that equal cards have the same hash (for set/dict usage)
        card1 = Card(Color.RED, Rank.ONE)
        card2 = Card(Color.RED, Rank.ONE)
        self.assertEqual(hash(card1), hash(card2))

        card_set = {card1, card2}
        self.assertEqual(len(card_set), 1)

        card3 = Card(Color.BLUE, Rank.ONE)
        card_set.add(card3)
        self.assertEqual(len(card_set), 2)

    def test_is_special_action(self):
        self.assertTrue(Card(Color.RED, Rank.DRAW_TWO).is_special_action())
        self.assertTrue(Card(Color.BLUE, Rank.SKIP).is_special_action())
        self.assertTrue(Card(Color.GREEN, Rank.REVERSE).is_special_action())
        self.assertFalse(Card(Color.YELLOW, Rank.FIVE).is_special_action())
        self.assertFalse(Card(Color.WILD, Rank.WILD).is_special_action()) # Wilds are not "special action" in this context

    def test_is_wild(self):
        self.assertTrue(Card(Color.WILD, Rank.WILD).is_wild())
        self.assertTrue(Card(Color.WILD, Rank.WILD_DRAW_FOUR).is_wild())
        self.assertFalse(Card(Color.RED, Rank.DRAW_TWO).is_wild())
        self.assertFalse(Card(Color.BLUE, Rank.FIVE).is_wild())

    def test_card_matches(self):
        red_five = Card(Color.RED, Rank.FIVE)
        red_seven = Card(Color.RED, Rank.SEVEN)
        blue_five = Card(Color.BLUE, Rank.FIVE)
        green_two = Card(Color.GREEN, Rank.TWO)

        # Color match
        self.assertTrue(red_seven.matches(red_five))
        # Rank match
        self.assertTrue(blue_five.matches(red_five))
        # No match
        self.assertFalse(green_two.matches(red_five))

        # Wild card matching
        wild_card = Card(Color.WILD, Rank.WILD)
        # Wild card can be played on anything
        self.assertTrue(wild_card.matches(red_five))
        self.assertTrue(wild_card.matches(green_two))

        # Playing on a wild card
        # If wild_on_table has active_color BLUE
        wild_on_table = Card(Color.WILD, Rank.WILD) # Its own color is WILD
        # wild_on_table.active_color = Color.BLUE # This would be set by game state (current_wild_color)

        blue_card = Card(Color.BLUE, Rank.ONE)
        red_card = Card(Color.RED, Rank.ONE)

        self.assertTrue(blue_card.matches(wild_on_table, current_color_chosen_for_wild=Color.BLUE))
        self.assertFalse(red_card.matches(wild_on_table, current_color_chosen_for_wild=Color.BLUE))
        # If no color chosen for wild on table (e.g. start of game), should not match non-wilds
        self.assertFalse(blue_card.matches(wild_on_table, current_color_chosen_for_wild=None))
        # An unchosen wild should still match its own color (WILD), which another Wild card would do
        another_wild = Card(Color.WILD, Rank.WILD_DRAW_FOUR)
        self.assertTrue(another_wild.matches(wild_on_table, current_color_chosen_for_wild=None)) # Wild on Wild
        self.assertTrue(another_wild.matches(wild_on_table, current_color_chosen_for_wild=Color.RED)) # Wild on chosen Wild


if __name__ == '__main__':
    unittest.main()
