from unittest import TestCase
import printsexp

longString = "This is a pretty long string for testing functions with"
testString = "aaaa bbbb cccc dddd eeee"


class TestsplitStringAcrossLines(TestCase):

    def test_1(self):
        result = printsexp.splitStringAcrossLines(testString, 5, 5)
        testResult = ['aaaa', 'bbbb', 'cccc', 'dddd', 'eeee']
        self.assertEqual(result, testResult)

    def test_2(self):
        result = printsexp.splitStringAcrossLines(testString, 10, 10)
        testResult = ['aaaa bbbb', 'cccc dddd', 'eeee']
        self.assertEqual(result, testResult)
