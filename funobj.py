import copy

class FuncObject(object):
    def __init__(self):
        self.persist = None

    def update(self, prop, val):
        newSelf = copy.copy(self)
        if not hasattr(newSelf, prop):
            raise AttributeError
        setattr(newSelf, prop, val)
        return newSelf

    def updateList(self, *propValueList):
        newSelf = copy.copy(self)
        for (prop, val) in propValueList:
            if not hasattr(newSelf, prop):
                raise AttributeError
            setattr(newSelf, prop, val)
        return newSelf

    def clone(self):
        newSelf = copy.copy(self)
        return newSelf

    def reset(self, *lst):
        args = zip(lst, [False]*len(lst))
        return wrapper(self.updateList, args)

    def set(self, *lst):
        args = zip(lst, [True]*len(lst))
        return wrapper(self.updateList, args)

    def updatePyList(self, propValueList):
        return wrapper(self.updateList, propValueList)

    def __str__(self):
        return '<' + type(self).__name__ + '>'


    #def toPyExp(self):
    def serialise(self):
        props = []
        for i in self.persist:
            attr = getattr(self, i)
            if hasattr(attr, 'serialise'):
                props.append([i, attr.serialise()])
            else:
                props.append([i, attr])

        return props

def wrapper(func, args):
    return func(*args)


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