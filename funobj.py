import copy
from reader import Symbol


class FuncObject(object):
    def __init__(self):
        self.persist = None

    @classmethod
    def fromFile(cls, lst):
        return cls().updateList(*lst)

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

    def updateRecList(self, *propValueList):
        newSelf = copy.copy(self)
        for (prop, val) in propValueList:
            if not hasattr(newSelf, prop):
                raise AttributeError

            if isinstance(val, (list, tuple)):
                pass
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


    # not very happy with this
    def serialise(self):
        tag = [Symbol('class'), self.__class__.__module__, self.__class__.__name__]
        props = [Symbol('list')]
        for i in self.persist:
            attr = getattr(self, i)
            if hasattr(attr, 'serialise'):
                props.append([Symbol('list'), i, attr.serialise()])
            elif isinstance(attr, list):
                newattr = [Symbol('list')]
                newattr.extend(attr)
                props.append([Symbol('list'), i, newattr])
            else:
                props.append([Symbol('list'), i, attr])

        tag.append(props)
        return tag



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