from unittest import TestCase, main
from tn import TNode, createTNodeExpFromPyExp, copyTNodeExp, replaceAdd, deleteAdd, insertAdd
from buffer import Buffer

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


# class TestCopyTNode(TestCase):
#     def test_copyTNode(self):
#         tree = createTreeFromSexp([4])
#         newTree = copyTNode(tree)
#         self.assertEqual(newTree.toPySexp(), [4])
#
#     def test_copyTNode2(self):
#         tree = createTreeFromSexp([[4, 5]])
#         newTree = copyTNode(tree)
#         self.assertEqual(newTree.toPySexp(), [[4, 5]])
#
#     def test_copyTNode3(self):
#         tree = createTreeFromSexp([4, 5, 6])
#         newTree = copyTNode(tree)
#         self.assertEqual(newTree.toPySexp(), [4, 5, 6])
#
#     def test_copyTNodeRec1(self):
#         tree = createTreeFromSexp([4, [10]])
#         newTree = copyTNode(tree)
#         self.assertEqual(newTree.toPySexp(), [4, [10]])
#
#     def test_copyTNodeRec2(self):
#         tree = createTreeFromSexp([4, [10, 20]])
#         newTree = copyTNode(tree)
#         self.assertEqual(newTree.toPySexp(), [4, [10, 20]])
#
#     def test_copyTNodeRec2(self):
#         tree = createTreeFromSexp([[10, 20], 4])
#         newTree = copyTNode(tree)
#         self.assertEqual(newTree.toPySexp(), [[10, 20], 4])
#
#     def test_copyTNodeRec3(self):
#         tree = createTreeFromSexp([4, [10], [20, [101]]])
#         newTree = copyTNode(tree)
#         self.assertEqual(newTree.toPySexp(), [4, [10], [20, [101]]])
#
#     def test_copyTNodeRec4(self):
#         tree = createTreeFromSexp([[4], [10, 15], [20, [101, 202]]])
#         newTree = copyTNode(tree)
#         self.assertEqual(newTree.toPySexp(), [[4], [10, 15], [20, [101, 202]]])
#
# class TestFunctional(TestCase):
#     def setUp(self):
#         self.tree1 = createTreeFromSexp([1, 2, 3, 4])
#         self.tree2 = createTreeFromSexp([1, 2, [11, 22, 33], 3, 4])
#         self.tree3 = createTreeFromSexp([1, 2, [11, 22, [101], 33], 3, 4])
#
#     def test_replace(self):
#         newTree = replaceAdd(self.tree1, [0], 5)
#         self.assertEqual(newTree.toPySexp(), [5, 2, 3, 4])
#
#     def test_replace2(self):
#         newTree = replaceAdd(self.tree1, [1], 5)
#         self.assertEqual(newTree.toPySexp(), [1, 5, 3, 4])
#
#     def test_replace3(self):
#         newTree = replaceAdd(self.tree1, [3], 5)
#         self.assertEqual(newTree.toPySexp(), [1, 2, 3, 5])
#
#     def test_replace4(self):
#         newTree = replaceAdd(self.tree2, [1], 5)
#         self.assertEqual(newTree.toPySexp(), [1, 5, [11, 22, 33], 3, 4])
#
#     def test_replace5(self):
#         newTree = replaceAdd(self.tree2, [2], 5)
#         self.assertEqual(newTree.toPySexp(), [1, 2, 5, 3, 4])
#
#     def test_replace11(self):
#         newTree = replaceAdd(self.tree2, [2, 0], 5)
#         self.assertEqual(newTree.toPySexp(), [1, 2, [5, 22, 33], 3, 4])
#
#     def test_replace12(self):
#         newTree = replaceAdd(self.tree2, [2, 2], 5)
#         self.assertEqual(newTree.toPySexp(), [1, 2, [11, 22, 5], 3, 4])
#
#     def test_replaceRec(self):
#         newTree = replaceAdd(self.tree2, [2, 2], self.tree1)
#         self.assertEqual(newTree.toPySexp(), [1, 2, [11, 22, [1, 2, 3, 4]], 3, 4])
#
#     def test_replace13(self):
#         newTree = replaceAdd(self.tree3, [2, 2, 0], 5)
#         self.assertEqual(newTree.toPySexp(), [1, 2, [11, 22, [5], 33], 3, 4])
#
#     def test_insert(self):
#         newTree = insertAdd(self.tree1, [0], 5)
#         self.assertEqual(newTree.toPySexp(), [5, 1, 2, 3, 4])
#
#     def test_insert2(self):
#         newTree = insertAdd(self.tree1, [1], 5)
#         self.assertEqual(newTree.toPySexp(), [1, 5, 2, 3, 4])
#
#     def test_insert3(self):
#         newTree = insertAdd(self.tree1, [4], 5)
#         self.assertEqual(newTree.toPySexp(), [1, 2, 3, 4, 5])
#
#     def test_insert11(self):
#         newTree = insertAdd(self.tree2, [2, 0], 5)
#         self.assertEqual(newTree.toPySexp(), [1, 2, [5, 11, 22, 33], 3, 4])
#
#     def test_insert12(self):
#         newTree = insertAdd(self.tree2, [2, 2], 5)
#         self.assertEqual(newTree.toPySexp(), [1, 2, [11, 22, 5, 33], 3, 4])
#
#     def test_insert13(self):
#         newTree = insertAdd(self.tree3, [2, 2, 0], 5)
#         self.assertEqual(newTree.toPySexp(), [1, 2, [11, 22, [5, 101], 33], 3, 4])
#
#     def test_delete(self):
#         newTree = deleteAdd(self.tree1, [0])
#         self.assertEqual(newTree.toPySexp(), [2, 3, 4])
#
#     def test_delete2(self):
#         newTree = deleteAdd(self.tree1, [1])
#         self.assertEqual(newTree.toPySexp(), [1, 3, 4])
#
#     def test_delete3(self):
#         newTree = deleteAdd(self.tree1, [3])
#         self.assertEqual(newTree.toPySexp(), [1, 2, 3])
#
#     def test_delete11(self):
#         newTree = deleteAdd(self.tree2, [2, 0])
#         self.assertEqual(newTree.toPySexp(), [1, 2, [22, 33], 3, 4])
#
#     def test_delete12(self):
#         newTree = deleteAdd(self.tree2, [2, 2])
#         self.assertEqual(newTree.toPySexp(), [1, 2, [11, 22], 3, 4])
#
#     def test_delete13(self):
#         newTree = deleteAdd(self.tree3, [2, 2, 0])
#         self.assertEqual(newTree.toPySexp(), [1, 2, [11, 22, None, 33], 3, 4])
#
#
#
#
# class TestTNode(TestCase):
#
#     def test_TNode(self):
#         node1 = TNode([1, 2, 3])
#         self.assertEqual(node1.toPySexp(), [[1, 2, 3]])
#
#     def test_toPySexp(self):
#         node1 = TNode(5)
#         self.assertEqual(node1.toPySexp(), [5])
#
#     def test_toPySexp2(self):
#         node1 = TNode(5)
#         node2 = TNode(6, None, node1)
#         node1.next = node2
#         self.assertEqual(node1.toPySexp(), [5, 6])
#
#     def test_toPySexp3(self):
#         node1 = TNode(5)
#         node2 = TNode(6)
#         node3 = TNode(7)
#         node1.next = node2
#         node2.next = node3
#         self.assertEqual(node1.toPySexp(), [5, 6, 7])
#
#     def test_toPySexpNest(self):
#         node1 = TNode(5)
#         node2 = TNode()
#         node2a = TNode(4)
#         node2b = TNode(7)
#         node3 = TNode(55)
#
#         node1.next = node2
#         node2.child = node2a
#         node2.next = node3
#
#         node2a.next = node2b
#
#         self.assertEqual(node1.toPySexp(), [5, [4, 7], 55])
#
#
#
#     #def test_activeToPySexp(self):
#     #    self.fail()
#
#
#     def test_isDataNode(self):
#         node = TNode(22)
#         self.assertFalse(node.isSubNode())
#
#     def test_isDataNode2(self):
#         node = TNode(22)
#         secondNode = TNode(node, node)
#         self.assertTrue(secondNode.isSubNode())
#
#
#     def test_insertBefore(self):
#         node1 = TNode(5)
#         node1.insertBefore(10)
#
#         self.assertEquals(node1.previous.toPySexp(), [10, 5])
#
#     def test_insertBefore2(self):
#         node1 = TNode(5)
#         node1.insertBefore(10)
#         node1.insertBefore(7)
#         first = node1.previous.previous
#
#         self.assertEquals(first.toPySexp(), [10, 7, 5])
#
#
#     def test_insertAfter(self):
#         node1 = TNode(5)
#         node1.insertAfter(10)
#
#         self.assertEquals(node1.toPySexp(), [5, 10])
#
#     def test_insertAfter2(self):
#         node1 = TNode(5)
#         node1.insertAfter(10)
#         node1.insertAfter(15)
#
#         self.assertEquals(node1.toPySexp(), [5, 15, 10])


if __name__ == '__main__':
    main()