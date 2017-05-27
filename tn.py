__author__ = 'chephren'
import funobj as fo
import reader


def isPyList(lst):
    return isinstance(lst, list)

def cons(value, cdr):
    return TNode(value, next=cdr)

def join(node1, node2):
    return node1.update('next', node2)

def joinList(lst, node):
    if lst is None:
        return node

    return joinNodeAdd(lst, [lst.len()-1], node)

def dropLast(lst):
    if lst.next is None:
        return None

    return copyToAdd(lst, [lst.len()-2])


def tnodeIndex(list, index):
    """ Find and return <tnode, index> at index, otherwise return the last <tnode, index> """
    for nodeIndex, node in enumerate(list):
        if nodeIndex==index or not node.next:
            return node, nodeIndex

def tnodeFindValue(list, targetValue):
    """ Find and return <tnode, index> for first node which has a child matching targetValue,
    otherwise return the last <tnode, index> """
    for nodeIndex, node in enumerate(list):
        if node.child == targetValue or not node.next:
            return node, nodeIndex

def tnodeFindNodeOrIndex(list, targetNode, defaultIndex):
    """ Find and return <tnode, index> from list which matches the targetNode,
    otherwise return the <tnode, index> at defaultIndex"""
    for nodeIndex, node in enumerate(list):
        if node == targetNode:
            return node, nodeIndex

    return tnodeIndex(list, defaultIndex)


def tnodeAddress(tree, targetAddress, savedAddress=[]):
    """ Find and return <tnode, address> at targetAddress """
    node, nodeIndex = tnodeIndex(tree, targetAddress[0])
    newSavedAddress = list(savedAddress) + [nodeIndex]
    if targetAddress[1:] and node.isSubNode():
        return tnodeAddress(node.child, targetAddress[1:], newSavedAddress)
    else:
        return node, newSavedAddress

def tnodeGetNVSFromAdd(exp, add, acc=[]):
    cur, curPos = tnodeIndex(exp, add[0])
    accNVS = list(acc)

    if add[2:] and cur.isSubNode():
        accNVS.append(cur.child.child)
        return tnodeGetNVSFromAdd(cur.child.next.child, add[2:], accNVS)
    elif add[1:] and cur.isSubNode():
        return tnodeGetNVSFromAdd(cur.child, add[1:], accNVS)
    else:
        accNVS.append(cur.child)
        return cur, accNVS

def tnodeNVS(exp, nvs, acc=[]):
    cur, curPos = tnodeFindValue(exp, nvs[0])
    accInd = list(acc)
    accInd.append(curPos)
    if nvs[1:] and cur.isSubNode():
        return tnodeNVS(cur.child, nvs[1:], accInd)
    else:
        return cur, accInd

def tnodeSearch(exp, searchVal, acc=[]):
    searchValPred = lambda node, address : node.child == searchVal
    return tnodeSearchPred(exp, searchValPred, acc)

def tnodeSearchAfter(exp, searchVal, startingIndex):
    def searchValPred(node, address):
        if address <= startingIndex:
            return False
        if node.child == searchVal:
            return True

        return False

    return tnodeSearchPred(exp, searchValPred, [0])

def tnodeSearchPred(exp, searchPred, acc=[]):
    accInd = list(acc)
    for node in exp:
        if searchPred(node, accInd):
            return node, accInd
        elif node.isSubNode():
            foundNode, foundAdd = tnodeSearchPred(node.child, searchPred, accInd + [0])

            if foundNode is not None:
                return foundNode, foundAdd

        accInd[-1] += 1
    return None, None

def tnodeSyncAddress(newexp, oldexp, oldadd, acc=[]):
    oldNode, oldPos = tnodeIndex(oldexp, oldadd[0])
    curNode, curPos = tnodeFindNodeOrIndex(newexp, oldNode, oldadd[0])
    accInd = list(acc)
    accInd.append(curPos)
    if oldadd[1:] and curNode.isSubNode():
        return tnodeSyncAddress(curNode.child, oldNode.child, oldadd[1:], accInd)
    else:
        return curNode, accInd

# ==================================PyList Functions==================================================

def foldrpy(func, lst):
    return func(lst[0], foldrpy(func, lst[1:])) if lst else None

def foldrtpy(func, lst):
    if lst:
        if isPyList(lst[0]):
            car = foldrtpy(func, lst[0])
        else:
            car = lst[0]
        return func(car, foldrtpy(func, lst[1:]))
    return None

def isNumberedExp(val):
    if isinstance(val, TNode) and val.child == '#':
        return True
    else:
        return False

def isQuotedExp(val):
    if isinstance(val, TNode) and val.child == 'quote':
        return True
    else:
        return False

def isMethodCallExp(val):
    " [<TNode> '<sym>]"
    if isinstance(val, TNode) and val.next \
            and val.next.quoted and not val.next.isSubNode()\
            and not val.next.next:
        return True
    else:
        return False

def parseNumberedNode(car, cdr):
    if isNumberedExp(car):
        id = car.next.child
        newNode = car.next.next.update('nodeID', id)
        return join(newNode, cdr)

    elif isQuotedExp(car):
        val = car.next.child
        newNode = TNode(val, quoted=True)
        return join(newNode, cdr)

    else:
        return cons(car, cdr)


def createTNodeExpFromPyExp(pyexp):
    return foldrtpy(parseNumberedNode, pyexp) if isPyList(pyexp) else pyexp

def createTNodeExpFromPyNumberedExp(pyexp):
    return foldrtpy(parseNumberedNode, pyexp).next

# ======================================================================================================

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
            return node.update('child', opAtAdd2(node.child, newAdd, newDest))
            #return TNode(opAtAdd2(node.child, newAdd, newDest), node.nodeID, node.next)
        else:
            return op(node)

    newAdd = add[1:]
    newDest = add[0]
    return opAtAdd2(node, newAdd, newDest)

def insertAdd(node, add, value):
    return opAtAdd(node, add, lambda addNode: cons(value, addNode))

def appendAdd(node, add, value):
    return opAtAdd(node, add, lambda addNode: join(addNode, cons(value, addNode.next)))

def joinNodeAdd(node, add, node2):
    return opAtAdd(node, add, lambda addNode: join(addNode, node2))

def deleteAdd(node, add):
    return opAtAdd(node, add, lambda addNode: addNode.next)

def replaceAdd(node, add, value):
    return opAtAdd(node, add, lambda addNode: TNode(value, addNode.nodeID, addNode.next, addNode.quoted))

def copyToAdd(node, add):
    return opAtAdd(node, add, lambda addNode: TNode(addNode.child))

def nestAdd(node, add):
    return opAtAdd(node, add, lambda addNode: cons(TNode(addNode.child), addNode.next))

def denestAdd(node, add):
    return opAtAdd(node, add, lambda addNode: joinList(addNode.child, addNode.next))

def slurpAdd(node, add):
    return opAtAdd(node, add, slurpOp)

def barfAdd(node, add):
    return opAtAdd(node, add, barfOp)

def updateAdd(node, add, value):
    return opAtAdd(node, add, lambda addNode: addNode.update(value[0], value[1]))

def quoteAdd(node, add, value):
    return opAtAdd(node, add, lambda addNode: addNode.update('quoted', value))

def methodChainAdd(node, add):
    return opAtAdd(node, add, methodChainOp)

def slurpOp(addNode):
    if addNode.next is None:
        return addNode

    slurpNode = addNode.next.update('next', None)
    newNode = joinList(addNode.child, slurpNode)
    return cons(newNode, addNode.next.next)

def barfOp(addNode):
    barfNode = addNode.child.last()
    newListNode = dropLast(addNode.child)
    return cons(newListNode, join(barfNode, addNode.next))

def methodChainOp(addNode):
    nextNode = TNode(addNode.next.child, quoted=True)
    currentNode = TNode(addNode.child, next=nextNode)
    return TNode(currentNode, next=addNode.next.next)

class TNode(fo.FuncObject):
    __nodes__ = 0
    def __init__(self, val=None, id=None, next=None, quoted=False):
        self.next = next
        self.child = self.parseValue(val)
        self.quoted = quoted
        self.persist = ['child', 'next']
        self.startToken = '('
        self.endToken = ')'

        if not id:
            self.nodeID = TNode.__nodes__
            TNode.__nodes__ += 1
        else:
            self.nodeID = id

    @classmethod
    def fromFile(cls, lst):
        return cls(*lst)

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
            newNode = [reader.Symbol('#'), i.nodeID]

            if i.isSubNode():
                pyExp = i.child.toPyNumberedExp()
            else: pyExp = (i.child)

            if i.quoted:
                newNode.append([reader.Symbol('quote'), pyExp])
            else:
                newNode.append(pyExp)

            ret.append(newNode)

        return ret


    def toPyExp(self):
        ret = list()
        for i in self:
            if i.isSubNode():
                pyExp = i.child.toPyExp()
            else: pyExp = (i.child)

            if i.quoted:
                ret.append(['quote', pyExp])
            else:
                ret.append(pyExp)

        return ret

    def serialise(self, topLevel=True):
        ret = [reader.Symbol('list')]
        for i in self:
            if isinstance(i.child, TNode):
                pyExp = i.child.serialise(False)
            elif hasattr(i.child, 'serialise'):
                pyExp = i.child.serialise()
            else: pyExp = i.child

            ret.append(pyExp)

        if topLevel:
            tag = [reader.Symbol('class'), self.__class__.__module__, self.__class__.__name__]
            return tag + [ret]
        else:
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

    def len(self, currentLength=1):
        if self.next:
            return self.next.len(currentLength + 1)
        else:
            return currentLength

    def last(self):
        if self.next:
            return self.next.last()
        else:
            return self


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
