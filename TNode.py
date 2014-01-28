__author__ = 'chephren'
import reader

def isList(lst):
    return isinstance(lst, list)

def createTreeFromSexp(sexp):
    startNode = None
    lastNode = None

    if sexp:
        if isList(sexp):
            for i in sexp:
                if startNode:
                    lastNode.insertAfter(createTreeFromSexp(i))
                    lastNode = lastNode.next
                else:
                    startNode = TNode(createTreeFromSexp(i))
                    lastNode = startNode
        else:  #atom
            return sexp

    return startNode

class TNode(object):
    def __init__(self, val=None, parent=None, prev=None, next=None):
        self.next = next
        self.previous = prev
        self.parent = parent
        self.setChild(val)

    def __iter__(self):
        return TNodeIterator(self)

    def toPySexp(self):
        ret = list()
        for i in self:
            if i.isSubNode():
                ret.append(i.child.toPySexp())
            else:
                ret.append(reader.atom(i.child))

        return ret

    def activeToPySexp(self):
        if self.isSubNode():
            return self.child.toPySexp()
        else:
            return reader.atom(self.child)

    def isSubNode(self):
        if isinstance(self.child, TNode):
            return True
        return False

    def insertBefore(self, element):
        newNode = TNode(element, self.parent, self.previous, self)
        if self.previous:
            self.previous.next = newNode
        elif self.parent:
            self.parent.child = newNode
        self.previous = newNode

    def insertAfter(self, element):
        newNode = TNode(element, self.parent, prev=self, next=self.next)
        if self.next:
            self.next.previous = newNode
        self.next = newNode

    def setChild(self, newChild):
        self.child = newChild

        if isTNode(newChild):
            for i in self.child:
                i.parent = self

    def insertNodeAfter(self, node):
        if self.next:
            self.next.previous = node
            node.next = self.next
        self.next = node
        node.previous = self
        node.parent = self.parent


    # Removes the current element and returns the new active node.
    # The new active node will be the next in sequence if one exists. Otherwise it will be the previous
    # and failing that it will return the parent.
    def removeSelf(self):
        if not self.previous:
            self.parent.child = self.next
        else:
            self.previous.next = self.next

        if self.next:
            self.next.previous = self.previous
            return self.next

        if self.previous:
            return self.previous

        return self.parent

    # wrap the current data in brackets.
    def nestChild(self):
        self.setChild(TNode(self.child, self))



def isTNode(obj):
    if isinstance(obj, TNode):
        return True
    return False


class TNodeIterator(object):
    def __init__(self, start):
        self.cur = TNode()
        self.cur.next = start

    def __iter__(self):
        return self

    def next(self):
        if self.cur.next:
            self.cur = self.cur.next
            return self.cur
        else:
            raise StopIteration
