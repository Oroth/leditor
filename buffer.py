import funobj as fo
import reader
import tn
from tn import replaceAdd, appendAdd, insertAdd, deleteAdd, nestAdd, denestAdd, quoteAdd, isPyList, \
    createTNodeExpFromPyExp, updateAdd, methodChainAdd, slurpAdd, barfAdd

class SimpleBuffer(fo.FuncObject):
    def __init__(self, root=None, cursorAdd=[0]):
        if root is None:
            self.root = tn.TNode([[reader.Symbol('')]])
        else:
            self.root = root
        self.cursor, self.cursorAdd = tn.tnodeAddress(self.root, cursorAdd)
        self.persist = ['cursorAdd']

    @classmethod
    def new(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def fromPyExp(cls, *fargs):
        pyexp = fargs[0]
        restargs = fargs[1:]
        # A buffer always operates on a list, never atoms, so convert to list if necessary
        if not isPyList(pyexp):
            bufexp = [[pyexp]]
        else:
            bufexp = [pyexp]
        return cls(createTNodeExpFromPyExp(bufexp), *restargs)

    def syncToNewRoot(self, newRoot):
        newCursor, newCursorAdd = tn.tnodeSyncAddress(newRoot, self.root, self.cursorAdd)
        return self.new(newRoot, newCursorAdd)

    def newCursorAdd(self, newCursorAdd):
        cursor, cursorAdd = tn.tnodeAddress(self.root, newCursorAdd)
        return self.updateList(('cursor', cursor), ('cursorAdd', cursorAdd))

    def onSubNode(self):
        return self.cursor.isSubNode()

    def onFirstNode(self):
        return self.cursorAdd[-1] == 0

    def rootChild(self):
        return self.root.child

    @property
    def current(self):
        return self.cursor.child

    def toPyExp(self):
        return self.root.childToPyExp()

    def cursorToPyExp(self):
        return self.cursor.childToPyExp()

    def cursorToFirst(self):
        return self.newCursorAdd([0, 0])

    def rootToCursor(self):
        return self.new(self.cursor)

    def opAtCursor(self, op, value=None):
        if value is not None:
            newImage = op(self.root, self.cursorAdd, value)
        else:
            newImage = op(self.root, self.cursorAdd)
        return self.new(newImage, self.cursorAdd)

    def appendAtCursor(self, value):
        return self.opAtCursor(appendAdd, value)

    def insertAtCursor(self, value):
        return self.opAtCursor(insertAdd, value).curNext()

    def replaceAtCursor(self, value):
        return self.opAtCursor(replaceAdd, value)

    def nestCursor(self):
        return self.opAtCursor(nestAdd)

    def denestCursor(self):
        return self.opAtCursor(denestAdd)

    def deleteAtCursor(self):
        return self.opAtCursor(deleteAdd)

    def slurpAtCursor(self):
        return self.opAtCursor(slurpAdd)

    def barfAtCursor(self):
        return self.opAtCursor(barfAdd)

    def length(self):
        return sum(1 for _ in self.root.child)

    def search(self, searchValue):
        foundNode, foundAdd = tn.tnodeSearchAfter(self.root, searchValue, self.cursorAdd)

        if foundNode is not None:
            return self.newCursorAdd(foundAdd)
        else:
            raise ValueError


    def curNext(self):
        if self.cursor.next:
            newAddress = list(self.cursorAdd)
            newAddress[-1] += 1
            return self.updateList(('cursorAdd', newAddress), ('cursor', self.cursor.next))
        else:
            raise ValueError

    def curCycle(self):
        if self.cursor.next:
            return self.curNext()
        else:
            return self.curFirst()

    def curCyclePrev(self):
        try:
            return self.curPrev()
        except ValueError:
            return self.curLast()

    def curPrev(self):
        if self.cursorAdd[-1] > 0:
            newAddress = list(self.cursorAdd)
            newAddress[-1] -= 1
            return self.newCursorAdd(newAddress)
        else:
            raise ValueError

    def curPrevUpAlong(self):
        cur = self
        while not cur.cursorAdd[-1] > 0:
            cur = cur.curUp()
        return cur.curPrev()

    def curFirst(self):
        newAddress = list(self.cursorAdd)
        newAddress[-1] = 0
        return self.newCursorAdd(newAddress)

    def curLast(self):
        cur = self
        while cur.cursor.next:
            cur = cur.curNext()
        return cur

    def curUp(self):
        if len(self.cursorAdd) > 1:
            newAddress = self.cursorAdd[0:-1]
            return self.newCursorAdd(newAddress)
        else:
            raise ValueError

    def curChild(self):
        if self.cursor.isSubNode():
            newAddress = list(self.cursorAdd)
            newAddress.append(0)
            return self.updateList(('cursorAdd', newAddress), ('cursor', self.cursor.child))
        else:
            raise ValueError

    def findFirst(self, pred):
        for n, node in enumerate(self.rootChild()):
            if pred(node.child):
                return self.newCursorAdd([0, n])
        else:
            raise ValueError

    def mapRoot(self, func):
        newTree = [func(node.child) for node in self.root.child]
        return self.fromPyExp(newTree, self.cursorAdd)

    def getNVSListAtCursor(self):
        return tn.tnodeGetNVSFromAdd(self.root.child, self.cursorAdd[1:])


class ViewBuffer(SimpleBuffer):
    def __init__(self, root=None, viewAdd=[0], cursorAdd=[0]):
        if root is None:
            self.root = tn.TNode([[reader.Symbol('')]])
        else:
            self.root = root
        self.view, self.viewAdd = tn.tnodeAddress(self.root, viewAdd)
        self.cursor, self.cursorAdd = tn.tnodeAddress(self.view, cursorAdd)
        self.persist = ['cursorAdd', 'root']

    def emptyBuffer(self):
        firstNode = self.root.child
        if firstNode.isSubNode():
            return firstNode.child.child == ''
        else:
            return firstNode.child == ''

    def newCursorAdd(self, newCursorAdd):
        cursor, cursorAdd = tn.tnodeAddress(self.view, newCursorAdd)
        return self.updateList(('cursor', cursor), ('cursorAdd', cursorAdd))

    def rootToCursorAdd(self):
        return self.viewAdd + self.cursorAdd[1:]

    def opAtCursor(self, op, value=None):
        if value is not None:
            newView = op(self.view, self.cursorAdd, value)
        else:
            newView = op(self.view, self.cursorAdd)
        newImage = replaceAdd(self.root, self.viewAdd, newView.child)
        newBuff = self.new(newImage, self.viewAdd, self.cursorAdd)
        return newBuff

    def deleteAtCursor(self):
        newBuff = self
        if self.cursor == self.view:
            newBuff = self.viewUp()
        return newBuff.opAtCursor(deleteAdd)

    def viewUp(self):
        if len(self.viewAdd) > 1:
            newViewAddress = self.viewAdd[0:-1]
        else:
            raise ValueError

        # new cursor address will be prefixed by the last step in the address to the old view
        newCursorAddress = [0] + self.viewAdd[-1:] + self.cursorAdd[1:]
        return self.new(self.root, newViewAddress, newCursorAddress)

    def viewToCursor(self):
        if not self.cursor.isSubNode():
            raise ValueError
        newViewAddress = self.viewAdd + self.cursorAdd[1:]
        return self.new(self.root, newViewAddress)

    def viewToRoot(self):
        return self.new(self.root, [0], [0])

    def newViewAdd(self, add):
        return self.new(self.root, add, self.viewAdd)

    def viewNext(self):
        if self.view.next:
            newAddress = list(self.viewAdd)
            newAddress[-1] += 1
            return self.new(self.root, newAddress)
        else:
            raise ValueError

    def viewPrev(self):
        if self.viewAdd[-1] > 0:
            newAddress = list(self.viewAdd)
            newAddress[-1] -= 1
            return self.new(self.root, newAddress)
        else:
            raise ValueError



class BufferSexp(ViewBuffer):
    def __init__(self, root=None, viewAdd=[0], cursorAdd=[0]):
        super(BufferSexp, self).__init__(root, viewAdd, cursorAdd)
        self.persist = ['viewAdd', 'cursorAdd']

    def indexNewRoot(self, newRoot):
        return self.new(newRoot, self.viewAdd, self.cursorAdd)

    def syncToNewRoot(self, newRoot):
        newView, newViewAdd = tn.tnodeSyncAddress(newRoot, self.root, self.viewAdd)
        newCursor, newCursorAdd = tn.tnodeSyncAddress(newView, self.view, self.cursorAdd)
        return self.new(newRoot, newViewAdd, newCursorAdd)

    def quoteAtCursor(self):
        return self.opAtCursor(quoteAdd, not self.cursor.quoted)

    def updateAtCursor(self, property, value):
        return self.opAtCursor(updateAdd, [property, value])

    def methodChainAtCursor(self):
        return self.opAtCursor(methodChainAdd)

    def toggleStringAtCursor(self):
        if isinstance(self.cursor.child, reader.Symbol):
            return self.replaceAtCursor(str(self.cursor.child))
        else: return self

    # move along to the next list and go to the first child
    def curNextChild(self):
        cur = self.curNext()
        while not cur.onSubNode():
            cur = cur.curNext()
        return cur.curChild()

    def curNextUpAlong(self):
        cur = self
        if cur.cursor == cur.view:
            return self
        while not cur.cursor.next:
            cur = cur.curUp()
            if cur.cursor == cur.view:
                return self
        return cur.curNext()

    def curDownAlong(self, nodeIsZipped):
        cur = self
        while not cur.onSubNode() or nodeIsZipped(cur.cursor):
            if nodeIsZipped(cur.cursor):
                cur = cur.curUp().curNextUpAlong()
            else:
                cur = cur.curNextUpAlong()
        return cur.curChild()

    def curNextSymbol(self):
        return self.curNextUpAlong().curBottom()

    def curNextUnzippedSymbol(self, nodeIsZipped):
        if nodeIsZipped(self.cursor):
            return self.curUp().curNextUpAlong().curUnzippedBottom(nodeIsZipped)
        else:
            return self.curNextUpAlong().curUnzippedBottom(nodeIsZipped)

    def curPrevSymbol(self):
        return self.curPrevUpAlong().curBottomLast()

    def curPrevUnzippedSymbol(self, nodeIsZipped):
        return self.curPrevUpAlong().curUnzippedBottomLast(nodeIsZipped)

    def curUnzippedLast(self, nodeIsZipped):
        cur = self
        while cur.cursor.next and not nodeIsZipped(cur.cursor):
            cur = cur.curNext()
        return cur

    def curBottom(self):
        cur = self
        while cur.cursor.isSubNode():
            cur = cur.curChild()
        return cur

    def curBottomLast(self):
        if self.cursor.isSubNode():
            last = self.curChild().curLast()
            return last.curBottomLast()
        else:
            return self

    def curUnzippedBottom(self, nodeIsZipped):
        cur = self
        while cur.cursor.isSubNode() and not nodeIsZipped(cur.cursor):
            cur = cur.curChild()
        return cur

    def curUnzippedBottomLast(self, nodeIsZipped):
        if self.cursor.isSubNode() and not nodeIsZipped(self.cursor):
            last = self.curChild().curUnzippedLast(nodeIsZipped)
            return last.curUnzippedBottomLast(nodeIsZipped)
        else:
            return self

    def curChildExp(self):
        try:
            return self.curChild()
        except ValueError:
            return self.cursor.child
