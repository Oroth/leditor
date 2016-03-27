import funobj as fo
import reader
import tn
from tn import replaceAdd, appendAdd, insertAdd, deleteAdd, nestAdd, denestAdd, quoteAdd, isPyList, \
    createTNodeExpFromPyExp


class Buffer(fo.FuncObject):
    def __init__(self, root, viewAdd=[0], cursorAdd=[0]):
        self.root = root
        #self.view, self.viewAdd = self.root.gotoNearestAddress(viewAdd)
        #self.cursor, self.cursorAdd = self.view.gotoNearestAddress(cursorAdd)
        self.view, self.viewAdd = tn.tnodeAddress(self.root, viewAdd)
        self.cursor, self.cursorAdd = tn.tnodeAddress(self.view, cursorAdd)
        self.topLine = 0

    @classmethod
    def new(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def fromPyExp(cls, pyexp, viewAdd=[0], cursorAdd=[0]):
        # A buffer always operates on a list, never atoms, so convert to list if necessary
        if not isPyList(pyexp):
            bufexp = [[pyexp]]
        else:
            bufexp = [pyexp]
        return cls(createTNodeExpFromPyExp(bufexp), viewAdd, cursorAdd)

    def onSubNode(self):
        return self.cursor.isSubNode()

    def cursorToPyExp(self):
        return self.cursor.childToPyExp()

    def cursorToFirst(self):
        return self.updateList(
            ('cursor', self.view.child),
            ('cursorAdd', [0, 0]))

    def cursorToAddress(self, add):
        return self.new(self.root, self.viewAdd, add)

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
        newBuff = self
        if self.cursor == self.view:
            newBuff = self.viewUp()
        newView = deleteAdd(newBuff.view, newBuff.cursorAdd)
        newImage = replaceAdd(newBuff.root, newBuff.viewAdd, newView.child)
        return self.new(newImage, newBuff.viewAdd, newBuff.cursorAdd)


    def viewUp(self):
        if len(self.viewAdd) > 1:
            newViewAddress = self.viewAdd[0:-1]
        else:
            raise ValueError

        # new cursor address will be prefixed by the last step in the address to the old view
        newCursorAddress = [0] + self.viewAdd[-1:] + self.cursorAdd[1:]
        return self.new(self.root, newViewAddress, newCursorAddress)

    def viewToCursor(self):
        newViewAddress = self.viewAdd + self.cursorAdd[1:]
        return self.new(self.root, newViewAddress)

    def viewToRoot(self):
        return self.new(self.root, [0], [0])

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

    def curNext(self):
        if self.cursor.next:
            newAddress = list(self.cursorAdd)
            newAddress[-1] += 1
            return self.updateList(('cursorAdd', newAddress), ('cursor', self.cursor.next))
        else:
            raise ValueError

    def curPrev(self):
        if self.cursorAdd[-1] > 0:
            newAddress = list(self.cursorAdd)
            newAddress[-1] -= 1
            return self.new(self.root, self.viewAdd, newAddress)
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
        return self.new(self.root, self.viewAdd, newAddress)

    def curLast(self):
        cur = self
        while cur.cursor.next:
            cur = cur.curNext()
        return cur

    def curUp(self):
        if len(self.cursorAdd) > 1:
            newAddress = self.cursorAdd[0:-1]
            return self.new(self.root, self.viewAdd, newAddress)
        else:
            raise ValueError

    def curChild(self):
        if self.cursor.isSubNode():
            newAddress = list(self.cursorAdd)
            newAddress.append(0)
            return self.updateList(('cursorAdd', newAddress), ('cursor', self.cursor.child))
        else:
            raise ValueError



class BufferSexp(Buffer):
    def __init__(self, root, viewAdd=[0], cursorAdd=[0]):
        super(BufferSexp, self).__init__(root, viewAdd, cursorAdd)

    def syncToNewRoot(self, newRoot):
        #newView, newViewAdd = tn.getAddressOnNewExp(self.viewAdd, self.root, newRoot)
        #newCursor, newCursorAdd = tn.getAddressOnNewExp(self.cursorAdd, self.view, newView)
        newView, newViewAdd = tn.tnodeSyncAddress(newRoot, self.root, self.viewAdd)
        newCursor, newCursorAdd = tn.tnodeSyncAddress(newView, self.view, self.cursorAdd)
        return self.new(newRoot, newViewAdd, newCursorAdd)

    def quoteAtCursor(self):
        return self.opAtCursor(quoteAdd)

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

    def curNextSymbol(self):
        return self.curNextUpAlong().curBottom()

    def curNextUnzippedSymbol(self, nodeIsZipped):
        return self.curNextUpAlong().curUnzippedBottom(nodeIsZipped)

    def curPrevSymbol(self):
        return self.curPrevUpAlong().curBottomLast()

    def curPrevUnzippedSymbol(self, nodeIsZipped):
        return self.curPrevUpAlong().curUnzippedBottomLast(nodeIsZipped)

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
            last = self.curChild().curLast()
            return last.curUnzippedBottomLast(nodeIsZipped)
        else:
            return self

    def curChildExp(self):
        try:
            return self.curChild()
        except ValueError:
            return self.cursor.child
