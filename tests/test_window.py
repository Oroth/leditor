from unittest import TestCase
import sys
sys.path.append(".")

#from .. import window
from window import *

class TestWindow(TestCase):
    def test_window(self):
        window = Window()
        self.assertEqual(window, window)

    def test_stdWindow(self):
        window = StdWindow()
        self.assertEqual(window, window)
