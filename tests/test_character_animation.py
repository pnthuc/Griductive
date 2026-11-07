import unittest
from griductive.ui.character_animation import CharacterAnimation


class ExpressionTest(unittest.TestCase):
    def test_blink_reaction_and_recovery(self):
        a=CharacterAnimation();a.advance(.06);self.assertEqual(a.frame,0)
        self.assertGreater(a.blink_amount,0.);self.assertLess(a.blink_amount,1.)
        a.advance(.05);self.assertEqual(a.blink_amount,1.)
        a.advance(.2);self.assertEqual(a.frame,0);self.assertEqual(a.blink_amount,0.)
        a.react();self.assertEqual(a.frame,2)
        a.advance(.7);self.assertEqual(a.frame,0)

    def test_confirmed_states_and_bars(self):
        a=CharacterAnimation();a.set_status('INNOCENT');self.assertEqual(a.frame,3)
        self.assertEqual(a.bars_progress,0.)
        a.advance(1.);self.assertEqual(a.frame,4)
        a.set_status('CRIMINAL');self.assertEqual(a.frame,5)
        self.assertEqual(a.bars_progress,0.)
        a.advance(.325);self.assertAlmostEqual(a.bars_progress,.5)
        a.advance(.5);self.assertEqual(a.frame,6);self.assertEqual(a.bars_progress,1.)
        a.set_status(None);self.assertEqual(a.bars_progress,0.)

    def test_negative_time_does_not_extend_reaction(self):
        a=CharacterAnimation();a.react();a.advance(-1.)
        self.assertEqual(a.elapsed,0.);self.assertEqual(a.reaction,.65)
