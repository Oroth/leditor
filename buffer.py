import funobj as fo
import reader
from tnode import replaceAdd, appendAdd, insertAdd, deleteAdd, nestAdd, denestAdd, quoteAdd, isPyList, \
    createTNodeExpFromPyExp


class Buffer(fo.FuncObject):
    def __init__(self, root, viewAdd=[0], cursorAdd=[0]):
        self.root = root

        if isinstance(viewAdd[0], reader.Symbol):
            self.view, self.viewAdd = self.root.gotoNodeAtNVS(viewAdd)
        else:
            self.view, self.viewAdd = self.root.gotoNearestAddress(viewAdd)
        self.cursor, self.cursorAdd = self.view.gotoNearestAddress(cursorAdd)
        self.topLine = 0

    def onSubNode(self):
        return self.cursor.isSubNode()

    def cursorToPySexp(self):
        return self.cursor.childToPyExp()

    def cursorToFirst(self):
        return self.updateList(
            ('cursor', self.view.child),
            ('cursorAdd', [0, 0]))     # actually want first in thing

    def cursorToAddress(self, add):
        return Buffer(self.root, self.viewAdd, add)

    def syncToNewRoot(self, newRoot):
        newView, newViewAdd = self.root.gotoAddressOnNewRoot(self.viewAdd, newRoot)
        newCursor, newCursorAdd = self.view.gotoAddressOnNewRoot(self.cursorAdd, newView)
        return Buffer(newRoot, newViewAdd, newCursorAdd)

    def syncViewAddToNewRoot(self, newRoot):
        add = list(self.viewAdd)
        oldNodeIter = self.root
        newNodeIter = newRoot
        newAdd = []
        while add:
            curDest = add.pop(0)
            newAdd.append(0)
            while curDest != 0:
                if newNodeIter == oldNodeIter:
                    if newNodeIter.next:
                        oldNodeIter = oldNodeIter.next
                        newNodeIter = newNodeIter.next
                        curDest -= 1
                        newAdd[-1] += 1
                    else: return (newNodeIter, newAdd)  # the old node must have been deleted from the new root
                elif newNodeIter == oldNodeIter.next:  # the old node was deleted
                    oldNodeIter = oldNodeIter.next
                elif newNodeIter.next == oldNodeIter: # a node was inserted into the old root
                    newNodeIter = newNodeIter.next
                    newAdd[-1] += 1

                else: return (newNodeIter, newAdd)  # something more complicated happened.

            # check if still have sublevels to follow and go to them if possible
            if add:
                if newNodeIter.isSubNode():
                    newNodeIter = newNodeIter.child
                    oldNodeIter = oldNodeIter.child
                else: return (newNodeIter, newAdd)

        return (newNodeIter, newAdd)

    def rootToCursorAdd(self):
        return self.viewAdd + self.cursorAdd[1:]

    def opAtCursor(self, op, value=None):
        if value is not None:
            newView = op(self.view, self.cursorAdd, value)
        else:
            newView = op(self.view, self.cursorAdd)
        newImage = replaceAdd(self.root, self.viewAdd, newView.child)
        return Buffer(newImage, self.viewAdd, self.cursorAdd)

    def appendAtCursor(self, value):
        return self.opAtCursor(appendAdd, value)

    def insertAtCursor(self, value):
        return self.opAtCursor(insertAdd, value).curNext()

    def replaceAtCursor(self, value):
        return self.opAtCursor(replaceAdd, value)

    def nestCursor(self):
        return self.opAtCursor(nestAdd)

    def quoteAtCursor(self):
        return self.opAtCursor(quoteAdd)

    def deleteAtCursor(self):
        newBuff = self
        if self.cursor == self.view:
            newBuff = self.viewUp()
        newView = deleteAdd(newBuff.view, newBuff.cursorAdd)
        newImage = replaceAdd(newBuff.root, newBuff.viewAdd, newView.child)
        return Buffer(newImage, newBuff.viewAdd, newBuff.cursorAdd)

    def toggleStringAtCursor(self):
        if isinstance(self.cursor.child, reader.Symbol):
            return self.replaceAtCursor(str(self.cursor.child))
        else: return self


    def viewUp(self):
        if len(self.viewAdd) > 1:
            newViewAddress = self.viewAdd[0:-1]
        else:
            raise ValueError

        # new cursor address will be prefixed by the last step in the address to the old view
        newCursorAddress = [0] + self.viewAdd[-1:] + self.cursorAdd[1:]
        return Buffer(self.root, newViewAddress, newCursorAddress)

    def viewToCursor(self):
        newViewAddress = self.viewAdd + self.cursorAdd[1:]
        return Buffer(self.root, newViewAddress)

    def viewToRoot(self):
        return Buffer(self.root, [0], [0])

    def viewNext(self):
        if self.view.next:
            newAddress = list(self.viewAdd)
            newAddress[-1] += 1
            return Buffer(self.root, newAddress)
        else:
            raise ValueError

    def viewPrev(self):
        if self.viewAdd[-1] > 0:
            newAddress = list(self.viewAdd)
            newAddress[-1] -= 1
            return Buffer(self.root, newAddress)
        else:
            raise ValueError

    def curNext(self):
        if self.cursor.next:
            newAddress = list(self.cursorAdd)
            newAddress[-1] += 1
            return self.updateList(('cursorAdd', newAddress), ('cursor', self.cursor.next))
        else:
            raise ValueError

    def curFirst(self):
        newAddress = list(self.cursorAdd)
        newAddress[-1] = 0
        return Buffer(self.root, self.viewAdd, newAddress)

    def curLast(self):
        cur = self
        while cur.cursor.next:
            cur = cur.curNext()

        return cur

    def curBottom(self):
        cur = self
        while cur.cursor.isSubNode():
            cur = cur.curChild()

        return cur

        #return self.updateList(('cursorAdd', newAddress), ('cursor', cur.cursor))

    def curNextUpAlong(self):
        cur = self

        if cur.cursor == cur.view:
            return self

        while not cur.cursor.next:
            cur = cur.curUp()
            if cur.cursor == cur.view:
                return self

        return cur.curNext()

    def curPrev(self):
        if self.cursorAdd[-1] > 0:
            newAddress = list(self.cursorAdd)
            newAddress[-1] -= 1
            return Buffer(self.root, self.viewAdd, newAddress)
        else:
            raise ValueError

    def curPrevUpAlong(self):
        cur = self

        while not cur.cursorAdd[-1] > 0:
            cur = cur.curUp()

        return cur.curPrev()

    def curUp(self):
        if len(self.cursorAdd) > 1:
            newAddress = self.cursorAdd[0:-1]
            return Buffer(self.root, self.viewAdd, newAddress)
        else:
            raise ValueError

    def curChild(self):
        if self.cursor.isSubNode():
            newAddress = list(self.cursorAdd)
            newAddress.append(0)
            return self.updateList(('cursorAdd', newAddress), ('cursor', self.cursor.child))
        else:
            return self.cursor.child  # the value


def createBufferFromPyExp(pyexp, viewAdd=[0], cursorAdd=[0]):
    # A buffer always operates on a list, never atoms, so convert to list if necessary
    if not isPyList(pyexp):
        bufexp = [[pyexp]]
    else:
        bufexp = [pyexp]

    return Buffer(createTNodeExpFromPyExp(bufexp), viewAdd, cursorAdd)