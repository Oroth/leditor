import copy

class FuncObject(object):
    def update(self, prop, val):
        newSelf = copy.copy(self)
        setattr(newSelf, prop, val)
        return newSelf

    def updateList(self, *propValueList):
        newSelf = copy.copy(self)
        for (prop, val) in propValueList:
            if not hasattr(newSelf, prop):
                raise AttributeError
            setattr(newSelf, prop, val)
        return newSelf





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