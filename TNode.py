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

def copyTNode(node):
    startNode = None
    lastNode = None

    if node:
        if isinstance(node, TNode):
            for i in node:
                if startNode:
                    lastNode.insertAfter(copyTNode(i.child))
                    lastNode = lastNode.next
                else:
                    startNode = TNode(copyTNode(i.child))
                    lastNode = startNode
        else:  #atom
            return node

    return startNode

def copyTNodeAsNewTreeClass(node, newTreeClass):
    startNode = None
    lastNode = None

    if node:
        if isinstance(node, TNode):
            for i in node:
                if startNode:
                    lastNode.insertAfter(copyTNodeAsNewTreeClass(i.child, newTreeClass))
                    lastNode = lastNode.next
                else:
                    startNode = newTreeClass(copyTNodeAsNewTreeClass(i.child, newTreeClass))
                    lastNode = startNode

                lastNode.evaled = i.evaled
        else:  #atom
            return node

    return startNode

class TNode(object):
    def __init__(self, val=None, parent=None, prev=None, next=None):
        self.next = next
        self.previous = prev
        self.parent = parent
        self.setChild(val)

        self.evaled = True
        self.displayValue = False

    def __iter__(self):
        return TNodeIterator(self)

    def toPySexp(self):
        ret = list()
        for i in self:
            if i.isSubNode():
                ret.append(i.child.toPySexp())
            else: ret.append(i.child)

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



    def getAddress(self):
        ret = []
        iter = self

        while iter.parent:
            curLevelLoc = 0
            while iter.previous:
                curLevelLoc += 1
                iter = iter.previous

            ret.insert(0, curLevelLoc)
            iter = iter.parent

        ret.insert(0, 0)  #because of root node...
        return ret

    def getAddressFrom(self, start):
        ret = []
        iter = self

        while iter.parent and iter != start:
            curLevelLoc = 0
            while iter.previous and iter != start:
                curLevelLoc += 1
                iter = iter.previous

            ret.insert(0, curLevelLoc)
            iter = iter.parent

        #ret.insert(0, 0)  #because of root node...
        return ret

    def gotoAddress(self, add):

        iter = self
        while add:
            curDest = add.pop(0)
            while curDest != 0:
                if iter.next:
                    iter = iter.next
                    curDest -= 1
                else: return None

            # check if still have sublevels to follow and go to them if possible
            if add:
                if iter.isSubNode():
                    iter = iter.child
                else: return None

        return iter.child

    def gotoNearestAddress(self, add):
        iter = self
        while add:
            curDest = add.pop(0)
            while curDest != 0:
                if iter.next:
                    iter = iter.next
                    curDest -= 1
                else: return iter

            # check if still have sublevels to follow and go to them if possible
            if add:
                if iter.isSubNode():
                    iter = iter.child
                else: return iter

        return iter

    def getNextUpAlong(self, direction, root):
        iter = self

        if iter == root:
            raise ValueError

        while not getattr(iter, direction):
            if iter.parent != root:
                iter = iter.parent
            else: raise ValueError

        return getattr(iter, direction)

    def getNearestAlong(self, direction, root):
        iter = self
        levels = 0
        switchedLevels = False

        if iter == root:
            raise ValueError

        while not getattr(iter, direction):
            if iter.parent != root:
                iter = iter.parent
                levels += 1
                switchedLevels = True
            else: raise ValueError

        iter = getattr(iter, direction)

        #now descend
        while levels != 0 and isinstance(iter.child, TNode):
            iter = iter.child
            levels -= 1

        if direction == 'previous' and switchedLevels:
            while iter.next:
                iter = iter.next

        return iter

    def getAddressOffset(self, offset):

        iter = self
        while offset:
            curDest = offset.pop(0)
            while curDest != 0:
                if iter.next:
                    iter = iter.next
                    curDest -= 1
                else: return None

            # check if still have sublevels to follow and go to them if possible
            if offset:
                if iter.isSubNode():
                    iter = iter.child
                else: return None

        return iter.child

    def insertBefore(self, element):
        newNode = self.__class__(element, self.parent, self.previous, self)
        if self.previous:
            self.previous.next = newNode
        elif self.parent:
            self.parent.child = newNode
        self.previous = newNode

    def insertAfter(self, element):
        newNode = self.__class__(element, self.parent, prev=self, next=self.next)
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
        if self.previous is None:
            if self.next:
                self.parent.child = self.next
            else:
                self.child = None
        else:
            self.previous.next = self.next

        if self.next:
            self.next.previous = self.previous
            return self.next

        if self.previous:
            return self.previous

        return self

    # wrap the current data in brackets.
    def nestChild(self):
        self.setChild(self.__class__(self.child, self))



def isTNode(obj):
    if isinstance(obj, TNode):
        return True
    return False


class TNodeIterator(object):
    def __init__(self, start):
        self.cur = start.__class__()
        self.cur.next = start

    def __iter__(self):
        return self

    def next(self):
        if self.cur.next:
            self.cur = self.cur.next
            return self.cur
        else:
            raise StopIteration
