__author__ = 'chephren'
import reader

def isList(lst):
    return isinstance(lst, list)

def transform(obj, property, func):
    newObj = obj.copy()
    newProp = func(getattr(newObj, property))
    setattr(newObj, property, newProp)
    return newObj

def transformList(obj, *propFuncList):
    newObj = obj.copy()
    #(propList, funcList) = zip(*propFuncList)
    for (prop, func) in propFuncList:
        newProp = func(getattr(newObj, prop))
        setattr(newObj, prop, newProp)

    return newObj

def createTreeFromSexp(sexp):
    startNode = None
    lastNode = None

    if sexp is not None:
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

# new. purely functional
# copies only the minimum number
def copyTNodeToInd(node, i):
    if i != 0:
        return cons(node.child, copyTNodeToInd(node.next, i - 1))
    else:
        return TNode(node.child)

def opAtAdd(node, add, op):
    def opAtAdd2(node, add, curDest):
        if curDest != 0:
            return cons(node.child, opAtAdd2(node.next, add, curDest - 1))
        elif add:
            newAdd = add[1:]
            newDest = add[0]
            return cons(opAtAdd2(node.child, newAdd, newDest), node.next)
        else:
            return op(node)

    newAdd = add[1:]
    newDest = add[0]
    return opAtAdd2(node, newAdd, newDest)

def insertAdd(node, add, value):
    return opAtAdd(node, add, lambda addNode: cons(value, addNode))

def appendAdd(node, add, value):
    return opAtAdd(node, add, lambda addNode: cons(addNode.child, cons(value, addNode.next)))

def deleteAdd(node, add):
    return opAtAdd(node, add, lambda addNode: addNode.next)

def replaceAdd(node, add, value):
    return opAtAdd(node, add, lambda addNode: cons(value, addNode.next))

def copyToAdd(node, add):
    return opAtAdd(node, add, lambda addNode: TNode(node.child))

def nestAdd(node, add):
    return opAtAdd(node, add, lambda addNode: cons(addNode, addNode.next))

def append(node1, node2):
    if not node1:
        return node2
    else:
        cons(node1.child, append(node1.next, node2))

#def insertAdd(node, add, value):
#    def insertAdd2(node, add, curDest):
#        if curDest != 0:
#            return cons(node.child, insertAdd2(node.next, add, curDest - 1))
#        elif add:
#            newAdd = add[1:]
#            newDest = add[0]
#            return cons(insertAdd2(node.child, newAdd, newDest), node.next)
#        else:
#            return cons(value, node)
#
#    newAdd = add[1:]
#    newDest = add[0]
#    return insertAdd2(node, newAdd, newDest)

#def deleteAdd(node, add):
#    def deleteAdd2(node, add, curDest):
#        if curDest != 0:
#            return cons(node.child, deleteAdd2(node.next, add, curDest - 1))
#        elif add:
#            newAdd = add[1:]
#            newDest = add[0]
#            return cons(deleteAdd2(node.child, newAdd, newDest), node.next)
#        else:
#            return node.next
#
#    newAdd = add[1:]
#    newDest = add[0]
#    return deleteAdd2(node, newAdd, newDest)
#
#def replaceAdd(node, add, value):
#    def replaceAdd2(node, add, curDest):
#        if curDest != 0:
#            return cons(node.child, replaceAdd2(node.next, add, curDest - 1))
#        elif add:
#            newAdd = add[1:]
#            newDest = add[0]
#            return cons(replaceAdd2(node.child, newAdd, newDest), node.next)
#        else:
#            return cons(value, node.next)
#
#    newAdd = add[1:]
#    newDest = add[0]
#    return replaceAdd2(node, newAdd, newDest)

def cons(value, cdr):
    car = TNode(value)
    car.next = cdr
    return car


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

class Cursor(object):
    def __init__(self, root, startAddress=[0], start=None):
        self.root = root
        #print "startAddress: ", startAddress
        self.address = list(startAddress)
        #self.address = list([0])
        if start:
            self.active = start
        else:
            self.active = root.gotoAddress(startAddress)

    def get(self):
        return self.active

    def refreshToNearest(self):
        return self.root.gotoNearestAddress(self.address)

    def onSubNode(self):
        return self.active.isSubNode()

    def childToPySexp(self):
        return self.active.activeToPySexp()

    def insertAfter(self, value):
        newFrame = copyTNode(self.root)
        c = Cursor(newFrame, self.address)
        c.active.insertAfter('')

    def next(self):
        if self.active.next:
            newAddress = list(self.address)
            newAddress[-1] += 1
            return Cursor(self.root, newAddress, self.active.next)
        else:
            raise ValueError

    def prev(self):
        if self.address[-1] > 0:
            newAddress = list(self.address)
            newAddress[-1] -= 1
            return Cursor(self.root, newAddress)
        else:
            raise ValueError

    def up(self):
        if len(self.address) > 1:
            newAddress = self.address[0:-1]
            return Cursor(self.root, newAddress)
        else:
            raise ValueError

    def child(self):
        if self.active.isSubNode():
            newAddress = list(self.address)
            newAddress.append(0)
            return Cursor(self.root, newAddress, self.active.child)
        else:
            return self.active.child  # the value


class TNode(object):
    def __init__(self, val=None, parent=None, prev=None, next=None):
        self.next = next
        self.previous = prev
        self.parent = parent

        if isList(val):
            self.child = createTreeFromSexp(val)
        else:
            self.child = val

        self.evaled = True
        self.displayValue = False

    def __iter__(self):
        return TNodeIterator(self)

    def __str__(self):
        return "TNode ", str(self.child)

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

        return iter

    def gotoNearestAddress(self, add):
        iter = self
        newAdd = []
        while add:
            curDest = add.pop(0)
            newAdd.append(0)
            while curDest != 0:
                if iter.next:
                    iter = iter.next
                    curDest -= 1
                    newAdd[-1] += 1
                else: return Cursor(self, newAdd, iter)

            # check if still have sublevels to follow and go to them if possible
            if add:
                if iter.isSubNode():
                    iter = iter.child
                else: return Cursor(self, newAdd, iter)

        return Cursor(self, newAdd, iter)

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

#    def slice(self, address):
#
#        startNode = None
#        lastNode = None
#
#        if self:
#            if isinstance(node, TNode):
#                for i in node:
#                    if startNode:
#                        lastNode.insertAfter(copyTNode(i.child))
#                        lastNode = lastNode.next
#                    else:
#                        startNode = TNode(copyTNode(i.child))
#                        lastNode = startNode
#            else:  #atom
#                return node
#
#        return startNode

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

#        if isTNode(newChild):
#            for i in self.child:
#                i.parent = self

#    def insertNodeAfter(self, node):
#        if self.next:
#            self.next.previous = node
#            node.next = self.next
#        self.next = node
#        node.previous = self
#        node.parent = self.parent


    # Removes the current element and returns the new active node.
    # The new active node will be the next in sequence if one exists. Otherwise it will be the previous
    # and failing that it will return the parent.
#    def removeSelf(self):
#        if self.previous is None:
#            if self.next:
#                self.parent.child = self.next
#            else:
#                self.child = None
#        else:
#            self.previous.next = self.next
#
#        if self.next:
#            self.next.previous = self.previous
#            return self.next
#
#        if self.previous:
#            return self.previous
#
#        return self

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
