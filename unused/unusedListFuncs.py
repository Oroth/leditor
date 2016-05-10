__author__ = 'chephren'
# Reference file for some alternative implementations of particular functions, which are currently unused
# Can be ignored.

import tn

def cons(value, cdr):
    car = tn.TNode(value)
    car.next = cdr
    return car


# def foldr(func, lst):
#     if lst[1:]:
#         return func(lst[0], foldr(func, lst[1:]))
#     return lst[0]

def tnodeIndex2(lst, ind):
    return tnodeIndex2(lst.next, ind-1) if lst.next and ind > 0 else lst[0]

def tnodeFold(func, lst, acc=None):
    if acc is None:
        acc = lst[0]
        newLst = lst.next
    else:
        newLst = lst
    if lst.next:
        return tnodeFold(func, newLst.next, func(acc, newLst))
    else:
        return acc

def tnodeFoldR(func, lst, last):
    if lst.next:
        return func(lst, tnodeFold(func, lst.next, last))
    else:
        return func(lst, last)



def append(first, sec):
    if sec:
        ret = tn.TNode(sec)
    else:
        ret = None
    first.next = ret
    return ret

def numberedCons(value, cdr):
    car = tn.TNode(value[1], value[0])
    car.next = cdr
    return car

def makeNumberedNode(numberedExp):
    id = numberedExp.next.child
    val = numberedExp.next.next.child
    return val


def transformPyLst(func, acc, lst):
    start = cur = acc
    for i in lst:
        cur = func(cur, i)
    return start

def transformPyExp(func, initfunc, acc, exp):
    start = cur = acc

    for i in exp:
        if tn.isPyList(i):
            cur = func(cur, transformPyExp(func, initfunc, initfunc(i[0]) , i[1:]))
        else:
            cur = func(cur, i)
    return start


def createTNodeExpFromPyExp2(pyexp):
    return transformPyExp(append, tn.TNode, tn.TNode(pyexp[0]), pyexp[1:]) if tn.isPyList(pyexp) else pyexp


def foldrtnumpy(func, lst):
    if lst:
        if tnodeNumberedExpContainsAtom(lst):
            return lst
        elif tn.isPyList(lst):
            return func(foldrtnumpy(func, lst[0]), foldrtnumpy(func, lst[1:]))
        else:
            return func(lst[0], foldrtnumpy(func, lst[1:]))
    return None

def createTNodeExpFromPyNumberedExp2(pyexp):
    return foldrtnumpy(numberedCons, pyexp) if tn.isPyList(pyexp) else pyexp




def createTNodeExpFromPyExp3(pyexp):
    startNode = None
    lastNode = None

    if pyexp is not None:
        if tn.isPyList(pyexp):
            for i in pyexp:
                if startNode:
                    newNode = tn.TNode(createTNodeExpFromPyExp3(i))
                    lastNode.next = newNode
                    lastNode = lastNode.next
                else:
                    startNode = tn.TNode(createTNodeExpFromPyExp3(i))
                    lastNode = startNode
        else:
            return pyexp

    return startNode

# Should be an integer-pyObj Pair
def tnodeNumberedExpContainsAtom(pynumexp):
    if len(pynumexp) == 2 and not tn.isPyList(pynumexp[0]) and not tn.isPyList(pynumexp[1]):
        return True
    else:
        return False

# like createTreeFromSexp, but picks up the nodeID
def createTNodeExpFromPyNumberedExp4(pyexp):
    if tnodeNumberedExpContainsAtom(pyexp):
        return tn.TNode(pyexp[1], pyexp[0])

    else:  # sexp = (id (sexp|atom ...))
        nodeID, pysubexp = pyexp[0], pyexp[1]

        startNode = None
        lastNode = None
        for i in pysubexp:
            if startNode:
                node = createTNodeExpFromPyNumberedExp4(i)
                lastNode.next = node
                lastNode = lastNode.next
            else:
                startNode = createTNodeExpFromPyNumberedExp4(i)
                lastNode = startNode

        return tn.TNode(startNode, nodeID)

