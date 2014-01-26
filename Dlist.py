__author__ = 'chephren'

import reader

def isList(val):
    return isinstance(val, list)

class DNode(object):
    def __init__(self):
        self.next = None
        self.previous = None
        self.element = None

    def insertBefore(self, element):
        tmpnew = DNode()
        tmpnew.element = element
        tmpnew.previous = self.previous
        tmpnew.next = self
        if self.previous:
            self.previous.next = tmpnew
        self.previous = tmpnew

    def insertAfter(self, element):
        tmpnew = DNode()
        tmpnew.element = element
        tmpnew.previous = self
        tmpnew.next = self.next
        if self.next:
            self.next.previous = tmpnew
        self.next = tmpnew

    def last(self):
        if self.next:
            self.next.last()
        else:
            return self

    def append(self, element):
        self.last().insertAfter(element)



######################################### Tree Node ###################################

def createTreeFromList(list):
    startNode = None
    lastNode = None
    rootNode = TNode()

    if list:
        for i in list:
            if startNode:
                if isList(i):
                    lastNode.insertNodeAfter(createTreeFromList(i))
                else:
                    lastNode.insertAfter(i)
                lastNode = lastNode.next
            else:
                if isList(i):
                    startNode = createTreeFromList(i)
                else:
                    startNode = TNode(i)
                startNode.parent = rootNode
                rootNode.child = startNode
                lastNode = startNode

    return rootNode

def createTreeFromSexp(sexp):
    startNode = None
    lastNode = None
    rootNode = TNode()

    if sexp:
        if isList(sexp):
            for i in sexp:
                if startNode:
                    if isList(i):
                        lastNode.insertNodeAfter(createTreeFromList(i))
                    else:
                        lastNode.insertAfter(i)
                    lastNode = lastNode.next
                else:
                    if isList(i):
                        startNode = createTreeFromList(i)
                    else:
                        startNode = TNode(i)
                    startNode.parent = rootNode
                    rootNode.child = startNode
                    lastNode = startNode
        else:  #atom
            startNode = TNode(sexp)
            return startNode
            #startNode.parent = rootNode
            #rootNode.child = startNode

    return rootNode


class TNode(object):
    def __init__(self, val=None, parent=None, prev=None, next=None):
        self.next = next
        self.previous = prev
        self.parent = parent
        self.child = None
        self.element = val

    # generate a python list from the current position
    def toSexpr(self):
        if self.child:
            current = self.child.toSexpr()
        else:
            current = reader.atom(self.element)

        if self.next:
            ret = list()
            ret.append(current)

            iter = self.next
            while iter:
                if iter.child:
                    ret.append(iter.child.toSexpr())
                else:
                    ret.append(reader.atom(iter.element))

                iter = iter.next
        else:
            ret = current

        return ret

    def activeToSexpr(self):
        if self.child:
            current = self.child.toSexpr()
        else:
            current = reader.atom(self.element)

        return current



    def insertBefore(self, element):
        tmpnew = TNode(element, self.parent, self.previous, self)
        if self.previous:
            self.previous.next = tmpnew
        else:
            if self.parent:
                self.parent.child = tmpnew
        self.previous = tmpnew

    def insertAfter(self, element):
        tmpnew = TNode(element, self.parent, prev=self, next=self.next)
        if self.next:
            self.next.previous = tmpnew
        self.next = tmpnew

    def insertNodeAfter(self, node):
        if self.next:
            self.next.previous = node
            node.next = self.next
        self.next = node
        node.previous = self
        node.parent = self.parent

    def removeSelf(self):
        if self.parent:
            if self.parent.child == self:
                self.parent.child = self.next
        if self.previous:
            self.previous.next = self.next
        if self.next:
            self.next.previous = self.previous
            return self.next

        if self.previous:
            return self.previous

        return self.parent



    def makeElementChild(self):
        if self.child:
            tmpnew = TNode()
            tmpnew.child = self.child

            iter = tmpnew.child
            while iter:
                iter.parent = tmpnew
                iter = iter.next

            tmpnew.parent = self
        else:
            tmpnew = TNode(self.element, self)
            self.element = None
        self.child = tmpnew

    def insertChildAfter(self, element):
        self.insertAfter(element)
        self.next.makeElementChild()

    def addChildNode(self, node):
        self.child = node
        node.parent = self

    def last(self):
        if self.next:
            return self.next.last()
        else:
            return self

    def append(self, element):
        final = self.last()
        final.insertAfter(element)


    #append
    #last
    #length (?)

    def forward(self):
        if self.next:
            return self.next

    def back(self):
        if self.previous: return self.previous
