__author__ = 'chephren'
import copy
import funobj as fo

# Terminology
# Atom - Something that is either a symbol, a string, a number (currently)
# Obj - Something that can be any python object, but not a TNode or List

# PyList - A normal python list of Objs
# PyExp - A normal python list of Objs, which may also include other PyLists
# PySexp - A python list of atoms and other PySexps

# TNode - Any generic TNode
# TNodeAtom
# TNodeObj
# TNodeList
# TNodeTree
# TNodeTreeRoot
# TNodeExp - Any generic TNode
# TNodeWinList
# TNodeWinListRoot
# TNodeSexp

# TNodeNumberedExp
# TNodeIDExpPair

# Buffer
# BufferSexp


def isPyList(lst):
    return isinstance(lst, list)

def cons(value, cdr):
    car = TNode(value)
    car.next = cdr
    return car

def numberedCons(value, cdr):
    car = TNode(value[1], value[0])
    car.next = cdr
    return car

def join(node1, node2):
    car = copy.copy(node1)
    car.next = node2
    return car

def joinList(lst, node):
    newLst = copy.deepcopy(lst)
    curLast = newLst
    while curLast.next:
        curLast = curLast.next

    curLast.next = node
    return newLst

def append(first, sec):
    ret = TNode(sec)
    first.next = ret
    return ret

# ========================================== Testing =======================================================
# differences to paramterise:

def transformPyLst(func, acc, lst):
    start, cur = acc
    for i in lst:
        cur = func(cur, i)
    return start

def transformPyExp(func, acc, exp):
    start, cur = acc
    for i in exp:
        if isPyList(i):
            transformPyExp(func,i[0] , i[1:])
        cur = func(cur, i)
    return start


def tnodeIndex(lst, ind):
    curNode = lst
    retInd = 0
    while curNode.next and ind > 0:
        curNode = curNode.next
        ind = ind - 1
        retInd = retInd + 1
    return curNode, retInd

def tnodeMatch(lst, toMatch, defaultInd):
    ind = 0
    defaultRet = lst
    for i in lst:
        if ind == defaultInd:
            defaultRet = i
        if i == toMatch:
            return i, ind
        ind = ind + 1

    return defaultRet, defaultInd

def tnodeAddress(exp, add, acc=[]):
    cur, curPos = tnodeIndex(exp, add[0])
    accInd = list(acc)
    accInd.append(curPos)
    if add[1:] and cur.isSubNode():
        return tnodeAddress(cur.child, add[1:], accInd)
    else:
        return cur, accInd

def tnodeSyncAddress(newexp, oldexp, oldadd, acc=[]):
    oldNode, oldPos = tnodeIndex(oldexp, oldadd[0])
    curNode, curPos = tnodeMatch(newexp, oldNode, oldadd[0])
    accInd = list(acc)
    accInd.append(curPos)
    if oldadd[1:] and curNode.isSubNode():
        return tnodeSyncAddress(curNode.child, oldNode.child, oldadd[1:], accInd)
    else:
        return curNode, accInd

def createTNodeExpFromPyExp3(pyexp):
    return transformPyExp(append, pyexp) if isPyList(pyexp) else pyexp


# ======================================================================================================

def createTNodeExpFromPyExp(pyexp):
    startNode = None
    lastNode = None

    if pyexp is not None:
        if isPyList(pyexp):
            for i in pyexp:
                if startNode:
                    newNode = TNode(createTNodeExpFromPyExp(i))
                    lastNode.next = newNode
                    lastNode = lastNode.next
                else:
                    startNode = TNode(createTNodeExpFromPyExp(i))
                    lastNode = startNode
        else:
            return pyexp

    return startNode

# Should be an integer-pyObj Pair
def tnodeNumberedExpContainsAtom(pynumexp):
    if len(pynumexp) == 2 and not isPyList(pynumexp[0]) and not isPyList(pynumexp[1]):
        return True
    else:
        return False

# like createTreeFromSexp, but picks up the nodeID
def createTNodeExpFromPyNumberedExp(pyexp):
    if tnodeNumberedExpContainsAtom(pyexp):
        return TNode(pyexp[1], pyexp[0])

    else:  # sexp = (id (sexp|atom ...))
        nodeID, pysubexp = pyexp[0], pyexp[1]

        startNode = None
        lastNode = None
        for i in pysubexp:
            if startNode:
                node = createTNodeExpFromPyNumberedExp(i)
                lastNode.next = node
                lastNode = lastNode.next
            else:
                startNode = createTNodeExpFromPyNumberedExp(i)
                lastNode = startNode

        return TNode(startNode, nodeID)



def opAtNVSAdd(node, nvs, op):
    def opAtAdd2(node, nvs, curDest):
        if node.isSubNode() and node.child.child == curDest:

            if nvs:
                newNvs = nvs[1:]
                newDest = nvs[0]
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
    return opAtAdd(node, add, lambda addNode: TNode(value, addNode.nodeID, addNode.next))

def copyToAdd(node, add):
    return opAtAdd(node, add, lambda addNode: TNode(addNode.child))

def nestAdd(node, add):
    return opAtAdd(node, add, lambda addNode: cons(TNode(addNode.child), addNode.next))

def denestAdd(node, add):
    return opAtAdd(node, add, lambda addNode: joinList(addNode.child, addNode.next))

def quoteAdd(node, add, value):
    return opAtAdd(node, add, lambda addNode: addNode.update('evaled', value))


class TNode(fo.FuncObject):
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
        if isPyList(val):
            return createTNodeExpFromPyExp(val)
        else:
            return val

    def toPyNumberedExp(self):
        ret = list()
        for i in self:
            newNode = [i.nodeID]
            if i.isSubNode():
                newNode.append(i.child.toPyNumberedExp())
            else: newNode.append(i.child)
            ret.append(newNode)

        return ret

    def toPyExp(self):
        ret = list()
        for i in self:
            if i.isSubNode():
                ret.append(i.child.toPyExp())
            else: ret.append(i.child)

        return ret

    def childToPyExp(self):
        if self.isSubNode():
            return self.child.toPyExp()
        elif self.child is None:
            return []
        else:
            return self.child

    def isSubNode(self):
        if isinstance(self.child, TNode):
            return True
        return False

    def getValueAtNVS(self, nvs):
        value, add = self.gotoNodeAtNVS(nvs)
        return value.child.next

    def gotoNodeAtNVS(self, nvs):
        curNvs = list(nvs)
        curAdd = [0]
        iter = self
        while curNvs:
            curDest = curNvs.pop(0)
            while curDest != iter.child.child:
                if iter.next:
                    iter = iter.next
                    curAdd[-1] += 1
                else: return None

            # check if still have sublevels to follow and go to them if possible
            if curNvs:
                if iter.isSubNode():
                    iter = iter.child.next
                    curAdd.append(1)
                else: return None

        return iter, curAdd


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


# Given a newExp try to find the closest thing to our address on the oldExp
# if stuff has been inserted before the position we need to look ahead to see if we can find our own spot
# if the node or one of the parents of the node we are on has been deleted then we need to get the oldest
# surviving parent
# currently the logic assumes that no more than one node has been inserted/deleted between oldExp and newExp
def getAddressOnNewExp(oldAddress, oldExp, newExp):
    add = list(oldAddress)
    oldNodeIter = oldExp
    newNodeIter = newExp
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
                else: return newNodeIter, newAdd  # the old node must have been deleted from the new root
            elif newNodeIter == oldNodeIter.next:  # the old node was deleted
                oldNodeIter = oldNodeIter.next
                curDest -= 1
            elif newNodeIter.next == oldNodeIter: # a node was inserted into the old root
                newNodeIter = newNodeIter.next
                newAdd[-1] += 1

            else: return newNodeIter, newAdd  # something more complicated happened.

        # check if still have sublevels to follow and go to them if possible
        if add:
            if newNodeIter.isSubNode():
                newNodeIter = newNodeIter.child
                oldNodeIter = oldNodeIter.child
            else: return newNodeIter, newAdd

    # check for case when something has been inserted immediately before the original position
    if newNodeIter.next == oldNodeIter:
        newNodeIter = newNodeIter.next
        newAdd[-1] += 1

    return newNodeIter, newAdd


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
