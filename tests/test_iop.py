#from unittest import TestCase, main
import unittest
import sys
sys.path.append(".")
import iop

class TestKey(unittest.TestCase):
    def test_key1(self):
        self.assertEqual(1, 1)

    def test_key2(self):
        self.assertEqual(1, 2)

if __name__ == '__main__':

    unittest.main()