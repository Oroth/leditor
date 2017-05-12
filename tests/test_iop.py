#from unittest import TestCase, main
import unittest
import sys
sys.path.append(".")
from iop import *

class TestKey(unittest.TestCase):
    def test_key1(self):
        k = Key.c('a')
        self.assertEqual(k.char, 'a')

    def test_key2(self):
        k = Key.c('A')
        self.assertEqual(k.char, 'A')
        self.assertEqual(k.shift(), True)

    def test_key3(self):
        k = Key.c('b')
        self.assertEqual(k.code, KEY_CHAR)

    def test_keyShift(self):
        k = Key.c('a', shift=True)
        self.assertEqual(k.char, 'A')

    def test_keyvk(self):
        k = Key.vk(KEY_ENTER)
        self.assertEqual(k.code, KEY_ENTER)


    def test_keySpace(self):
        k = Key.c(' ')
        self.assertEqual(k.code, KEY_SPACE)

    #def test_keyEnter(self):
    #    k = Key.c(chr(13))
    #    self.assertEqual(k.code(), KEY_ENTER)


    def test_keyvk2(self):
        k = Key.vk(KEY_DOWN)
        self.assertEqual(k.char, chr(0))

    def test_keyctrl(self):
        k = Key.vk(KEY_DOWN, ctrl=True)
        self.assertEqual(k.ctrl(), True)

    def test_printable(self):
        k = Key.vk(KEY_DOWN)
        self.assertEqual(k.isPrintable(), False)

if __name__ == '__main__':
    unittest.main()