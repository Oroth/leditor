from unittest import TestCase
from TNode import TNode
from TNode import createTreeFromSexp
from TNode import copyTNode
from TNode import Cursor

__author__ = 'chephren'

class TestCursor(TestCase):
    pass


class TestTNode(TestCase):

    def test_next(self):
        tree = createTreeFromSexp([11, 15, 17])
        c = Cursor(tree, [0]).next()
        self.assertEqual(c.get().child, 15)


    def test_next2(self):
        tree = createTreeFromSexp([11, 15, 17, 19])
        c = Cursor(tree, [0]).next().next()
        self.assertEqual(c.get().child, 17)

    def test_next3(self):
        tree = createTreeFromSexp([11, 15, [101, 202], 17])
        c = Cursor(tree, [2, 0]).next()
        self.assertEqual(c.get().child, 202)

    def test_prev(self):
        tree = createTreeFromSexp([11, 15, 17])
        c = Cursor(tree, [2]).prev()
        self.assertEqual(c.get().child, 15)

    def test_prev2(self):
        tree = createTreeFromSexp([11, 15, 17, 19])
        c = Cursor(tree, [3]).prev().prev()
        self.assertEqual(c.get().child, 15)

    def test_prev3(self):
        tree = createTreeFromSexp([11, 15, [101, 202], 17])
        c = Cursor(tree, [2, 1]).prev()
        self.assertEqual(c.get().child, 101)

    def test_up(self):
        tree = createTreeFromSexp([11, 15, [55, 66], 19])
        c = Cursor(tree, [2, 1]).up()
        self.assertEqual(c.get().child.toPySexp(), [55, 66])

    def test_up2(self):
        tree = createTreeFromSexp([11, [101, 404, [1100, 2200, 3300]], 19])
        c = Cursor(tree, [1, 2, 0]).up().up()
        self.assertEqual(c.get().child.toPySexp(), [101, 404, [1100, 2200, 3300]])

#    def test_up3(self):
#        tree = createTreeFromSexp([11, 15, [101, 202], 17])
#        c = Cursor(tree, [2, 1]).prev()
#        self.assertEqual(c.get().child, 101)

    def test_child(self):
        tree = createTreeFromSexp([11, 15, [55, 66], 19])
        c = Cursor(tree, [2]).child()
        self.assertEqual(c.get().child, 55)

    def test_child2(self):
        tree = createTreeFromSexp([11, [101, 404, [1100, 2200, 3300]], 19])
        c = Cursor(tree, [1]).child().next().next().child()
        self.assertEqual(c.get().child, 1100)

    def test_refreshToNearest(self):
        tree = createTreeFromSexp([11, [101, 404, [1100, 2200, 3300]], 19])
        c = Cursor(tree, [1])
        self.assertEqual(c.get().child.toPySexp(), [101, 404, [1100, 2200, 3300]])

    def test_refreshToNearest2(self):
        tree = createTreeFromSexp([11, [101, 404, [1100, 2200, 3300]], 19])
        c = Cursor(tree, [1, 0])
        self.assertEqual(c.get().child, 101)

    def test_createTree(self):
        tree = createTreeFromSexp(22)
        self.assertEqual(tree, 22)

    def test_createTree2(self):
        tree = createTreeFromSexp([11])
        self.assertEqual(tree.toPySexp(), [11])

    def test_createTree3(self):
        tree = createTreeFromSexp([11, 15])
        self.assertEqual(tree.toPySexp(), [11, 15])

    def test_createTree4(self):
        tree = createTreeFromSexp([11, 15, 17])
        self.assertEqual(tree.toPySexp(), [11, 15, 17])

    def test_createTreeRec(self):
        tree = createTreeFromSexp([[10]])
        self.assertEqual(tree.toPySexp(), [[10]])

    def test_createTreeRec2(self):
        tree = createTreeFromSexp([22, [33, 44]])
        self.assertEqual(tree.toPySexp(), [22, [33, 44]])


    def test_toPySexp(self):
        node1 = TNode(5)
        self.assertEqual(node1.toPySexp(), [5])

    def test_toPySexp2(self):
        node1 = TNode(5)
        node2 = TNode(6, None, node1)
        node1.next = node2
        self.assertEqual(node1.toPySexp(), [5, 6])

    def test_toPySexp3(self):
        node1 = TNode(5)
        node2 = TNode(6)
        node3 = TNode(7)
        node1.next = node2
        node2.next = node3
        self.assertEqual(node1.toPySexp(), [5, 6, 7])

    def test_toPySexpNest(self):
        node1 = TNode(5)
        node2 = TNode()
        node2a = TNode(4)
        node2b = TNode(7)
        node3 = TNode(55)

        node1.next = node2
        node2.child = node2a
        node2.next = node3

        node2a.next = node2b

        self.assertEqual(node1.toPySexp(), [5, [4, 7], 55])

    def test_copyTNode(self):
        tree = createTreeFromSexp([4])
        newTree = copyTNode(tree)
        self.assertEqual(newTree.toPySexp(), [4])

    def test_copyTNode2(self):
        tree = createTreeFromSexp([[4, 5]])
        newTree = copyTNode(tree)
        self.assertEqual(newTree.toPySexp(), [[4, 5]])

    def test_copyTNode3(self):
        tree = createTreeFromSexp([4, 5, 6])
        newTree = copyTNode(tree)
        self.assertEqual(newTree.toPySexp(), [4, 5, 6])

    def test_copyTNodeRec1(self):
        tree = createTreeFromSexp([4, [10]])
        newTree = copyTNode(tree)
        self.assertEqual(newTree.toPySexp(), [4, [10]])

    def test_copyTNodeRec2(self):
        tree = createTreeFromSexp([4, [10, 20]])
        newTree = copyTNode(tree)
        self.assertEqual(newTree.toPySexp(), [4, [10, 20]])

    def test_copyTNodeRec2(self):
        tree = createTreeFromSexp([[10, 20], 4])
        newTree = copyTNode(tree)
        self.assertEqual(newTree.toPySexp(), [[10, 20], 4])

    def test_copyTNodeRec3(self):
        tree = createTreeFromSexp([4, [10], [20, [101]]])
        newTree = copyTNode(tree)
        self.assertEqual(newTree.toPySexp(), [4, [10], [20, [101]]])

    def test_copyTNodeRec4(self):
        tree = createTreeFromSexp([[4], [10, 15], [20, [101, 202]]])
        newTree = copyTNode(tree)
        self.assertEqual(newTree.toPySexp(), [[4], [10, 15], [20, [101, 202]]])

    #def test_activeToPySexp(self):
    #    self.fail()


    def test_isDataNode(self):
        node = TNode(22)
        self.assertFalse(node.isSubNode())

    def test_isDataNode2(self):
        node = TNode(22)
        secondNode = TNode(node, node)
        self.assertTrue(secondNode.isSubNode())


    def test_insertBefore(self):
        node1 = TNode(5)
        node1.insertBefore(10)

        self.assertEquals(node1.previous.toPySexp(), [10, 5])

    def test_insertBefore2(self):
        node1 = TNode(5)
        node1.insertBefore(10)
        node1.insertBefore(7)
        first = node1.previous.previous

        self.assertEquals(first.toPySexp(), [10, 7, 5])


    def test_insertAfter(self):
        node1 = TNode(5)
        node1.insertAfter(10)

        self.assertEquals(node1.toPySexp(), [5, 10])

    def test_insertAfter2(self):
        node1 = TNode(5)
        node1.insertAfter(10)
        node1.insertAfter(15)

        self.assertEquals(node1.toPySexp(), [5, 15, 10])

    def test_removeSelf(self):
        node1 = TNode(5)
        node1.insertAfter(10)

        node1.next.removeSelf()

        self.assertEqual(node1.toPySexp(), [5])

    def test_removeSelf2(self):
        node1 = TNode(5)
        node1.insertAfter(10)
        node1.insertAfter(15)

        node1.next.removeSelf()

        self.assertEqual(node1.toPySexp(), [5, 10])

#    def test_nestData(self):
#        self.fail()