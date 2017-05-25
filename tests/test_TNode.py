import unittest
from unittest import TestCase, main
import os, sys

import tn
from tn import createTNodeExpFromPyExp, replaceAdd, insertAdd, deleteAdd


def suite():

    class KnownGood(unittest.TestCase):
        def __init__(self, input, output):
            super(KnownGood, self).__init__()
            self.input = input
            self.output = output
        def runTest(self):
            self.assertEqual(createTNodeExpFromPyExp(self.input).toPyExp(), self.output)

    suite = unittest.TestSuite()
    vals = [[11], [11, 15], [11, 15, 17], 7]
    suite.addTests(KnownGood(val, val) for val in vals)
    return suite

test_suiteTest = suite()

class TestCreateTreeFromSexp(TestCase):

    def test_createTree(self):
        val = 22
        tree = createTNodeExpFromPyExp(val)
        self.assertEqual(tree, val)

    def test_createTree2(self):
        vals = [[11], [11, 15], [11, 15, 17]]
        val = [11]
        tree = createTNodeExpFromPyExp(val)
        self.assertEqual(tree.toPyExp(), val)


    def test_createTree3(self):
        val = [11, 15]
        tree = createTNodeExpFromPyExp(val)
        self.assertEqual(tree.toPyExp(), val)

    def test_createTree4(self):
        val = [11, 15, 17]
        tree = createTNodeExpFromPyExp(val)
        self.assertEqual(tree.toPyExp(), val)

    def test_createTreeRec(self):
        val = [[10]]
        tree = createTNodeExpFromPyExp(val)
        self.assertEqual(tree.toPyExp(), val)

    def test_createTreeRec2(self):
        val = [22, [33, 44]]
        tree = createTNodeExpFromPyExp(val)
        self.assertEqual(tree.toPyExp(), val)

    def test_createTreeRec3(self):
        val = [22, [11, 10, [9]], [33, 44], 17]
        tree = createTNodeExpFromPyExp(val)
        self.assertEqual(tree.toPyExp(), val)


class testPyListFuncs(TestCase):
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

    # unit_dir='.'
    # test_modules=[filename.replace('.py','') for filename in os.listdir(unit_dir)
    #               if filename.endswith('.py') and filename.startswith('test_')]
    # map(__import__,test_modules)
    #
    # suite = unittest.TestSuite()
    # for mod in [sys.modules[modname] for modname in test_modules]:
    #     suite.addTest(unittest.TestLoader().loadTestsFromModule(mod))
    # unittest.TextTestRunner(verbosity=2).run(suite)



    #suite = unittest.TestSuite()
    #suite.addTest(unittest.TestLoader().loadTestsFromModule(test_eval))
    #unittest.TextTestRunner(verbosity=2).run(suite)
    #unittest.
    unittest.TextTestRunner(verbosity=2).run(suite())
    #main()