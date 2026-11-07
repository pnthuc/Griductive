import unittest
from pathlib import Path
from PySide6.QtWidgets import QApplication
from griductive.ui.portraits import load_expression_frames

ROOT=Path(__file__).resolve().parents[1]


class SpriteRegistrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])
        cls.bank=load_expression_frames(ROOT/'assets')

    def test_atlas_seams_are_transparent(self):
        for frames in self.bank.values():
            for frame in frames:
                image=frame.toImage()
                for y in range(3):
                    self.assertTrue(all(image.pixelColor(x,y).alpha()==0 for x in range(image.width())))

    def test_blink_slot_contains_a_complete_portrait(self):
        for frames in self.bank.values():
            opened, closed = (frames[index].toImage() for index in (0, 1))
            self.assertEqual(opened.size(), closed.size())
            self.assertNotEqual(opened, closed)
            self.assertTrue(any(closed.pixelColor(x, 200).alpha() >= 240
                                for x in range(closed.width())))

    def test_pixel_frames_have_clear_borders_on_every_side(self):
        from PySide6.QtGui import QImage
        bank=load_expression_frames(ROOT/'assets')
        self.assertEqual(len(bank),25)
        for actor, frames in bank.items():
            for slot, frame in enumerate(frames):
                image=frame.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
                alpha=bytes(image.bits())[3::4]
                width,height=image.width(),image.height()
                with self.subTest(actor=actor,slot=slot):
                    self.assertTrue(any(alpha))
                    self.assertFalse(any(alpha[:8*width]))
                    self.assertFalse(any(alpha[(height-8)*width:]))
                    for y in range(height):
                        self.assertFalse(any(alpha[y*width:y*width+8]))
                        self.assertFalse(any(alpha[(y+1)*width-8:(y+1)*width]))

    def test_regenerated_poses_keep_character_dimensions(self):
        from PySide6.QtGui import QImage
        bank=load_expression_frames(ROOT/'assets')
        def bounds(frame):
            image=frame.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
            alpha=bytes(image.bits())[3::4]
            points=[(i%image.width(),i//image.width()) for i,a in enumerate(alpha) if a]
            return (min(x for x,y in points),min(y for x,y in points),
                    max(x for x,y in points),max(y for x,y in points))
        for actor in range(5,10):
            expected=bounds(bank[actor][0])
            for slot in range(1,7):
                with self.subTest(actor=actor,slot=slot):
                    actual=bounds(bank[actor][slot])
                    self.assertLessEqual(abs((actual[3]-actual[1])-(expected[3]-expected[1])),3)
                    self.assertLessEqual(abs(actual[3]-expected[3]),3)
                    self.assertLessEqual(abs((actual[2]-actual[0])-(expected[2]-expected[0])),5)
