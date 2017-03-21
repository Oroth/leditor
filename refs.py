"""
Provides data structures for creating and setting references
"""

import funobj as fo

class Store(fo.FuncObject):
    def __init__(self):
        self._store = []

    def newValue(self, value):
        self._store.append(value)


    def fnSyncRef(self, refSetter):
        newStore = list(self._store)
        newStore[refSetter.refid] = refSetter.newVal
        return self.update('_store', newStore)

    def syncRef(self, refSetter):
        self._store[refSetter.refid] = refSetter.newVal


s = Store()


class Ref(fo.FuncObject):
    __IDs__ = 0
    __store__ = s

    def __init__(self, val):
        self.id = Ref.__IDs__
        Ref.__IDs__ += 1

        Ref.__store__.newValue(val)

    def get(self):
        return Ref.__store__._store[self.id]

    def setRef(self, newVal):
        return RefSetter(self.id, newVal)


class RefSetter(fo.FuncObject):
    def __init__(self, refid, val):
        self.refid = refid
        self.newVal = val


if __name__ == '__main__':

    t = Ref(55)

