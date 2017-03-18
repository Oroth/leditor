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
    def __init__(self, editorList=None, x=0, y=0, width=iop.screenWidth(), height=iop.screenHeight()):
        self.posx, self.posy = x, y
        self.maxx, self.maxy = width, height
        self.editorList = editorList
        self.editorCmd = False

        self.editModeCL = cmdList.CmdList([
            (Key.c('l'), 'cmdEditorNext'),
            (Key.c('h'), 'cmdEditorPrev'),
            (Key.c('d'), 'cmdEditorDel'),
            (Key.c('>'), 'cmdInspectProcedureCall'),
            (Key.c('?'), 'cmdEditorDisplayHelp'),
            (Key.vk(iop.KEY_SPACE), 'cmdEditorRunProg'),
            (Key.vk(iop.KEY_ENTER), 'cmdNewEditorOnCursor')
        ])

        self.message = None

        self.persist = ['editorList']

    def setPosition(self, newPosx, newPosy, newMaxx, newMaxy):
        self.posx, self.posy = newPosx, newPosy
        self.maxx, self.maxy = newMaxx, newMaxy

    def draw(self, posx, posy, maxx, maxy, isActive):
        image = self.getEditor().draw(maxx, maxy, isActive)
        screen.printToScreen(image, posx, posy)

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

    def handleKeys(self, key, mouse):
        if self.editorCmd:
            result = self.editModeCL.process(key, self)
            if result:
                return result.updateList(
                    ('editorCmd', False),
                    ('message', None))

            if key.isPrintable():
                return self.updateList(
                    ('editorCmd', False),
                    ('message', None))
            else:
                return self

        elif key.char() == 'b' and key.ctrl():
            return self.updateList(
                ('editorCmd', True),
                ('message', "--Buffer Command--"))

        else:
            relativePositionMouse = mouse.getMouseWithRelativePosition(self.posx, self.posy)
            newEditor = self.getEditor().handleKeys(key, relativePositionMouse)
            return self.updateList(
                ('editorList', self.editorList.replaceAtCursor(newEditor)))



    def cmdNewScreenEditor(self):
        newEd = screenEditor.ScreenEditor(self.maxx, self.maxy)
        return self.update('editorList', self.editorList.appendAtCursor(newEd).curNext())


    def cmdNewFileEditor(self):
        path = './'
        fileList = fileEditor.dirToList(path)

        fileRoot = tn.createTNodeExpFromPyExp([fileList])
        fileBuffer = buffer.BufferSexp(fileRoot)
        newEd = fileEditor.FileEditor(fileBuffer)

        return self.update('editorList', self.editorList.appendAtCursor(newEd).curNext())


    def cmdNewPager(self):
        file, pathList = self.editorList.getCurrent().buffer.getNVSListAtCursor()
        print pathList
        pathText = '.\\' + '\\'.join(pathList)
        print pathText
        f = open(pathText, 'r')
        flist = f.readlines()
        newEd = pager.Pager(flist)
        f.close()

        return self.update('editorList', self.editorList.appendAtCursor(newEd).curNext())


    def cmdNewEditorOnCursor(self):
        newEd = self.getEditor().clone()
        newEd2 = newEd.update('buffer', newEd.buffer.viewToCursor())

        return self.update('editorList', self.editorList.appendAtCursor(newEd2).curNext())

    def cmdInspectProcedureCall(self):
        try:
            return self.cmdInspectProcedureCall2()
        except ex.UnappliedProcedureException:
            return self


    def cmdInspectProcedureCall2(self, proc=None, args=None):
        curEd = self.getEditor()
        procedure = self.getEditor().buffer.cursor if proc is None else proc

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
            newEd = CodeEditor.InspectionEditor(newTree.viewToCursor(),
                                          zippedNodes=curEd.zippedNodes)
            newEd.env = env

            return self.update('editorList', self.editorList.appendAtCursor(newEd).curNext())

        else:
            raise ex.UnappliedProcedureException(procValue)


    def cmdEditorDisplayHelp(self):
        curEd = self.getEditor()

        rootObj = curEd.getNodeValue(curEd.buffer.root)
        helpResult = rootObj.call(reader.Symbol('help')).call("all")
        newBuff = rootObj.updateVarSource('evalBuffer', helpResult)
        newEd = CodeEditor.CodeEditor(newBuff.viewToCursor())
        newEd.printingMode = 'vertical'
        newEd.evalCursorMode = 'disabled'

        return self.update('editorList', self.editorList.appendAtCursor(newEd).curNext())

    def cmdEditorRunProg(self):
        curEd = self.getEditor()
        imageRoot = curEd.buffer.root
        evalBuffer = buffer.BufferSexp(imageRoot, curEd.buffer.rootToCursorAdd())

        #procedure = self.getEditor().buffer.cursor
        #procValue = curEd.getNodeValue(procedure.child)
        #newTree, env = procValue.inspect(*args2)
        #newEd = CodeEditor.InspectionEditor(newTree.root, newTree.rootToCursorAdd())

        prog = CodeEditor.evalIOHandler(evalBuffer)
        newEditorList =  self.editorList.appendAtCursor(prog).curNext()

        return self.update('editorList', newEditorList)


    def cmdEditorNext(self):
        return self.update('editorList', self.editorList.curCycle())


    def cmdEditorPrev(self):
        return self.update('editorList', self.editorList.curCyclePrev())


    def cmdEditorDel(self):
        if self.editorList.length() > 1:
            return self.update('editorList', self.editorList.deleteAtCursor())
        else:
            return self



def syncWindowsToEditorList(winTree, newEditorList):
    return winTree.mapRoot(lambda node: node.syncWithEditorList(newEditorList))

def syncEditorsToImage(editorList, newImage):
    return editorList.mapRoot(lambda node: node.syncWithImage(newImage))


# class WinEditorList(buffer.SimpleBuffer):
#     def __init__(self, *args, **kargs):
#         super(WinEditorList, self).__init__(*args, **kargs)
#         self.persist = ['cursorAdd']


class WindowManager(fo.FuncObject):
    def __init__(self, imageFileName=None):
        if imageFileName == 'testIDImage':
            pyLoad = reader.loadFile(imageFileName)
            pyImage = [0]
            pyImage.append(pyLoad)
            imageRoot = tn.createTNodeExpFromPyNumberedExp(pyImage)

            self.ImageRoot = imageRoot
            self.hist = imageRoot
            startEditor = self.createListEdFromEditorSettings(imageRoot, "EditorSettings")
            self.editorList = buffer.SimpleBuffer.fromPyExp(startEditor, [0, 0])

            startWindow = Window(self.editorList, 0, 0, iop.screenWidth(), iop.screenHeight())
            self.winTree = buffer.SimpleBuffer.fromPyExp(startWindow, [0, 0])
            self.imageFileName = imageFileName

        else:
            self.ImageRoot = None
            self.hist = None
            self.editorList = None
            self.winTree = None
            self.imageFileName = None


        self.winCmd = False
        self.cmdBar = None
        self.message = None

        self.persist = ['editorList', 'winTree']

        self.wincl = cmdList.CmdList([
            (Key.c('j'), 'cmdWinDown'),
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
            (Key.c('w', ctrl=True), 'cmdStartWinMode'),
            (Key.c('s', ctrl=True), 'cmdSave'),
            (Key.c(':'), 'cmdStartCmdBar'),
            (Key.vk(iop.KEY_F9, alt=True), 'cmdScreenEditor'),
            (Key.vk(iop.KEY_F10, alt=True), 'cmdFileEditor'),
            (Key.vk(iop.KEY_F11, alt=True), 'cmdTextPager'),
        ])



    def getCmdBarEnv(self):
        return eval.Env.fromList([
            ('screenEditor', self.cmdScreenEditor),
            ('fileEditor', self.cmdFileEditor),
            ('save', self.cmdSave),
            ('winNext', self.cmdWinNext),
            ('split', self.cmdWinSplit),
            ('we', self.cmdWriteEditorSettingsTS),
            ('le', self.cmdLoadEditorSettings),
            ('wi', self.cmdWriteImageTS),
            ('li', self.cmdLoadLatestImage),
            ('wa', self.cmdWriteAll),
            ('la', self.cmdLoadLatestAll)
        ], eval.global_env)

    def test(self):
        print 'test'
        return 'tested'

    def quitWithoutSave(self):
        return False



    def getWinCount(self):
        return self.winTree.length()

    def getWMSettings(self):

        editorList = [e.getEditorSettings() for e in self.editorList.toPyExp()]

        return [reader.Symbol('WindowManager'),
                [reader.Symbol('EditorList'),
                 [reader.Symbol('cursor'), self.editorList.cursorAdd],
                 [reader.Symbol('root'), editorList]]]


    def getEditSexp(self):
        curWin = self.winTree.getCurrent()
        curEd = curWin.getEditor()
        return curEd.getEditorSettings()

    def curWin(self):
        return self.winTree.getCurrent()

    def writeEditor(self):
        print self.getWMSettings()
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

    def createListEdFromEditorSettings(self, root, filename):
        "returns an editor with settings as per the EditorSettings file"
        if os.path.isfile(filename):
            pyEditorLoad = reader.loadFile(filename)
            window = dict(pyEditorLoad[2][1:])
            edZipNode = dict(zip(window['zippedNodes'], [True]*len(window['zippedNodes'])))

            newBuffer = buffer.BufferSexp(root, window['address'], window['cursor'])

            listEd =  CodeEditor.CodeEditor(newBuffer, edZipNode)
            listEd.printingMode = window['printingMode']
            listEd.id = window['id']
        else:
            newBuffer = buffer.BufferSexp(root)
            listEd = CodeEditor.CodeEditor(newBuffer)

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

    def calculateMsg(self):
        if self.message:
            return self.message
        elif self.curWin().message:
            return self.curWin().message
        else:
            return ''


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
            msg = screen.stringToImage(self.calculateMsg(), maxX, 2)
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

    def loadNewImage(self, newImage):
        syncedEditorList = syncEditorsToImage(self.editorList, newImage)
        syncedWindowList = syncWindowsToEditorList(self.winTree, syncedEditorList)

        return self.updateList(
            ('ImageRoot', newImage),
            ('hist', newImage),
            ('editorList', syncedEditorList),
            ('winTree', syncedWindowList))


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

        result = eval.eval(buffer.BufferSexp(cmdBuffer.root), self.getCmdBarEnv())
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

        if key.isPrintable():
            return mouseResult.update('message', None).handleKeysMain(key, mouse)
        else:
            return mouseResult.handleKeysMain(key, mouse)

    def handleKeysMain(self, key, mouse):

        if self.winCmd and key.on():
            result = self.wincl.process(key, self)
            ret = result if result else self
            return ret.update('winCmd', False)

        mainResult = self.mainCl.process(key, self)
        if mainResult:
            return mainResult

        else:
            resultWin = self.curWin().handleKeys(key, mouse)
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
                    return self

            else:
                return self.replaceWindow(resultWin)



    def cmdWinDown(self):
        try:
            return self.update('winTree', self.winTree.curNext())
        except ValueError:
            return self

    def cmdWinUp(self):
        try:
            return self.update('winTree', self.winTree.curPrev())
        except ValueError:

            return self

    def cmdWinDel(self):
        if self.winTree.length() > 1:
            return self.update('winTree', self.winTree.deleteAtCursor())
        else:
            return self

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
        return self.addWindow(self.curWin().cmdEditorRunProg())

    def cmdOpenWinOnCursor(self):
        return self.addWindow(self.curWin().cmdNewEditorOnCursor())

    def cmdOpenWinInspectProc(self):
        try:
            return self.addWindow(self.curWin().cmdInspectProcedureCall2())
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
            ('winCmd', True))

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


    def cmdWriteAll(self):
        self.cmdWriteImageTS()
        self.cmdWriteEditorSettingsTS()
        return self.update('message', "Image and editor settings saved")


    def cmdWriteEditorSettingsTS(self):
        # bit of a hack, but basically change the persistence definition at save time as currently difficult to
        # retain with the way objects are set up.
        self.editorList.persist.append('root')
        self.winTree.persist.append('root')
        pyObj = self.serialise()
        text = reader.to_string(pyObj)
        reader.writeLatestFile('filefs/', 'EditorSettings', text)

        return self.update('message', "Saving Editor settings")

    def cmdWriteImageTS(self):
        pyObj = self.ImageRoot.child.toPyNumberedExp()
        text = reader.to_string(pyObj)
        reader.writeLatestFile('imagefs/', 'image', text)

        return self.update('message', "Saving Latest Image")

    def cmdLoadLatestAll(self):
        pyEditorLoad = reader.readLatestFile('filefs/')
        newWM = self.loadEditorSettingsFromPyExp(pyEditorLoad)

        return newWM.cmdLoadLatestImage()

    def cmdLoadLatestImage(self):
        pyImageLoad = reader.readLatestFile('imagefs/')

        pyImage = [0]
        pyImage.append(pyImageLoad)
        imageRoot = tn.createTNodeExpFromPyNumberedExp(pyImage)

        return self.loadNewImage(imageRoot)

    def loadEditorSettingsFromPyExp(self, pyExp):
        root = tn.TNode(tn.createTNodeExpFromPyExp(pyExp))
        newBuff = buffer.BufferSexp(root)
        return eval.eval(newBuff)


    def cmdLoadEditorSettings(self):
        pyEditorLoad = reader.readLatestFile('filefs/')
        newWM = self.loadEditorSettingsFromPyExp(pyEditorLoad)
        newWM2 = newWM.loadNewImage(self.ImageRoot)
        return newWM2

        # newEditor = CodeEditor.CodeEditor(newBuff).update('_isRootImageEditor', False)
        # newWin = self.curWin().addEditor(newEditor)
        # return self.addWindow(newWin)

        #newEditor = self.createListEdFromEditorSettings(self.ImageRoot, latestFile)
