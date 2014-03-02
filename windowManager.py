__author__ = 'chephren'
import TNode
from TNode import cons, Buffer
import utility
import Editors
import libtcodpy as libtcod
import evalNode
import reader

# interface

class Window(object):
    def __init(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.image = libtcod.console_new(width, height)


class Column(object):
    def __init__(self, width, function):
        self.width = width
        self.function = function
        self.rows = None

    #def widthIncrease(self, x):

    #def widthDecrease(self, x)

    def draw(self, x, y):
        self.function.draw(x, y)

    def handleKeys(self, key):
        result = self.function.handleKeys(key)
        if result:
            return True

class evalIOHandler(object):
    def __init__(self, funcTree):
        self.tree = funcTree
        self.keyHistory = []
        self.output = ''
        self.function = None

    def handleKeys(self, key):
        if key.c != 0:
            self.keyHistory.append(chr(key.c))
            self.tree.calcValue(0)
            self.function = self.tree.value[0]
            self.output = self.function(int(chr(key.c)))
            return False


    def draw(self, posx, posy, maxx, maxy, hlcol=None):
        pen = utility.Pen(posx, posy, maxx, maxy)
        pen.write(str(self.output))


class WindowManager(TNode.FuncObject):
    def __init__(self, ImageRoot):
        self.ImageRoot = ImageRoot

        # root of windows
        winRoot = TNode.TNode(self.parse_memory(ImageRoot))
        self.winTree = Buffer(winRoot, [0], [0, 0])
        #self.active = self.root
        #self.winCursor = Cursor(self.winRoot, [0])
        self.winCmd = False
        self.cols = 1
        self.wins = 1
        self.hist = ImageRoot

    def parse_memory(self, root):
        editor = root.child.next.child
        code = root.child.next.next

        edId = editor.next.child
        edAddNode = editor.next.next.child
        edAdd = edAddNode.next.child
        edAddPy = edAdd.toPySexp()
        print edAddPy

        edCurNode = editor.next.next.next.child
        edCur = edCurNode.next.child
        edCurPy = edCur.toPySexp()
        print "edCurPy", edCurPy

#        actCode = root.gotoAddress(edAddPy)
#        listEd = Editors.TreeEditor(root, actCode, edCurPy)

#        curs = Cursor(root, edAddPy)
#        listEd = Editors.TreeEditor(curs, edAddPy)
        listEd = Editors.TreeEditor(root, edAddPy)

        return TNode.TNode(listEd)

    def writeImage(self):

        pyObj = self.ImageRoot.child.toPySexp()
        text = reader.to_string(pyObj)
        f = open("image", 'w')
        f.write(text)
        f.close()

#    def addCol(self):
#        self.cols += 1
#        newWidth = utility.screenWidth() / self.cols
#        #need to readjust all columns..
#        self.active.insertAfter(newWidth)
#        self.active = self.active.next
#
#        iter = self.winRoot
#        iter.child.width = newWidth
#        while iter.next:
#            iter.next.child.width = newWidth
#            iter = iter.next

    def addWindow(self, newFunc):
        self.wins += 1
        newWinTree = self.winTree.appendAtCursor(newFunc).curNext()
        return newWinTree

    def draw(self):
        maxX = utility.screenWidth()
        curY = 0
        yStep = utility.screenHeight() / self.wins

        for i in self.winTree.root.child:
            if i == self.winTree.cursor:
                i.child.draw(0, curY, maxX, curY + yStep, libtcod.azure)
            else: i.child.draw(0, curY, maxX, curY + yStep, libtcod.grey)
            curY += yStep
            if i.next:
                libtcod.console_hline(0, 0, curY - 1, utility.screenWidth())


    def handleKeys(self, key):
        #return self.active.child.function.handleKeys(key)

        if self.winCmd:

            if chr(key.c) == 'j':
                try:
                    return self.updateList(
                        ('winTree', self.winTree.curNext()),
                        ('winCmd', False))
                except ValueError: pass

            elif chr(key.c) == 'k':
                try:
                    return self.updateList(
                        ('winTree', self.winTree.curPrev()),
                        ('winCmd', False))
                except ValueError: pass

            elif chr(key.c) == 'o':
                #abomination
                #cursorToView
                curAdd = self.winTree.cursor.child.buffer.cursorAdd
                viewAdd = self.winTree.cursor.child.buffer.viewAdd
                newEd = Editors.TreeEditor(self.ImageRoot, viewAdd + curAdd[1:])
                newWinTree = self.addWindow(newEd)
                return self.updateList(
                    ('winTree', newWinTree),
                    ('winCmd', False)
                )


            elif chr(key.c) == 'd':
                if self.wins > 1:
                    return self.updateList(
                        ('winTree', self.winTree.deleteAtCursor()),
                        ('wins', self.wins - 1))


            elif chr(key.c) == 'u':
                if self.hist.next:
                    self.ImageRoot = self.hist.next
                    self.hist = self.hist.next

            elif chr(key.c) == 'w':
                try:
                    next = self.winTree.curNext()
                except ValueError:
                    next = self.winTree.cursorToStart()

                return self.updateList(
                    ('buffer', next),
                    ('winCmd', False))

            # run a function like a program
            elif key.vk == libtcod.KEY_SPACE:
                newTree = TNode.copyTNodeAsNewTreeClass(self.active.child.active, evalNode.EvalNode)
                newTree.calcValue(0)
                prog = evalIOHandler(newTree)
                self.addWindow(prog)
                self.active = self.active.next
                self.winCmd = False

            elif key.vk == libtcod.KEY_ENTER:
                newTree = TNode.copyTNodeAsNewTreeClass(self.active.child.active, evalNode.EvalNode)
                newEd = Editors.TreeEditor(newTree)
                newEd.showValues = True
                newEd.env = evalNode.global_env
                newEd.root.calcValue(newEd.id)
                self.addWindow(newEd)
                self.active = self.active.next
                self.winCmd = False

            elif chr(key.c) == '>':
                #newTree = TNode.copyTNodeAsNewTreeClass(self.active.child.active, evalNode.EvalNode)
                activeEd = self.active.child
                activeNode = self.active.child.active

                if activeNode.isSubNode():
                    args = []
                    if activeNode.child.next:
                        for i in activeNode.child.next:
                            args.append(i.getValue(self.active.child.id))


                    (newTree, env) = activeNode.child.getValue(activeEd.id)('inspect', *args)
                    newEd = Editors.TreeEditor(newTree)
                    newEd.context = activeNode.child
                    newEd.contextParent = activeEd.id
                    newEd.showValues = True
                    newEd.env = env
                    #newEd.root.calcValue()
                    newEd.root.eval(newEd.id, env)
                    self.addWindow(newEd)
                    self.active = self.active.next
                self.winCmd = False

        elif chr(key.c) == 'w': #and key.lctrl:
            self.winCmd = True
            print "windowing"

        else:
            result = self.winTree.cursor.child.handleKeys(key)
            #print "result ", result
            if result == 'ESC':
                self.writeImage()
                return False

            if result == 'UNDO':
                if self.hist.next:
                    self.ImageRoot = self.hist.next
                    self.hist = self.hist.next

            else:
                self.winTree = self.winTree.replaceAtCursor(result)

                if self.ImageRoot != result.buffer.root:
                    self.ImageRoot = result.buffer.root
                    if result.updateUndo:
                        self.hist = cons(self.ImageRoot.child, self.hist)
                    #print "hist", self.hist.child.toPySexp()

            # need to sync all Editors to the newTree
            for i in self.winTree.root.child:
                i.child = i.child.syncWithImage(self.ImageRoot)
            #functional: map(self.winTree.root.child .syncWithImage)

            return self
            #return self.update('winTree', self.winTree.replaceAtCursor(result))

        return self


