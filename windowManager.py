__author__ = 'chephren'
import TNode
from TNode import cons, Buffer
import Editors
import reader
import CodeEditor
import os.path
import iop


# interface

class Window(object):
    def __init(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.image = iop.console_new(width, height)


class Column(object):
    def __init__(self, width, function):
        self.width = width
        self.function = function
        self.rows = None

    def draw(self, x, y):
        self.function.draw(x, y)

    def handleKeys(self, key):
        result = self.function.handleKeys(key)
        if result:
            return True



class WindowManager(TNode.FuncObject):
    def __init__(self, imageRoot, imageFileName):
        self.ImageRoot = imageRoot
        winRoot = TNode.TNode(self.loadEditorSettings(imageRoot))
        self.winTree = Buffer(winRoot, [0], [0, 0])
        self.winCmd = False
        self.cols = 1
        self.wins = 1
        self.hist = imageRoot
        self.imageFileName = imageFileName

    def writeImage(self):
        pyObj = self.ImageRoot.child.toNodeIDValuePySexp()
        text = reader.to_string(pyObj)
        f = open(self.imageFileName, 'w')
        f.write(text)
        f.close()

    def getEditSexp(self):
        curWin = self.winTree.cursor
        curEd = curWin.child
        viewAdd = curEd.buffer.viewAdd
        cursorAdd = curEd.buffer.cursorAdd
        s = reader.Symbol
        zipList = []
        for k, v in curEd.zippedNodes.iteritems():
            if v is True:
                zipList.append(k)

        return [reader.Symbol('editor'),
                    [s('address'), self.winTree.viewAdd], [s('cursor'), self.winTree.cursorAdd],
                    [reader.Symbol('window'), [reader.Symbol('id'), curEd.id],
                    [reader.Symbol('maxx'), curEd.maxx], [reader.Symbol('maxy'), curEd.maxy],
                    [reader.Symbol('address'), viewAdd], [reader.Symbol('cursor'), cursorAdd],
                    [reader.Symbol('printingMode'), curEd.printingMode],
                    [reader.Symbol('zippedNodes'), zipList]]]

    def writeEditor(self):
        pyObj = self.getEditSexp()
        text = reader.to_string(pyObj)
        f = open('EditorSettings', 'w')
        f.write(text)
        f.close()

    def loadEditorSettings(self, root):
        if os.path.isfile("EditorSettings"):
            pyEditorLoad = reader.loadFile("EditorSettings")
            window = dict(pyEditorLoad[3][1:])
            edZipNode = dict(zip(window['zippedNodes'], [True]*len(window['zippedNodes'])))

            listEd = CodeEditor.CodeEditor(root, window['address'], window['cursor'], edZipNode)
            listEd.printingMode = window['printingMode']
            listEd.id = window['id']

        else:
            listEd = Editors.TreeEditor(root)

        return TNode.TNode(listEd)

    def addCol(self):
       self.cols += 1
       newWidth = iop.screenWidth() / self.cols
       #need to readjust all columns..
       self.active.insertAfter(newWidth)
       self.active = self.active.next

       iter = self.winRoot
       iter.child.width = newWidth
       while iter.next:
           iter.next.child.width = newWidth
           iter = iter.next

    def addWindow(self, newFunc):
        self.wins += 1
        newWinTree = self.winTree.appendAtCursor(newFunc).curNext()
        return newWinTree

    # calculates and sets posx, posy, maxx, maxy for all windows trying to allocate available screen real estate
    # as equally as possible
    def calculateWindowPositions(self):
        maxX = iop.screenWidth()
        curY = 0

        screenForWins = iop.screenHeight() #- numberOfBorders
        minYStep = screenForWins / self.wins
        leftover = screenForWins % self.wins

        for i in self.winTree.root.child:
            if leftover > 0:
                curYStep = minYStep + 1
                leftover -= 1
            else:
                curYStep = minYStep

            i.child.setPosition(0, curY, maxX, curYStep)
            curY += curYStep


    def draw(self):
        self.calculateWindowPositions()

        maxX = iop.screenWidth()
        curY = 0
        screenForWins = iop.screenHeight()
        minYStep = screenForWins / self.wins
        leftover = screenForWins % self.wins

        for i in self.winTree.root.child:
            if leftover > 0:
                curYStep = minYStep + 1
                leftover -= 1
            else:
                curYStep = minYStep

            if i == self.winTree.cursor:
                i.child.draw(0, curY, maxX, curYStep, isActive=True)
            else: i.child.draw(0, curY, maxX, curYStep, isActive=False)
            curY += curYStep


    def matchWindowToClick(self, x, y):
        winAdd = [0, 0]
        for winNode in self.winTree.root.child:
            win = winNode.child
            if win.posx <= x < win.posx + win.maxx and win.posy <= y < win.posy + win.maxy:
                return winNode, winAdd
            winAdd[-1] += 1


    def handleKeys(self, key, mouse):
        if mouse.lbuttonPressed():
            windowClicked, windowAddress = self.matchWindowToClick(mouse.x(), mouse.y())
            if windowClicked != self.winTree.cursor:
                new = self.winTree.cursorToAddress(windowAddress)
                self.winTree = new # imperative at the moment to allow simultaenously switching and selecting
                # an expression

                #return self.updateList(
                #    ('winTree', new),
                #    ('winCmd', False))

        if self.winCmd:

            if key.char() == 'j':
                try:
                    return self.updateList(
                        ('winTree', self.winTree.curNext()),
                        ('winCmd', False))
                except ValueError: pass

            elif key.char() == 'k':
                try:
                    return self.updateList(
                        ('winTree', self.winTree.curPrev()),
                        ('winCmd', False))
                except ValueError: pass

            elif key.char() == 'o':
                #cursorToView
                curEd = self.winTree.cursor.child
                newEd = Editors.TreeEditor(self.ImageRoot, curEd.buffer.rootToCursorAdd(),
                                           zippedNodes=curEd.zippedNodes)
                newWinTree = self.addWindow(newEd)
                return self.updateList(
                    ('winTree', newWinTree),
                    ('winCmd', False))

            elif key.char() == 'd':
                if self.wins > 1:
                    return self.updateList(
                        ('winTree', self.winTree.deleteAtCursor()),
                        ('wins', self.wins - 1),
                        ('winCmd', False))

            elif key.char() == 'u':
                if self.hist.next:
                    return self.updateList(
                        ('ImageRoot', self.hist.next),
                        ('hist', self.hist.next))

            elif key.char() == 'w':
                try:
                    next = self.winTree.curNext()
                except ValueError:
                    next = self.winTree.cursorToFirst()

                return self.updateList(
                    ('winTree', next),
                    ('winCmd', False))

            # run a function like a program
            elif key.code() == iop.KEY_SPACE:
                curEd = self.winTree.cursor.child
                evalBuffer = TNode.Buffer(self.ImageRoot, curEd.buffer.rootToCursorAdd())
                prog = CodeEditor.evalIOHandler(evalBuffer)
                newWinTree = self.addWindow(prog)

                newWM = self.updateList(
                    ('winTree', newWinTree),
                    ('winCmd', False))

                return newWM

            elif key.code() == iop.KEY_ENTER:
                curEd = self.winTree.cursor.child
                newEd = CodeEditor.CodeEditor(self.ImageRoot, curEd.buffer.rootToCursorAdd(),
                                              zippedNodes=curEd.zippedNodes)
                newEd.evalBuffer()
                newWinTree = self.addWindow(newEd)

                return self.updateList(
                    ('winTree', newWinTree),
                    ('winCmd', False))

            elif key.char() == '>':
                print 'inspecting'
                curEd = self.winTree.cursor.child
                curNode = curEd.buffer.cursor

                if curNode.isSubNode():
                    args = []
                    if curNode.child.next:
                        for i in curNode.child.next:
                            args.append(curEd.nodeValues[i])

                    (newTree, env) = curEd.nodeValues[curNode.child]('inspect', *args)

                    newEd = CodeEditor.InspectionEditor(newTree.root, newTree.rootToCursorAdd(),
                                                  zippedNodes=curEd.zippedNodes)

                    newEd.context = curEd.buffer
                    newEd.contextParent = curEd.id    # not really needed?
                    newEd.showValues = True
                    newEd.env = env
                    newEd.evalBuffer()

                    newWinTree = self.addWindow(newEd)
                    return self.updateList(
                        ('winTree', newWinTree),
                        ('winCmd', False))

            elif key.code() == iop.KEY_ESCAPE:
                return self.update('winCmd', False)

        elif key.char() == 'w' and key.lctrl():
            self.winCmd = True
            self.winTree.cursor.child.statusBar.displayMessage("Window Mode")
            print "windowing"

        elif key.char() == 's' and key.lctrl():
            self.writeImage()
            self.writeEditor()
            self.winTree.cursor.child.statusBar.displayMessage("Saving Image")
            print "saving"

        else:
            result = self.winTree.cursor.child.handleKeys(key, mouse)
            if result == 'ESC':
                self.writeImage()
                self.writeEditor()
                return False

            if result == 'UNDO':
                if self.hist.next:
                    self.ImageRoot = self.hist.next
                    self.hist = self.hist.next

            else:
                self.winTree = self.winTree.replaceAtCursor(result)

                if isinstance(result, Editors.TreeEditor) and result.syncWithRoot and \
                                                        self.ImageRoot != result.buffer.root:
                    self.ImageRoot = result.buffer.root
                    if result.updateUndo:
                        self.hist = cons(self.ImageRoot.child, self.hist)
                    #print "hist", self.hist.child.toPySexp()

            # need to sync all Editors to the newTree
            for i in self.winTree.root.child:
                if isinstance(i.child, Editors.TreeEditor) and i.child.syncWithRoot:
                    i.child = i.child.syncWithImage(self.ImageRoot)
            #functional: map(self.winTree.root.child .syncWithImage)

            return self
            #return self.update('winTree', self.winTree.replaceAtCursor(result))

        return self



