__author__ = 'chephren'
import reader
import copy




class FuncObject(object):
    def update(self, prop, val):
        newSelf = copy.copy(self)
        setattr(newSelf, prop, val)
        return newSelf

    def updateList(self, *propValueList):
        newSelf = copy.copy(self)
        #changes = []
        for (prop, val) in propValueList:
            if not hasattr(newSelf, prop):
                raise AttributeError
            #old = getattr(newSelf, prop)
            setattr(newSelf, prop, val)
        return newSelf


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

def opAtNVSAdd(node, nvs, op):
    def opAtAdd2(node, nvs, curDest):
        if node.isSubNode() and node.child.child == curDest:

            if nvs:
                newNvs = nvs[1:]
                newDest = nvs[0]
                #return cons(opAtAdd2(node.child, newAdd, newDest), node.next)
                return TNode(opAtAdd2(node.child, newNvs, newDest), node.nodeID, node.next)
            else:
                return TNode(node.child.child, node.nodeID, op(node.child.next))

        else:
            return join(node, opAtAdd2(node.next, nvs, curDest))

    newNvs = nvs[1:]
    newDest = nvs[0]
    return opAtAdd2(node, newNvs, newDest)

def opAtAdd(node, add, op):
    def opAtAdd2(node, add, curDest):
        if curDest != 0:
            return join(node, opAtAdd2(node.next, add, curDest - 1))
        elif add:
            newAdd = add[1:]
            newDest = add[0]
            #return cons(opAtAdd2(node.child, newAdd, newDest), node.next)
            return TNode(opAtAdd2(node.child, newAdd, newDest), node.nodeID, node.next)
        else:
            return op(node)

    newAdd = add[1:]
    newDest = add[0]
    return opAtAdd2(node, newAdd, newDest)

def insertAdd(node, add, value):
    return opAtAdd(node, add, lambda addNode: cons(value, addNode))

def appendAdd(node, add, value):
    return opAtAdd(node, add, lambda addNode: join(addNode, cons(value, addNode.next)))

def deleteAdd(node, add):
    return opAtAdd(node, add, lambda addNode: addNode.next)

def replaceAdd(node, add, value):
    #return opAtAdd(node, add, lambda addNode: cons(value, addNode.next))
    return opAtAdd(node, add, lambda addNode: addNode.update('child', addNode.parseValue(value)))

def copyToAdd(node, add):
    return opAtAdd(node, add, lambda addNode: TNode(addNode.child))

def nestAdd(node, add):
    return opAtAdd(node, add, lambda addNode: cons(TNode(addNode.child), addNode.next))

def quoteAdd(node, add, value):
    return opAtAdd(node, add, lambda addNode: addNode.update('evaled', value))


def append(node1, node2):
    if not node1:
        return node2
    else:
        cons(node1.child, append(node1.next, node2))


def cons(value, cdr):
    car = TNode(value)
    car.next = cdr
    return car

def join(node1, node2):
    car = copy.copy(node1)
    #car = TNode(node1.child, node1.nodeID)
    car.next = node2
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


class Buffer(FuncObject):
    def __init__(self, root, viewAdd=[0], cursorAdd=[0]):
        self.root = root
        self.view, self.viewAdd = self.root.gotoNearestAddress(viewAdd)
        self.cursor, self.cursorAdd = self.view.gotoNearestAddress(cursorAdd)

    def onSubNode(self):
        return self.cursor.isSubNode()

    def cursorToPySexp(self):
        return self.cursor.activeToPySexp()

    def cursorToFirst(self):
        return self.updateList(
            ('cursor', self.view.child),
            ('cursorAdd', [0, 0])     # actually want first in thing
        )

    def syncToNewRoot(self, newRoot):
#        return Buffer(newRoot, self.viewAdd, self.cursorAdd)
        newView, newViewAdd = self.root.gotoAddressOnNewRoot(self.viewAdd, newRoot)
        newCursor, newCursorAdd = self.view.gotoAddressOnNewRoot(self.cursorAdd, newView)
        return Buffer(newRoot, newViewAdd, newCursorAdd)

    def syncViewAddToNewRoot(self, newRoot):
        add = list(self.viewAdd)
        oldNodeIter = self.root
        newNodeIter = newRoot
        newAdd = []
        while add:
            curDest = add.pop(0)
            newAdd.append(0)
            while curDest != 0:
                if newNodeIter == oldNodeIter:
                    if newNodeIter.next:
                        oldNodeIter = oldNodeIter.next
                        newNodeIter = newNodeIter.next
                        curDest -= 1
                        newAdd[-1] += 1
                    else: return (newNodeIter, newAdd)  # the old node must have been deleted from the new root
                elif newNodeIter == oldNodeIter.next:  # the old node was deleted
                    oldNodeIter = oldNodeIter.next
                elif newNodeIter.next == oldNodeIter: # a node was inserted into the old root
                    newNodeIter = newNodeIter.next
                    newAdd[-1] += 1

                else: return (newNodeIter, newAdd)  # something more complicated happened.

            # check if still have sublevels to follow and go to them if possible
            if add:
                if newNodeIter.isSubNode():
                    newNodeIter = newNodeIter.child
                    oldNodeIter = oldNodeIter.child
                else: return (newNodeIter, newAdd)

        return (newNodeIter, newAdd)

    def rootToCursorAdd(self):
        return self.viewAdd + self.cursorAdd[1:]

    def opAtCursor(self, op, value=None):
        if value:
            newView = op(self.view, self.cursorAdd, value)
        else:
            newView = op(self.view, self.cursorAdd)
        newImage = replaceAdd(self.root, self.viewAdd, newView.child)
        return Buffer(newImage, self.viewAdd, self.cursorAdd)

#    def appendAtCursor(self, value):
#        return self.opAtCursor(appendAdd, value)

    def appendAtCursor(self, value):
        newView = appendAdd(self.view, self.cursorAdd, value)
        newImage = replaceAdd(self.root, self.viewAdd, newView.child)
        newBuffer = Buffer(newImage, self.viewAdd, self.cursorAdd)
        return newBuffer

    def insertAtCursor(self, value):
        newView = insertAdd(self.view, self.cursorAdd, value)
        newImage = replaceAdd(self.root, self.viewAdd, newView.child)
        newCursorAdd = list(self.cursorAdd)
        newCursorAdd[-1] += 1
        return Buffer(newImage, self.viewAdd, newCursorAdd)

    def deleteAtCursor(self):
        newBuff = self
        if self.cursor == self.view:
            newBuff = self.viewUp()
        newView = deleteAdd(newBuff.view, newBuff.cursorAdd)
        newImage = replaceAdd(newBuff.root, newBuff.viewAdd, newView.child)
        return Buffer(newImage, newBuff.viewAdd, newBuff.cursorAdd)

    def replaceAtCursor(self, value):
        newView = replaceAdd(self.view, self.cursorAdd, value)
        newImage = replaceAdd(self.root, self.viewAdd, newView.child)
        return Buffer(newImage, self.viewAdd, self.cursorAdd)

    def nestCursor(self):
        newView = nestAdd(self.view, self.cursorAdd)
        newImage = replaceAdd(self.root, self.viewAdd, newView.child)
        return Buffer(newImage, self.viewAdd, self.cursorAdd)

    def quoteAtCursor(self):
        newView = quoteAdd(self.view, self.cursorAdd, not(self.cursor.evaled))
        newImage = replaceAdd(self.root, self.viewAdd, newView.child)
        return Buffer(newImage, self.viewAdd, self.cursorAdd)

    def toggleStringAtCursor(self):
        if isinstance(self.cursor.child, reader.Symbol):
            return self.replaceAtCursor(str(self.cursor.child))
        else: return self

    def viewUp(self):
        # from curUp
        if len(self.viewAdd) > 1:
            newViewAddress = self.viewAdd[0:-1]
        else:
            raise ValueError

        # new cursor address will be prefixed by the last step in the address to the old view
        newCursorAddress = [0] + self.viewAdd[-1:] + self.cursorAdd[1:]
        return Buffer(self.root, newViewAddress, newCursorAddress)

    def viewToCursor(self):
        newViewAddress = self.viewAdd + self.cursorAdd[1:]
        return Buffer(self.root, newViewAddress)

    def viewToRoot(self):
        return Buffer(self.root, [0], [0])

    def viewNext(self):
        if self.view.next:
            newAddress = list(self.viewAdd)
            newAddress[-1] += 1
            return Buffer(self.root, newAddress)
        else:
            raise ValueError

    def viewPrev(self):
        if self.viewAdd[-1] > 0:
            newAddress = list(self.viewAdd)
            newAddress[-1] -= 1
            return Buffer(self.root, newAddress)
        else:
            raise ValueError

    def curNext(self):
        if self.cursor.next:
            newAddress = list(self.cursorAdd)
            newAddress[-1] += 1
            return self.updateList(('cursorAdd', newAddress), ('cursor', self.cursor.next))
        else:
            raise ValueError

    def curLast(self):
        cur = self
        while cur.cursor.next:
            cur = cur.curNext()

        return cur

    def curNextUpAlong(self):
        cur = self

        if cur.cursor == cur.view:
            return self

        while not cur.cursor.next:
            cur = cur.curUp()
            if cur.cursor == cur.view:
                return self

        return cur.curNext()

    def curPrev(self):
        if self.cursorAdd[-1] > 0:
            newAddress = list(self.cursorAdd)
            newAddress[-1] -= 1
            return Buffer(self.root, self.viewAdd, newAddress)
        else:
            raise ValueError

    def curPrevUpAlong(self):
        cur = self

        while not cur.cursorAdd[-1] > 0:
            cur = cur.curUp()

        return cur.curPrev()

    def curUp(self):
        if len(self.cursorAdd) > 1:
            newAddress = self.cursorAdd[0:-1]
            return Buffer(self.root, self.viewAdd, newAddress)
        else:
            raise ValueError

    def curChild(self):
        if self.cursor.isSubNode():
            newAddress = list(self.cursorAdd)
            newAddress.append(0)
            return self.updateList(('cursorAdd', newAddress), ('cursor', self.cursor.child))
        else:
            return self.cursor.child  # the value


class TNode(FuncObject):
    __nodes__ = 0
    def __init__(self, val=None, id=None, next=None):
        self.next = next
        self.child = self.parseValue(val)

        self.evaled = True
        self.displayValue = False

        if not id:
            self.nodeID = TNode.__nodes__
            TNode.__nodes__ += 1
        else:
            self.nodeID = id

    def __iter__(self):
        return TNodeIterator(self)

    def __str__(self):
        if self.isSubNode():
            return "<TNode ...>"
        else:
            return "<TNode " + str(self.child) + ">"

    def __hash__(self):
        return hash(self.nodeID)

    def __eq__(self, other):
        if isinstance(other, TNode):
            return self.nodeID == other.nodeID
        else: return False

    def parseValue(self, val):
        if isList(val):
            return createTreeFromSexp(val)
        else:
            return val

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
        elif self.child is None:
            return []
        else:
            #return reader.atom(self.child)
            return self.child

    def isSubNode(self):
        if isinstance(self.child, TNode):
            return True
        return False

    def getNodeAtNVS(self, nvs):
        add = list(nvs)
        iter = self
        while add:
            curDest = add.pop(0)
            while curDest != iter.child.child:
                if iter.next:
                    iter = iter.next
                else: return None

            # check if still have sublevels to follow and go to them if possible
            if add:
                if iter.isSubNode():
                    iter = iter.child.next
                else: return None

        return iter.child.next

    def gotoAddress(self, address):
        add = list(address)
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

    def gotoNearestAddress(self, address):
        add = list(address)
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
                else: return (iter, newAdd)

            # check if still have sublevels to follow and go to them if possible
            if add:
                if iter.isSubNode():
                    iter = iter.child
                else: return (iter, newAdd)

        return (iter, newAdd)

    def gotoAddressOnNewRoot(self, address, newRoot):
        add = list(address)
        oldNodeIter = self
        newNodeIter = newRoot
        newAdd = []
        while add:
            curDest = add.pop(0)
            newAdd.append(0)
            while curDest != 0:
                if newNodeIter == oldNodeIter:
                    if newNodeIter.next:
                        oldNodeIter = oldNodeIter.next
                        newNodeIter = newNodeIter.next
                        curDest -= 1
                        newAdd[-1] += 1
                    else: return (newNodeIter, newAdd)  # the old node must have been deleted from the new root
                elif newNodeIter == oldNodeIter.next:  # the old node was deleted
                    oldNodeIter = oldNodeIter.next
                    curDest -= 1
                elif newNodeIter.next == oldNodeIter: # a node was inserted into the old root
                    newNodeIter = newNodeIter.next
                    newAdd[-1] += 1

                else: return (newNodeIter, newAdd)  # something more complicated happened.

            # check if still have sublevels to follow and go to them if possible
            if add:
                if newNodeIter.isSubNode():
                    newNodeIter = newNodeIter.child
                    oldNodeIter = oldNodeIter.child
                else: return (newNodeIter, newAdd)

        return (newNodeIter, newAdd)


#    def getNextUpAlong(self, direction, root):
#        iter = self
#
#        if iter == root:
#            raise ValueError
#
#        while not getattr(iter, direction):
#            if iter.parent != root:
#                iter = iter.parent
#            else: raise ValueError
#
#        return getattr(iter, direction)
#
#    def getNearestAlong(self, direction, root):
#        iter = self
#        levels = 0
#        switchedLevels = False
#
#        if iter == root:
#            raise ValueError
#
#        while not getattr(iter, direction):
#            if iter.parent != root:
#                iter = iter.parent
#                levels += 1
#                switchedLevels = True
#            else: raise ValueError
#
#        iter = getattr(iter, direction)
#
#        #now descend
#        while levels != 0 and isinstance(iter.child, TNode):
#            iter = iter.child
#            levels -= 1
#
#        if direction == 'previous' and switchedLevels:
#            while iter.next:
#                iter = iter.next
#
#        return iter

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

#    def insertBefore(self, element):
#        newNode = self.__class__(element, self.parent, self.previous, self)
#        if self.previous:
#            self.previous.next = newNode
#        elif self.parent:
#            self.parent.child = newNode
#        self.previous = newNode

    def insertAfter(self, element):
        newNode = self.__class__(element, next=self.next)
        if self.next:
            self.next.previous = newNode
        self.next = newNode

    def setChild(self, newChild):
        self.child = newChild

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
