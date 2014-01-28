__author__ = 'chephren'
import reader

def isList(lst):
    return isinstance(lst, list)

#def createTreeFromSexp(sexp):
#    startNode = None
#    lastNode = None
#    rootNode = TNode()
#
#    if sexp:
#        if isList(sexp):
#            for i in sexp:
#                if startNode:
#                    if isList(i):
#                        lastNode.insertNodeAfter(createTreeFromSexp(i))
#                    else:
#                        lastNode.insertAfter(i)
#                    lastNode = lastNode.next
#                else:
#                    if isList(i):
#                        startNode = createTreeFromSexp(i)
#                    else:
#                        startNode = TNode(i)
#                    startNode.parent = rootNode
#                    rootNode.child = startNode
#                    lastNode = startNode
#        else:  #atom
#            return TNode(sexp)
#            #startNode.parent = rootNode
#            #rootNode.child = startNode
#
#    return rootNode

#def createTreeFromSexp(sexp):
#    startNode = None
#    lastNode = None
#    rootNode = TNode()
#
#    if sexp:
#        if isList(sexp):
#            for i in sexp:
#                if startNode:
#                    lastNode.insertNodeAfter(createTreeFromSexp(i))
#                    lastNode = lastNode.next
#                else:
#                    startNode = createTreeFromSexp(i)
#                    startNode.parent = rootNode
#                    rootNode.data = startNode
#                    lastNode = startNode
#        else:  #atom
#            return TNode(sexp)
#
#    return rootNode

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
        self.data = val

    def __iter__(self):
        return TNodeIterator(self)

    def toPySexp(self):
        ret = list()
        for i in self:
            if i.isDataNode():
                ret.append(i.data.toPySexp())
            else:
                ret.append(reader.atom(i.data))

        return ret

    def activeToPySexp(self):
        if self.isDataNode():
            return self.data.toPySexp()
        else:
            return reader.atom(self.data)

    def isDataNode(self):
        if isinstance(self.data, TNode):
            return True
        return False

    def insertBefore(self, element):
        newNode = TNode(element, self.parent, self.previous, self)
        if self.previous:
            self.previous.next = newNode
        elif self.parent:
                self.parent.data = newNode
        self.previous = newNode

    def insertAfter(self, element):
        newNode = TNode(element, self.parent, prev=self, next=self.next)
        if self.next:
            self.next.previous = newNode
        self.next = newNode

    def setChild(self, newChild):
        self.data = newChild

        if isTNode(newChild):
            for i in self.data:
                iter.parent = self.data

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
    def nestData(self):
        self.data = TNode(self.data, self)

        #iter = self.data
        #while iter:
            #iter.parent = self.data
            #iter = iter.next

        for i in self.data:
            iter.parent = self.data


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
