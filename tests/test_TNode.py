import unittest
from unittest import TestCase, main

import tn
from tn import createTNodeExpFromPyExp, replaceAdd, insertAdd, deleteAdd


class TestParseTree(unittest.TestCase):
    def __init__(self, correctValue, input):
        super(TestParseTree, self).__init__()
        self.correctValue = correctValue
        self.result = self.test(input)

    def test(self, input):
        return createTNodeExpFromPyExp(input).toPyExp()

    def runTest(self):
        self.assertEqual(self.result, self.correctValue)

class TestTnodeIndex(TestCase):
    def __init__(self, correctValue, inputArray, inputIndex):
        super(TestTnodeIndex, self).__init__()
        self.correctAnswer = correctValue
        self.result = self.test(inputArray, inputIndex)

    def test(self, inputArray, inputIndex):
        tree = createTNodeExpFromPyExp(inputArray)
        node, index = tn.tnodeIndex(tree, inputIndex)
        return node.child

    def runTest(self):
        self.assertEqual(self.result, self.correctAnswer)



def getTests(testCaseClass):
    return unittest.TestLoader().loadTestsFromTestCase(testCaseClass)

def suite():
    suite = unittest.TestSuite()
    vals = [[11], [11, 15], [11, 15, 17], [[10]], [22, [33, 44]], [22, [11, 10, [9]], [33, 44], 17]]
    suite.addTests(TestParseTree(val, val) for val in vals)

    vals = [0, 1, 2, 3, 4]
    suite.addTests(TestTnodeIndex(val, vals, val) for val in vals)

    suite.addTest(getTests(TestPyListFuncs))
    suite.addTest(getTests(TestParseNumberedExp))
    suite.addTest(getTests(TestOpAtAdd))
    return suite


class TestCreateTreeFromSexp(TestCase):

    def test_createTree(self):
        val = 22
        tree = createTNodeExpFromPyExp(val)
        self.assertEqual(tree, val)


class TestPyListFuncs(TestCase):
    def test_foldrpy(self):
        lst = [1, 2, 3, 4, 5]
        tlst = tn.foldrpy(tn.cons, lst)
        self.assertEqual(tlst.toPyExp(), lst)

    def test_foldrtpy(self):
        lst = [[1, 33], 5, ["string", 7], 41]
        tlst = tn.foldrtpy(tn.cons, lst)
        self.assertEqual(tlst.toPyExp(), lst)


class TestParseNumberedExp(TestCase):
    def test_pne1(self):
        input = ['#', ['#', 2, 'val2']]
        output = ['val2']
        tree = tn.createTNodeExpFromPyNumberedExp(input)
        self.assertEqual(tree.toPyExp(), output)

    def test_pne2(self):
        input = ['#', ['#', 2, 'val2'], ['#', 3, 'val3']]
        output = ['val2', 'val3']
        tree = tn.createTNodeExpFromPyNumberedExp(input)
        self.assertEqual(tree.toPyExp(), output)


    def test_pne3(self):
        input = ['#', [['#', 2, 106], ['#', 3, 'notstring'], ['#', 4, 207], ['#', 5, 'gime']]]
        output = [[106, "notstring", 207, 'gime']]
        tree = tn.createTNodeExpFromPyNumberedExp(input)
        self.assertEqual(tree.toPyExp(), output)



class TestOpAtAdd(TestCase):
    def setUp(self):
        self.tree1 = createTNodeExpFromPyExp([1, 2, 3, 4])
        self.tree2 = createTNodeExpFromPyExp([1, 2, [11, 22, 33], 3, 4])
        self.tree3 = createTNodeExpFromPyExp([1, 2, [11, 22, [101], 33], 3, 4])

    def test_replace(self):
        newTree = replaceAdd(self.tree1, [0], 5)
        self.assertEqual(newTree.toPyExp(), [5, 2, 3, 4])

    def test_replace2(self):
        newTree = replaceAdd(self.tree1, [1], 5)
        self.assertEqual(newTree.toPyExp(), [1, 5, 3, 4])

    def test_replace3(self):
        newTree = replaceAdd(self.tree1, [3], 5)
        self.assertEqual(newTree.toPyExp(), [1, 2, 3, 5])

    def test_replace4(self):
        newTree = replaceAdd(self.tree2, [1], 5)
        self.assertEqual(newTree.toPyExp(), [1, 5, [11, 22, 33], 3, 4])

    def test_replace5(self):
        newTree = replaceAdd(self.tree2, [2], 5)
        self.assertEqual(newTree.toPyExp(), [1, 2, 5, 3, 4])

    def test_replace11(self):
        newTree = replaceAdd(self.tree2, [2, 0], 5)
        self.assertEqual(newTree.toPyExp(), [1, 2, [5, 22, 33], 3, 4])

    def test_replace12(self):
        newTree = replaceAdd(self.tree2, [2, 2], 5)
        self.assertEqual(newTree.toPyExp(), [1, 2, [11, 22, 5], 3, 4])

    def test_replaceRec(self):
        newTree = replaceAdd(self.tree2, [2, 2], self.tree1)
        self.assertEqual(newTree.toPyExp(), [1, 2, [11, 22, [1, 2, 3, 4]], 3, 4])

    def test_replace13(self):
        newTree = replaceAdd(self.tree3, [2, 2, 0], 5)
        self.assertEqual(newTree.toPyExp(), [1, 2, [11, 22, [5], 33], 3, 4])

    def test_insert(self):
        newTree = insertAdd(self.tree1, [0], 5)
        self.assertEqual(newTree.toPyExp(), [5, 1, 2, 3, 4])

    def test_insert2(self):
        newTree = insertAdd(self.tree1, [1], 5)
        self.assertEqual(newTree.toPyExp(), [1, 5, 2, 3, 4])

    def test_insert3(self):
        newTree = insertAdd(self.tree1, [4], 5)
        self.assertEqual(newTree.toPyExp(), [1, 2, 3, 4, 5])

    def test_insert11(self):
        newTree = insertAdd(self.tree2, [2, 0], 5)
        self.assertEqual(newTree.toPyExp(), [1, 2, [5, 11, 22, 33], 3, 4])

    def test_insert12(self):
        newTree = insertAdd(self.tree2, [2, 2], 5)
        self.assertEqual(newTree.toPyExp(), [1, 2, [11, 22, 5, 33], 3, 4])

    def test_insert13(self):
        newTree = insertAdd(self.tree3, [2, 2, 0], 5)
        self.assertEqual(newTree.toPyExp(), [1, 2, [11, 22, [5, 101], 33], 3, 4])

    def test_delete(self):
        newTree = deleteAdd(self.tree1, [0])
        self.assertEqual(newTree.toPyExp(), [2, 3, 4])

    def test_delete2(self):
        newTree = deleteAdd(self.tree1, [1])
        self.assertEqual(newTree.toPyExp(), [1, 3, 4])

    def test_delete3(self):
        newTree = deleteAdd(self.tree1, [3])
        self.assertEqual(newTree.toPyExp(), [1, 2, 3])

    def test_delete11(self):
        newTree = deleteAdd(self.tree2, [2, 0])
        self.assertEqual(newTree.toPyExp(), [1, 2, [22, 33], 3, 4])

    def test_delete12(self):
        newTree = deleteAdd(self.tree2, [2, 2])
        self.assertEqual(newTree.toPyExp(), [1, 2, [11, 22], 3, 4])

    def test_delete13(self):
        newTree = deleteAdd(self.tree3, [2, 2, 0])
        self.assertEqual(newTree.toPyExp(), [1, 2, [11, 22, None, 33], 3, 4])





if __name__ == '__main__':

    unittest.TextTestRunner(verbosity=2).run(suite())
