from unittest import TestCase
from TNode import TNode
from TNode import createTreeFromSexp

__author__ = 'chephren'

class TestTNode(TestCase):

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



    #def test_activeToPySexp(self):
    #    self.fail()


    def test_isDataNode(self):
        node = TNode(22)
        self.assertFalse(node.isChildTNode())

    def test_isDataNode2(self):
        node = TNode(22)
        secondNode = TNode(node, node)
        self.assertTrue(secondNode.isChildTNode())


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

    def test_nestData(self):
        self.fail()