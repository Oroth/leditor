__author__ = 'chephren'
import tn
import buffer
import reader
import screen
import CodeEditor
import screenEditor
import fileEditor
from cmdBar import CmdBar
import os.path
import pager
import iop
from iop import Key
import funobj as fo
import eval
import leditor_exceptions as ex
from tn import cons
import cmdList


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

    def cmdNewScreenEditor(self):
        newEd = screenEditor.ScreenEditor(self.maxx, self.maxy)

        return self.updateList(
            ('editorList', self.editorList.appendAtCursor(newEd).curNext()),
            ('editorCmd', False))

    def cmdNewFileEditor(self):
        path = './'
        fileList = fileEditor.dirToList(path)
        # fileList =  \
        #     [
        #         [reader.Symbol('file1'),
        #          [reader.Symbol('file2'), reader.Symbol('file3')],
        #          reader.Symbol('file4')
        #          ]]
        #fileList = [map(reader.Symbol, listdir(path))]
        fileRoot = tn.createTNodeExpFromPyExp([fileList])
        newEd = fileEditor.FileEditor(fileRoot)

        return self.updateList(
            ('editorList', self.editorList.appendAtCursor(newEd).curNext()),
            ('editorCmd', False))

    def cmdNewPager(self):
        text = "some example text - awawy awyay"
        file, pathList = self.editorList.getCurrent().buffer.getNVSListAtCursor()
        print pathList
        pathText = '.\\' + '\\'.join(pathList)
        print pathText
        f = open(pathText, 'r')
        flist = f.readlines()
        newEd = pager.Pager(flist)
        f.close()

        return self.updateList(
            ('editorList', self.editorList.appendAtCursor(newEd).curNext()),
            ('editorCmd', False))

    #def cmdNewEditor(self):

    def cmdNewEditorOnCursor(self):
        newEd = CodeEditor.CodeEditor(
            root = self.getEditor().buffer.root,
            rootCursorAdd = self.getEditor().buffer.rootToCursorAdd(),
            zippedNodes = self.getEditor().zippedNodes)

        return self.updateList(
            ('editorList', self.editorList.appendAtCursor(newEd).curNext()),
            ('editorCmd', False))

    def cmdInspectProcedureCall(self, args=None):
        return self.cmdInspectProcedureCall2(self.getEditor().buffer.cursor, args)

    def cmdInspectProcedureCall2(self, procedure, args=None):
        curEd = self.getEditor()
        if args is None:
            procValue = curEd.getNodeValue(procedure.child)
        else:
            procValue = curEd.getNodeValue(procedure)

        if procedure.isSubNode() and hasattr(procValue, 'inspect'):
            if args is None:
                args2 = [curEd.getNodeValue(node) for node in procedure.child][1:]
            else:
                args2 = args
            newTree, env = procValue.inspect(*args2)
            newEd = CodeEditor.InspectionEditor(newTree.root, newTree.rootToCursorAdd(),
                                          zippedNodes=curEd.zippedNodes)
            newEd.env = env

            return self.updateList(
                ('editorList', self.editorList.appendAtCursor(newEd).curNext()),
                ('editorCmd', False))

        else:
            raise ex.UnappliedProcedureException(procValue)


    def cmdDisplayHelp(self):
        curEd = self.getEditor()

        rootObj = curEd.getNodeValue(curEd.buffer.root)
        helpResult = rootObj.call(reader.Symbol('help')).call("all")
        newBuff = rootObj.updateVarSource('evalBuffer', helpResult)
        newEd = CodeEditor.CodeEditor(newBuff.root, newBuff.cursorAdd)
        newEd.printingMode = 'vertical'
        newEd.evalCursorMode = 'disabled'

        return self.updateList(
            ('editorList', self.editorList.appendAtCursor(newEd).curNext()),
            ('editorCmd', False))

    def cmdRunProg(self):
        curEd = self.getEditor()
        imageRoot = curEd.buffer.root
        evalBuffer = buffer.BufferSexp(imageRoot, curEd.buffer.rootToCursorAdd())

        #procedure = self.getEditor().buffer.cursor
        #procValue = curEd.getNodeValue(procedure.child)
        #newTree, env = procValue.inspect(*args2)
        #newEd = CodeEditor.InspectionEditor(newTree.root, newTree.rootToCursorAdd())


        prog = CodeEditor.evalIOHandler(evalBuffer)
        newEditorList =  self.editorList.appendAtCursor(prog).curNext()

        return self.updateList(
            ('editorList', newEditorList),
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

            elif key.char() == 'd':
                if self.editorList.length() > 1:
                    return self.updateList(
                        ('editorList', self.editorList.deleteAtCursor()),
                        ('editorCmd', False))

            elif key.char() == '>':
                try:
                    return self.cmdInspectProcedureCall()
                except ex.UnappliedProcedureException:
                    return self.update('editorCmd', False)

            elif key.char() == '?':
                return self.cmdDisplayHelp()

            elif key.code() == iop.KEY_SPACE:
                return self.cmdRunProg()


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

        self.cmdBar = None
        self.message = ''

        self.wincl = cmdList.CmdList(
            [(Key.c('j'), 'cmdWinDown'),
             (Key.c('k'), 'cmdWinUp'),
             (Key.c('d'), 'cmdWinDel'),
             (Key.c('u'), 'cmdWinUndo'),
             (Key.c('w'), 'cmdWinNext'),
             (Key.c('>'), 'cmdOpenWinInspectProc'),
             (Key.vk(iop.KEY_SPACE), 'cmdRunProg'),
             (Key.vk(iop.KEY_ENTER), 'cmdOpenWinOnCursor'),
             #(Key.vk(iop.KEY_F5), 'cmdWinUp'),
             (Key.vk(iop.KEY_F10), 'cmdToggleFullScreen'),
             (Key.vk(iop.KEY_ESCAPE), 'cmdExitWinMode')
             ])

        self.mainCl = cmdList.CmdList([
            (Key.c('w', lctrl=True), 'cmdStartWinMode'),
            (Key.c('s', lctrl=True), 'cmdSave'),
            (Key.c(':'), 'cmdStartCmdBar'),
            (Key.vk(iop.KEY_F9, lalt=True), 'cmdScreenEditor'),
            (Key.vk(iop.KEY_F10, lalt=True), 'cmdFileEditor'),
            (Key.vk(iop.KEY_F11, lalt=True), 'cmdTextPager'),

        ])

    def test(self):
        print 'test'
        return 'tested'

    def quitWithoutSave(self):
        return False



    def getWinCount(self):
        return self.winTree.length()

    def getEditSexp(self):
        curWin = self.winTree.getCurrent()
        curEd = curWin.getEditor()
        return curEd.getEditorSettings()

    def curWin(self):
        return self.winTree.getCurrent()



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

    def createListEdFromEditorSettings(self, root):
        "returns an editor with settings as per the EditorSettings file"
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

        screenForWins = iop.screenHeight() - 1 #- numberOfBorders
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

        screenForWins = iop.screenHeight() - 1  # leave space for cmd bar
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

        cmdPosy = screenForWins
        if self.cmdBar:
            cmdImage = self.cmdBar.draw(maxX, 2, isActive=True)
            screen.printToScreen(cmdImage, 0, cmdPosy)
        else:
            #blank = screen.createBlank(maxX, 2)
            #screen.overlayLinesOnImage(blank, 0)
            msg = screen.stringToImage(self.message, maxX, 2)
            screen.printToScreen(msg, 0, cmdPosy)


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

        if newEditor.isRootImageEditor():
            newImage = newEditor.buffer.root

            if newEditor.syncWithRoot and self.ImageRoot != newImage:
                self.ImageRoot = newImage
                if newEditor.updateUndo:
                    self.hist = cons(self.ImageRoot.child, self.hist)

            syncedEditorList = syncEditorsToImage(newEditorList, newImage)

        else:
            syncedEditorList = newEditorList

        return self.updateList(
            ('editorList', syncedEditorList),
            ('winTree', syncWindowsToEditorList(newWinList, syncedEditorList)))

    def addWindow(self, newWindow):
        newWinList = self.winTree.appendAtCursor(newWindow).curNext()
        return self.integrateUpdatedWindowList(newWinList)

    def replaceWindow(self, newWindow):
        newWinList = self.winTree.replaceAtCursor(newWindow)
        return self.integrateUpdatedWindowList(newWinList)




    def evalCmdBarResult(self, cmdBuffer):

        # Maybe should get done in the actual cmdbar
        cmd = cmdBuffer.toPyExp()
        print cmd

        if cmd[0] in ('q', 'quit'):
            return False

        env = eval.Env(('write', 'test', 'split'), (self.cmdSave, self.test, self.cmdWinSplit), eval.global_env)
        result = eval.eval(buffer.BufferSexp(cmdBuffer.root), env)
        print result

        if isinstance(result, WindowManager):
            return result.update('cmdBar', None)

        self.message = reader.to_string(result)

        return self.updateList(
            ('cmdBar', None))

    def handleCmdBarInput(self, key, mouse):
        cmdResult = self.cmdBar.handleKeys(key, mouse)
        if cmdResult.returnState == 'ESCAPE':
            return self.update('cmdBar', None)

        elif cmdResult.returnState == 'PRINT':
            return self.evalCmdBarResult(cmdResult.buffer)

        else:
            return self.update('cmdBar', cmdResult)

    def handleKeys(self, key, mouse):

        if self.cmdBar:
            return self.handleCmdBarInput(key, mouse)

        mouseResult = self

        if mouse.lbuttonPressed():
            windowClicked, windowAddress = self.matchWindowToClick(mouse.x(), mouse.y())
            if windowClicked != self.winTree.cursor:
                newWinTree = self.winTree.newCursorAdd(windowAddress)
                mouseResult = self.update('winTree', newWinTree)
                #self.winTree = new # imperative at the moment to allow simultaenously switching and selecting
                # an expression

        if key.isPrintable():
            return mouseResult.handleKeysMain(key, mouse).update('message', '')
        else:
            return mouseResult.handleKeysMain(key, mouse)


    def handleKeysMain(self, key, mouse):

        curWin = self.winTree.getCurrent()
        curEd = curWin.getEditor()

        if self.winCmd:
            result = self.wincl.process(key, self)
            return result if result else self

        mainResult = self.mainCl.process(key, self)

        if mainResult:
            return mainResult

        else:
            resultWin = curWin.handleKeys(key, mouse)

            resultEd = resultWin.getEditor()

            if resultEd == 'UNDO':
                if self.hist.next:
                    self.hist = self.hist.next
                    self.ImageRoot = tn.TNode(self.hist.child)


                    syncedEditorList = syncEditorsToImage(self.editorList, self.ImageRoot)

                    return self.updateList(
                        ('editorList', syncedEditorList),
                        ('winTree', syncWindowsToEditorList(self.winTree, syncedEditorList)))

            else:
                return self.replaceWindow(resultWin)


        return self

    def cmdWinDown(self):
        try:
            return self.updateList(
                ('winTree', self.winTree.curNext()),
                ('winCmd', False))
        except ValueError: return self

    def cmdWinUp(self):
        try:
            return self.updateList(
                ('winTree', self.winTree.curPrev()),
                ('winCmd', False))
        except ValueError: return self

    def cmdWinDel(self):
        if self.winTree.length() > 1:
            return self.updateList(
                ('winTree', self.winTree.deleteAtCursor()),
                ('winCmd', False))

    def cmdWinSplit(self):
        curWin = self.winTree.getCurrent()
        newEd = curWin.getEditor().clone()
        newWin = curWin.addEditor(newEd)
        return self.addWindow(newWin)

    # Does this even work?
    def cmdWinUndo(self):
        if self.hist.next:
            return self.updateList(
                ('ImageRoot', self.hist.next),
                ('hist', self.hist.next))

    def cmdWinNext(self):
        return self.updateList(
            ('winTree', self.winTree.curCycle()),
            ('winCmd', False))

    def cmdRunProg(self):
        self.winCmd = False
        return self.addWindow(self.curWin().cmdRunProg())

    def cmdOpenWinOnCursor(self):
        self.winCmd = False
        return self.addWindow(self.curWin().cmdNewEditorOnCursor())

    def cmdOpenWinInspectProc(self):
        self.winCmd = False
        try:
            return self.addWindow(self.curWin().cmdInspectProcedureCall())
        except ex.UnappliedProcedureException:
            return self

    # elif key.code() == iop.KEY_F5:
    #     self.winCmd = False
    #     #return self.replaceWindow(curWin.cmdRunProg())
    #     return self.addWindow(curWin.cmdInspectProcedureCall(["abc"]))

    def cmdExitWinMode(self):
        return self.update('winCmd', False)

    def cmdToggleFullscreen(self):
        iop.toggleFullScreen()
        return self.update('winCmd', False)

    def cmdSave(self):
        self.writeImage()
        self.writeEditor()
        print "saving"
        return self.update('message', "Saving Image")

    def cmdStartWinMode(self):
        return self.updateList(
            ('message', 'Window Mode'),
            ('winCmd', True)
        )

    def cmdStartCmdBar(self):
        return self.update('cmdBar', CmdBar())

    def cmdScreenEditor(self):
        print "changing to screen mode"
        return self.replaceWindow(self.curWin().cmdNewScreenEditor())

    def cmdFileEditor(self):
        print "changing to file edit mode"
        return self.replaceWindow(self.curWin().cmdNewFileEditor())

    def cmdTextPager(self):
        print "changing to text paging mode"
        return self.replaceWindow(self.curWin().cmdNewPager())