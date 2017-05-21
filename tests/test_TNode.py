import unittest
from unittest import TestCase, main
import os, sys

import tn
from tn import createTNodeExpFromPyExp, replaceAdd, insertAdd, deleteAdd


__author__ = 'chephren'

# class TestCursor(TestCase):
#     def setUp(self):
#         self.tree = createTreeFromSexp([2, 4, 6, [11, [101, 202], 33], 8, 9])
#
#     def test_next(self):
#         c = Buffer(self.tree, [0]).next()
#         self.assertEqual(c.get().child, 4)
#
#     def test_next2(self):
#         c = Buffer(self.tree, [0]).next().next()
#         self.assertEqual(c.get().child, 6)
#
#     def test_next3(self):
#         c = Buffer(self.tree, [3, 0]).next()
#         self.assertEqual(c.BufferToPySexp(), [101, 202])
#
#     def test_prev(self):
#         c = Buffer(self.tree, [2]).prev()
#         self.assertEqual(c.get().child, 4)
#
#     def test_prev2(self):
#         c = Buffer(self.tree, [3]).prev().prev()
#         self.assertEqual(c.get().child, 4)
#
#     def test_prev3(self):
#         c = Buffer(self.tree, [3, 1]).prev()
#         self.assertEqual(c.get().child, 11)
#
#     def test_up(self):
#         c = Buffer(self.tree, [3, 1]).up()
#         self.assertEqual(c.BufferToPySexp(), [11, [101, 202], 33])
#
#     def test_up2(self):
#         c = Buffer(self.tree, [3, 2, 0]).up().up()
#         self.assertEqual(c.BufferToPySexp(), [11, [101, 202], 33])
#
#     #    def test_up3(self):
#     #        tree = createTreeFromSexp([11, 15, [101, 202], 17])
#     #        c = Buffer(tree, [2, 1]).prev()
#     #        self.assertEqual(c.get().child, 101)
#
#     def test_child(self):
#         tree = createTreeFromSexp([11, 15, [55, 66], 19])
#         c = Buffer(tree, [2]).child()
#         self.assertEqual(c.get().child, 55)
#
#     def test_child2(self):
#         tree = createTreeFromSexp([11, [101, 404, [1100, 2200, 3300]], 19])
#         c = Buffer(tree, [1]).child().next().next().child()
#         self.assertEqual(c.get().child, 1100)
#
#     def test_refreshToNearest(self):
#         tree = createTreeFromSexp([11, [101, 404, [1100, 2200, 3300]], 19])
#         c = Buffer(tree, [1])
#         self.assertEqual(c.get().child.toPySexp(), [101, 404, [1100, 2200, 3300]])
#
#     def test_refreshToNearest2(self):
#         tree = createTreeFromSexp([11, [101, 404, [1100, 2200, 3300]], 19])
#         c = Buffer(tree, [1, 0])
#         self.assertEqual(c.get().child, 101)

class TestCreateTreeFromSexp(TestCase):

    def test_createTree(self):
        tree = createTNodeExpFromPyExp(22)
        self.assertEqual(tree, 22)

    def test_createTree2(self):
        tree = createTNodeExpFromPyExp([11])
        self.assertEqual(tree.toPyExp(), [11])

    def test_createTree3(self):
        tree = createTNodeExpFromPyExp([11, 15])
        self.assertEqual(tree.toPyExp(), [11, 15])

    def test_createTree4(self):
        tree = createTNodeExpFromPyExp([11, 15, 17])
        self.assertEqual(tree.toPyExp(), [11, 15, 17])

    def test_createTreeRec(self):
        tree = createTNodeExpFromPyExp([[10]])
        self.assertEqual(tree.toPyExp(), [[10]])

    def test_createTreeRec2(self):
        tree = createTNodeExpFromPyExp([22, [33, 44]])
        self.assertEqual(tree.toPyExp(), [22, [33, 44]])

class TestTNodeFunctions(TestCase):
    def test_tnodeList(self):
        tree = tn.createTNodeExpFromPyExp([11, 15, 17, 19])
        self.assertEqual(tree.toPyExp(), [11, 15, 17, 19])

    def test_tnodeExpFromPyExp(self):
        tree = tn.createTNodeExpFromPyExp([22, [33, 44]])
        self.assertEqual(tree.toPyExp(), [22, [33, 44]])

    def test_tnodeExpFromPyExp2(self):
        tree = tn.createTNodeExpFromPyExp([22, [11, 10, [9]], [33, 44], 17])
        self.assertEqual(tree.toPyExp(), [22, [11, 10, [9]], [33, 44], 17])





# class TestMiscTNode(TestCase):
#     def test_list1(self):
#         tree = unusedListFuncs.foldrpy(unusedListFuncs.cons, [1, 5, "string", 41])
#         self.assertEqual(tree.toPyExp(), [1, 5, "string", 41])
#
#     def test_list2(self):
#         tree = unusedListFuncs.foldrtpy(unusedListFuncs.cons, [[1, 33], 5, ["string", 7], 41])
#         self.assertEqual(tree.toPyExp(), [[1, 33], 5, ["string", 7], 41])
#
#     def test_list3(self):
#         tree = unusedListFuncs.parseNumberedExp(['#', 1, [['#', 2, "string"]]])
#         self.assertEqual(tree.toPyExp(), ["string"])
#
#     def test_list4(self):
#         tree = unusedListFuncs.parseNumberedExp(['#', 1, [['#', 2, 106], ['#', 3, 'notstring'], ['#', 4, 207], ['#', 5, 'gime']]])
#         self.assertEqual(tree.toPyExp(), [106, "notstring", 207, 'gime'])



class TestFunctional(TestCase):
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
    main()