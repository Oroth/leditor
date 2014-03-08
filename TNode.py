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

#class Cursor(object):
#    def __init__(self, root, startAddress=[0], start=None):
#        self.root = root
#        #print "startAddress: ", startAddress
#        self.address = list(startAddress)
#        #self.address = list([0])
#        if start:
#            self.active = start
#        else:
#            self.active = root.gotoAddress(startAddress)
#
#    def get(self):
#        return self.active
#
#    def refreshToNearest(self):
#        return self.root.gotoNearestAddress(self.address)
#
#    def onSubNode(self):
#        return self.active.isSubNode()
#
#    def childToPySexp(self):
#        return self.active.activeToPySexp()
#
#    def insertAfter(self, value):
#        newFrame = copyTNode(self.root)
#        c = Cursor(newFrame, self.address)
#        c.active.insertAfter('')
#
#    def next(self):
#        if self.active.next:
#            newAddress = list(self.address)
#            newAddress[-1] += 1
#            return Cursor(self.root, newAddress, self.active.next)
#        else:
#            raise ValueError
#
#    def prev(self):
#        if self.address[-1] > 0:
#            newAddress = list(self.address)
#            newAddress[-1] -= 1
#            return Cursor(self.root, newAddress)
#        else:
#            raise ValueError
#
#    def up(self):
#        if len(self.address) > 1:
#            newAddress = self.address[0:-1]
#            return Cursor(self.root, newAddress)
#        else:
#            raise ValueError
#
#    def child(self):
#        if self.active.isSubNode():
#            newAddress = list(self.address)
#            newAddress.append(0)
#            return Cursor(self.root, newAddress, self.active.child)
#        else:
#            return self.active.child  # the value


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
        return Buffer(newRoot, self.viewAdd, self.cursorAdd)

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

    def curNext(self):
        if self.cursor.next:
            newAddress = list(self.cursorAdd)
            newAddress[-1] += 1
            return self.updateList(('cursorAdd', newAddress), ('cursor', self.cursor.next))
        else:
            raise ValueError

    def curNextUpAlong(self):
        cur = self
        while not cur.cursor.next:
            cur = cur.curUp()

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
        if self.isSubNode():
            return "<TNode ...>"
        else:
            return "<TNode " + str(self.child) + ">"

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



#    def getAddress(self):
#        ret = []
#        iter = self
#
#        while iter.parent:
#            curLevelLoc = 0
#            while iter.previous:
#                curLevelLoc += 1
#                iter = iter.previous
#
#            ret.insert(0, curLevelLoc)
#            iter = iter.parent
#
#        ret.insert(0, 0)  #because of root node...
#        return ret
#
#    def getAddressFrom(self, start):
#        ret = []
#        iter = self
#
#        while iter.parent and iter != start:
#            curLevelLoc = 0
#            while iter.previous and iter != start:
#                curLevelLoc += 1
#                iter = iter.previous
#
#            ret.insert(0, curLevelLoc)
#            iter = iter.parent
#
#        #ret.insert(0, 0)  #because of root node...
#        return ret

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
