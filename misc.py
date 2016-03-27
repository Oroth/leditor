__author__ = 'chephren'
# Reference file for some alternative implementations of particular functions, which are currently unused
# Can be ignored.

import tn

def numberedCons(value, cdr):
    car = tn.TNode(value[1], value[0])
    car.next = cdr
    return car

def foldr(func, lst):
    if lst[1:]:
        return func(lst[0], foldr(func, lst[1:]))
    return lst[0]

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

def foldrpy(func, lst):
    return func(lst[0], foldrpy(func, lst[1:])) if lst else None

def foldrtpy(func, lst):
    if lst:
        if tn.isPyList(lst[0]):
            return func(foldrtpy(func, lst[0]), foldrtpy(func, lst[1:]))
        else:
            return func(lst[0], foldrtpy(func, lst[1:]))
    return None

def foldrtnumpy(func, lst):
    if lst:
        if not tn.tnodeNumberedExpContainsAtom(lst):
            return func(foldrtnumpy(func, lst[0]), foldrtnumpy(func, lst[1:]))
        else:
            return func(lst[0], foldrtnumpy(func, lst[1:]))
    return None

def createTNodeExpFromPyExp2(pyexp):
    return foldrtpy(tn.cons, pyexp) if tn.isPyList(pyexp) else pyexp

def createTNodeExpFromPyNumberedExp3(pyexp):
    return foldrtnumpy(numberedCons, pyexp) if tn.isPyList(pyexp) else pyexp