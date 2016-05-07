__author__ = 'chephren'
import tn
import buffer
import reader
import screen
import CodeEditor
import os.path
import iop
import funobj as fo
import eval
from tn import cons


class Window(fo.FuncObject):
    def __init__(self, editorList, x=0, y=0, width=iop.screenWidth(), height=iop.screenHeight()):
        self.posx, self.posy = x, y
        self.maxx, self.maxy = width, height
        self.editorList = editorList
        self.editorCmd = False

    def setPosition(self, newPosx, newPosy, newMaxx, newMaxy):
        self.posx, self.posy = newPosx, newPosy
        self.maxx, self.maxy = newMaxx, newMaxy

    def draw(self, posx, posy, maxx, maxy, isActive):
        image = self.getEditor().draw(maxx, maxy, isActive)
        screen.printToScreen(image, posx, posy)

    def cmdNewEditorOnCursor(self):
        newEd = CodeEditor.CodeEditor(self.getEditor().buffer.root, self.getEditor().buffer.rootToCursorAdd(),
                                      zippedNodes=self.getEditor().zippedNodes)

        return self.updateList(
            ('editorList', self.editorList.appendAtCursor(newEd).curNext()),
            ('editorCmd', False))

    def cmdInspectProcedureCall(self):
        return self.cmdInspectProcedureCall2(self.getEditor().buffer.cursor)

    def cmdInspectProcedureCall2(self, procedure):
        curEd = self.getEditor()
        #curNode = curEd.buffer.cursor

        if procedure.isSubNode():
            args = [curEd.nodeValues[node] for node in procedure.child][1:]
            newTree, env = curEd.nodeValues[procedure.child].inspect(*args)
            newEd = CodeEditor.InspectionEditor(newTree.root, newTree.rootToCursorAdd(),
                                          zippedNodes=curEd.zippedNodes)
            newEd.env = env

            return self.updateList(
                ('editorList', self.editorList.appendAtCursor(newEd).curNext()),
                ('editorCmd', False))


    def cmdDisplayHelp(self):
        curEd = self.getEditor()

        rootObj = curEd.getNodeValue(curEd.buffer.root)
        helpResult = rootObj.call(reader.Symbol('help')).call("all")
        newBuff = rootObj.updateVarSource('evalBuffer', helpResult)
        newEd = CodeEditor.CodeEditor(newBuff.root, newBuff.cursorAdd)
        newEd.printingMode = 'vertical'

        return self.updateList(
            ('editorList', self.editorList.appendAtCursor(newEd).curNext()),
            ('editorCmd', False))


    def handleKeys(self, key, mouse):
        curEd = self.getEditor()
        if self.editorCmd:
            if key.code() == iop.KEY_ENTER:
                return self.cmdNewEditorOnCursor()

            # change the current window to the next editor:
            elif key.char() == 'l':
                return self.updateList(
                    ('editorList', self.editorList.curCycle()),
                    ('editorCmd', False))

            elif key.char() == 'h':
                return self.updateList(
                    ('editorList', self.editorList.curCyclePrev()),
                    ('editorCmd', False))

            elif key.char() == '>':
                return self.cmdInspectProcedureCall()

            elif key.char() == '?':
                return self.cmdDisplayHelp()

            if key.isPrintable():
                return self.update('editorCmd', False)
            else:
                return self

        elif key.char() == 'b' and key.lctrl():
            curEd.statusBar.updateMessage("Editor List Command")
            print 'edit cmd'
            return self.update('editorCmd', True)

        else:
            relativePositionMouse = mouse.getMouseWithRelativePosition(self.posx, self.posy)
            newEditor = self.getEditor().handleKeys(key, relativePositionMouse)
            return self.updateList(
                ('editorList', self.editorList.replaceAtCursor(newEditor)))

    def getEditor(self):
        return self.editorList.cursor.child

    def addEditor(self, newEd):
        newEditorList = self.editorList.appendAtCursor(newEd).curNext()
        return self.update('editorList', newEditorList)

    def nextEditor(self):
        return self.update('editorList', self.editorList.curCycle())

    def syncWithEditorList(self, newEditorList):
        if newEditorList.root != self.editorList.root:
            return self.update('editorList', self.editorList.syncToNewRoot(newEditorList.root))
        else:
            return self


def syncWindowsToEditorList(winTree, newEditorList):
    return winTree.mapRoot(lambda node: node.syncWithEditorList(newEditorList))

def syncEditorsToImage(editorList, newImage):
    return editorList.mapRoot(lambda node: node.syncWithImage(newImage))


class WindowManager(fo.FuncObject):
    def __init__(self, imageFileName):
        pyLoad = reader.loadFile(imageFileName)
        pyImage = [0]
        pyImage.append(pyLoad)
        imageRoot = tn.createTNodeExpFromPyNumberedExp(pyImage)

        self.ImageRoot = imageRoot
        self.hist = imageRoot
        startEditor = self.createListEdFromEditorSettings(imageRoot)
        self.editorList = buffer.SimpleBuffer.fromPyExp(startEditor, [0, 0])

        startWindow = Window(self.editorList, 0, 0, iop.screenWidth(), iop.screenHeight())
        self.winTree = buffer.SimpleBuffer.fromPyExp(startWindow, [0, 0])
        self.imageFileName = imageFileName
        self.winCmd = False

    def getWinCount(self):
        return self.winTree.length()

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

    # calculates and sets posx, posy, maxx, maxy for all windows trying to allocate available screen real estate
    # as equally as possible
    def calculateWindowPositions(self):
        maxX = iop.screenWidth()
        curY = 0
        wins = self.winTree.length()

        screenForWins = iop.screenHeight() #- numberOfBorders
        minYStep = screenForWins / wins
        leftover = screenForWins % wins

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
        wins = self.winTree.length()

        screenForWins = iop.screenHeight()
        minYStep = screenForWins / wins
        leftover = screenForWins % wins

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

    # not sure if this is conceptually the right way to go about doing this, but once we've collect all the
    # updates in a newWindowList then this function unpicks it all to get at the various level of changes:
    # newWindow, new editor, new image
    # and then syncs the various parts
    def integrateUpdatedWindowList(self, newWinList):
        newWin = newWinList.cursor.child
        newEditorList = newWin.editorList
        newEditor = newEditorList.cursor.child
        newImage = newEditor.buffer.root

        if newEditor.syncWithRoot and self.ImageRoot != newImage:
            self.ImageRoot = newImage
            if newEditor.updateUndo:
                self.hist = cons(self.ImageRoot.child, self.hist)

        syncedEditorList = syncEditorsToImage(newEditorList, newImage)

        return self.updateList(
            ('editorList', syncedEditorList),
            ('winTree', syncWindowsToEditorList(newWinList, syncedEditorList)))


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
                if self.winTree.length() > 1:
                    return self.updateList(
                        ('winTree', self.winTree.deleteAtCursor()),
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
                resultWin = curWin.cmdNewEditorOnCursor()
                newWinList = self.winTree.appendAtCursor(resultWin).curNext()
                self.winCmd = False
                return self.integrateUpdatedWindowList(newWinList)

            elif key.char() == '>':
                resultWin = curWin.cmdInspectProcedureCall()
                newWinList = self.winTree.appendAtCursor(resultWin).curNext()
                self.winCmd = False
                return self.integrateUpdatedWindowList(newWinList)

            elif key.code() == iop.KEY_ESCAPE:
                return self.update('winCmd', False)

            else:
                return self

        elif key.char() == 'w' and key.lctrl():
            self.winCmd = True
            curEd.statusBar.updateMessage("Window Mode")
            print "windowing"
            return self

        elif key.char() == 's' and key.lctrl():
            self.writeImage()
            self.writeEditor()
            curEd.statusBar.updateMessage("Saving Image")
            print "saving"
            return self

        else:
            resultWin = curWin.handleKeys(key, mouse)

            resultEd = resultWin.getEditor()
            if resultEd == 'ESC':
                self.writeImage()
                self.writeEditor()
                return False

            elif resultEd == 'UNDO':
                if self.hist.next:
                    self.ImageRoot = self.hist.next
                    self.hist = self.hist.next

                    syncedEditorList = syncEditorsToImage(self.editorList, self.ImageRoot)

                    return self.updateList(
                        ('editorList', syncedEditorList),
                        ('winTree', syncWindowsToEditorList(self.winTree, syncedEditorList)))

            else:
                newWinList = self.winTree.replaceAtCursor(resultWin)
                newWinManager = self.integrateUpdatedWindowList(newWinList)
                return newWinManager


        return self
