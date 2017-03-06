__author__ = 'chephren'
import copy
import funobj as fo
import reader


def isPyList(lst):
    return isinstance(lst, list)

def cons(value, cdr):
    car = TNode(value)
    car.next = cdr
    return car

def join(node1, node2):
    car = copy.copy(node1)
    car.next = node2
    return car

def joinList(lst, node):
    newLst = copy.deepcopy(lst)
    curLast = newLst

    if curLast is None:
        return node

    while curLast.next:
        curLast = curLast.next

    curLast.next = node
    return newLst

def dropLast(lst):
    newLst = copy.deepcopy(lst)
    curLast = newLst

    if curLast.next is None:
        return None

    while curLast.next and curLast.next.next:
        curLast = curLast.next

    curLast.next = None
    return newLst


def tnodeIndex(lst, ind):
    curNode = lst
    retInd = 0
    while curNode.next and ind > 0:
        curNode = curNode.next
        ind = ind - 1
        retInd = retInd + 1
    return curNode, retInd

def tnodeFindChild(lst, val):
    curNode = lst
    retInd = 0
    while curNode.next and curNode.child != val:
        curNode = curNode.next
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

    # if add[1:] and cur.isSubNode():
    #     return tnodeGetNVSFromAdd(cur.child, add[1:], accNVS)
    # else:
    #     return cur, accNVS

def tnodeNVS(exp, nvs, acc=[]):
    cur, curPos = tnodeFindChild(exp, nvs[0])
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
    curNode, curPos = tnodeMatch(newexp, oldNode, oldadd[0])
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
    if isinstance(val, TNode) and val.next and val.next.quoted and not val.next.isSubNode():
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
        newNode.quoted = True
        return join(newNode, cdr)

    elif isMethodCallExp(car):
        methodNameNode = TNode(car.next.child)
        objExpNode = TNode(car.child, next=methodNameNode)
        newNode = TNode(objExpNode, methodChain=True)
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
    slurpNode = addNode.next.update('next', None)
    newNode = joinList(addNode.child, slurpNode)
    return cons(newNode, addNode.next.next)

def barfOp(addNode):
    barfNode = addNode.child.last()
    newListNode = dropLast(addNode.child)
    return cons(newListNode, join(barfNode, addNode.next))

def methodChainOp(addNode):
    nextNode = TNode(addNode.next.child)
    currentNode = TNode(addNode.child, next=nextNode)
    return TNode(currentNode, next=addNode.next.next, methodChain=True)

class TNode(fo.FuncObject):
    __nodes__ = 0
    def __init__(self, val=None, id=None, next=None, quoted=False, methodChain=False):
        self.next = next
        self.child = self.parseValue(val)
        self.quoted = quoted
        self.methodChain = methodChain

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
            newNode = [reader.Symbol('#'), i.nodeID]

            if i.isSubNode():
                pyExp = i.child.toPyNumberedExp()
            else: pyExp = (i.child)

            if i.quoted:
                newNode.append([reader.Symbol('quote'), pyExp])
            elif i.methodChain:
                pyExp[1] = [reader.Symbol('quote'), pyExp[1]]
                newNode.append(pyExp)
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
            elif i.methodChain:
                pyExp[1] = ['quote', pyExp[1]]
                ret.append(pyExp)
            else:
                ret.append(pyExp)

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
