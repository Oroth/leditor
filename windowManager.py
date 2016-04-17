__author__ = 'chephren'
import tn
import buffer
import reader
import screen
import CodeEditor
import os.path
import iop
import funobj as fo
from tn import cons


class Window(fo.FuncObject):
    def __init__(self, editor, x=0, y=0, width=iop.screenWidth(), height=iop.screenHeight()):
        self.posx, self.posy = x, y
        self.maxx, self.maxy = width, height
        self.editor = editor

    def setPosition(self, newPosx, newPosy, newMaxx, newMaxy):
        self.posx, self.posy = newPosx, newPosy
        self.maxx, self.maxy = newMaxx, newMaxy

    def draw(self, posx, posy, maxx, maxy, isActive):
        image = self.editor.draw(maxx, maxy, isActive)
        screen.printToScreen(image, posx, posy)

    def handleKeys(self, key, mouse):
        relativePositionMouse = mouse.getMouseWithRelativePosition(self.posx, self.posy)
        return self.update('editor', self.editor.handleKeys(key, relativePositionMouse))

    def getEditor(self):
        return self.editor



class WindowManager(fo.FuncObject):
    def __init__(self, imageFileName):
        pyLoad = reader.loadFile(imageFileName)
        pyImage = [0]
        pyImage.append(pyLoad)
        imageRoot = tn.createTNodeExpFromPyNumberedExp(pyImage)

        self.ImageRoot = imageRoot
        self.hist = imageRoot
        startEditor = self.createListEdFromEditorSettings(imageRoot)
        self.editorList = tn.TNode(startEditor)
        startEditorBuffer = buffer.SimpleBuffer(self.editorList, [0, 0])

        startWindow = Window(startEditor, 0, 0, iop.screenWidth(), iop.screenHeight())
        self.winTree = buffer.SimpleBuffer.fromPyExp(startWindow, [0, 0])
        self.imageFileName = imageFileName
        self.winCmd = False
        self.wins = 1


    def getEditSexp(self):
        curWin = self.winTree.getCurrent()
        curEd = curWin.getEditor()
        return curEd.getEditorSettings()

    def writeEditor(self):
        pyObj = self.getEditSexp()
        text = reader.to_string(pyObj)
        f = open('EditorSettings', 'w')
        f.write(text)
        f.close()

    def writeImage(self):
        pyObj = self.ImageRoot.child.toPyNumberedExp()
        text = reader.to_string(pyObj)
        f = open(self.imageFileName, 'w')
        f.write(text)
        f.close()

    # returns an editor with settings as per the EditorSettings file
    def createListEdFromEditorSettings(self, root):
        if os.path.isfile("EditorSettings"):
            pyEditorLoad = reader.loadFile("EditorSettings")
            window = dict(pyEditorLoad[2][1:])
            edZipNode = dict(zip(window['zippedNodes'], [True]*len(window['zippedNodes'])))

            listEd = CodeEditor.CodeEditor(root, window['address'], window['cursor'], edZipNode)
            listEd.printingMode = window['printingMode']
            listEd.id = window['id']
        else:
            listEd =CodeEditor.CodeEditor(root)

        return listEd


    def addWindow(self, newFunc):
        self.wins += 1
        newWin = Window(newFunc)
        newWinTree = self.winTree.appendAtCursor(newWin).curNext()
        return newWinTree

    # calculates and sets posx, posy, maxx, maxy for all windows trying to allocate available screen real estate
    # as equally as possible
    def calculateWindowPositions(self):
        maxX = iop.screenWidth()
        curY = 0

        screenForWins = iop.screenHeight() #- numberOfBorders
        minYStep = screenForWins / self.wins
        leftover = screenForWins % self.wins

        for winNode in self.winTree.first():
            if leftover > 0:
                curYStep = minYStep + 1
                leftover -= 1
            else:
                curYStep = minYStep

            winNode.child.setPosition(0, curY, maxX, curYStep)
            curY += curYStep


    def draw(self):
        self.calculateWindowPositions()

        maxX = iop.screenWidth()
        curY = 0
        screenForWins = iop.screenHeight()
        minYStep = screenForWins / self.wins
        leftover = screenForWins % self.wins

        for winNode in self.winTree.first():
            window = winNode.child
            if leftover > 0:
                curYStep = minYStep + 1
                leftover -= 1
            else:
                curYStep = minYStep

            if winNode == self.winTree.cursor:
                window.draw(0, curY, maxX, curYStep, True)
            else: window.draw(0, curY, maxX, curYStep,False)
            curY += curYStep


    def matchWindowToClick(self, x, y):
        winAdd = [0, 0]
        for winNode in self.winTree.first():
            win = winNode.child
            if win.posx <= x < win.posx + win.maxx and win.posy <= y < win.posy + win.maxy:
                return winNode, winAdd
            winAdd[-1] += 1


    def handleKeys(self, key, mouse):
        if mouse.lbuttonPressed():
            windowClicked, windowAddress = self.matchWindowToClick(mouse.x(), mouse.y())
            if windowClicked != self.winTree.cursor:
                new = self.winTree.newCursorAdd(windowAddress)
                self.winTree = new # imperative at the moment to allow simultaenously switching and selecting
                # an expression

        curWin = self.winTree.getCurrent()
        curEd = curWin.getEditor()

        if self.winCmd:

            if key.char() == 'b':
                newEd = CodeEditor.CodeEditor(self.ImageRoot, [0], curEd.buffer.rootToCursorAdd(),
                                              zippedNodes=curEd.zippedNodes)
                #newWinList = self.editorList.appendAtCursor(newEd).curNext()

                newWinList = curWin.appendAtCursor(newEd).curNext()
                newWinTree = self.winTree.replaceAtCursor(newEd)
                return self.updateList(
                    ('winTree', newWinTree),
                    ('winList', newWinList),
                    ('winCmd', False))

            # change the current window to the next editor:
            if key.char() == 'n':
                newWinList = self.editorList.curCycle()
                nextEd = newWinList.cursor.child
                newWinTree = self.winTree.replaceAtCursor(nextEd)

                return self.updateList(
                    ('winList', newWinList),
                    ('winTree', newWinTree),
                    ('winCmd', False))

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
                return self.updateList(
                    ('winTree', self.winTree.curCycle()),
                    ('winCmd', False))

            # run a function like a program
            elif key.code() == iop.KEY_SPACE:
                evalBuffer = buffer.BufferSexp(self.ImageRoot, curEd.buffer.rootToCursorAdd())
                prog = CodeEditor.evalIOHandler(evalBuffer)
                newWinTree = self.addWindow(prog)

                newWM = self.updateList(
                    ('winTree', newWinTree),
                    ('winCmd', False))

                return newWM

            elif key.code() == iop.KEY_ENTER:
                newEd = CodeEditor.CodeEditor(self.ImageRoot, curEd.buffer.rootToCursorAdd(),
                                             zippedNodes=curEd.zippedNodes)
                newWinTree = self.addWindow(newEd)

                return self.updateList(
                    ('winTree', newWinTree),
                    ('winCmd', False))

            elif key.char() == '>':
                curNode = curEd.buffer.cursor

                if curNode.isSubNode():
                    args = [curEd.nodeValues[node] for node in curNode.child][1:]
                    newTree, env = curEd.nodeValues[curNode.child].inspect(*args)
                    newEd = CodeEditor.InspectionEditor(newTree.root, newTree.rootToCursorAdd(),
                                                  zippedNodes=curEd.zippedNodes)
                    newEd.env = env

                    newWinTree = self.addWindow(newEd)
                    return self.updateList(
                        ('winTree', newWinTree),
                        ('winCmd', False))

            elif key.code() == iop.KEY_ESCAPE:
                return self.update('winCmd', False)

        elif key.char() == 'w' and key.lctrl():
            self.winCmd = True
            curEd.statusBar.updateMessage("Window Mode")
            print "windowing"

        elif key.char() == 's' and key.lctrl():
            self.writeImage()
            self.writeEditor()
            curEd.statusBar.updateMessage("Saving Image")
            print "saving"

        else:
            resultWin = curWin.handleKeys(key, mouse)
            resultEd = resultWin.getEditor()
            if resultEd == 'ESC':
                self.writeImage()
                self.writeEditor()
                return False

            if resultEd == 'UNDO':
                if self.hist.next:
                    self.ImageRoot = self.hist.next
                    self.hist = self.hist.next

            else:
                self.winTree = self.winTree.replaceAtCursor(resultWin)

                if resultEd.syncWithRoot and self.ImageRoot != resultEd.buffer.root:
                    self.ImageRoot = resultEd.buffer.root
                    if resultEd.updateUndo:
                        self.hist = cons(self.ImageRoot.child, self.hist)
                    #print "hist", self.hist.child.toPySexp()

            # need to sync all Editors to the newTree
            for winNode in self.winTree.first():
                win = winNode.child
                if win.editor.syncWithRoot:
                    win.editor = win.editor.syncWithImage(self.ImageRoot)
            #functional: map(self.winTree.root.child .syncWithImage)

            return self
            #return self.update('winTree', self.winTree.replaceAtCursor(result))

        return self



