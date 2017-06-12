"""
Provides data structures for creating and setting references
"""

import funobj as fo

class Store(fo.FuncObject):
    def __init__(self):
        self._store = []

    def newValue(self, value):
        newStore = list(self._store)
        newStore.append(value)
        refIndex = Ref(len(newStore) -1)
        return self.update('_store', newStore), refIndex

    def get(self, ref):
        return self._store[ref._id]

    def set(self, ref, value):
        newStore = list(self._store)
        newStore[ref._id] = value
        return self.update('_store', newStore)


class Ref(fo.FuncObject):
    def __init__(self, val):
        self._id = val


if __name__ == '__main__':

    t = Ref(55)

