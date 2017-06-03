import os.path

import funobj as fo
import tn, buffer, CodeEditor
import iop, screen, window
import reader, eval, leditor_exceptions as ex
import cmdList
from cmdBar import CmdBar
from iop import Key
import repl, simpleFileEditor as sfe


def syncWindowsToEditorList(windowList, newEditorList):
    return windowList.mapRoot(lambda node: node.syncWithEditorList(newEditorList))

def syncEditorsToImage(editorList, newImage):
    return editorList.mapRoot(lambda node: node.syncWithImage(newImage))


class WindowManager(fo.FuncObject):
    def __init__(self, app=None, imageFileName=None):
        if imageFileName == 'testIDImage':
            pyLoad = reader.loadFile(imageFileName)
            pyImage = [0]
            pyImage.append(pyLoad)
            imageRoot = tn.createTNodeExpFromPyNumberedExp(pyImage)

            self.ImageRoot = imageRoot
            self.hist = imageRoot
            startEditor = self.createListEdFromEditorSettings(imageRoot, "EditorSettings")
            self.editorList = buffer.SimpleBuffer.fromPyExp(startEditor, [0, 0])

            startWindow = window.StdWindow(self.editorList, 0, 0, app.screenCols, app.screenHeight)
            self.windowList = buffer.SimpleBuffer.fromPyExp(startWindow, [0, 0])
            self.imageFileName = imageFileName

        else:
            self.ImageRoot = None
            self.hist = None
            self.editorList = None
            self.windowList = None
            self.imageFileName = None

        self.app = app
        self.winCmd = False
        self.cmdBar = None
        self.message = None
        self.persist = ['editorList', 'windowList']
        self.track = None

        self.wincl = cmdList.CmdList([
            (Key.c('j'), cmdWinDown),
            (Key.c('k'), cmdWinUp),
            (Key.c('d'), cmdWinDel),
            #(Key.c('u'), cmdWinUndo),
            (Key.c('w'), cmdWinNext),
            (Key.c('>'), cmdOpenWinInspectProc),
            (Key.vk(iop.KEY_SPACE), cmdRunProg),
            (Key.vk(iop.KEY_ENTER), cmdOpenWinOnCursor),
            (Key.vk(iop.KEY_F10), cmdToggleFullscreen),
            (Key.vk(iop.KEY_ESCAPE), cmdExitWinMode)
        ])

        self.mainCl = cmdList.CmdList([
            (Key.c('w', ctrl=True), cmdStartWinMode),
            (Key.c('s', ctrl=True), 'cmdSave'),
            (Key.c(':'), cmdStartCmdBar),
            (Key.vk(iop.KEY_F5), cmdPlayMedia),
            (Key.vk(iop.KEY_F9, alt=True), cmdScreenEditor),
            (Key.vk(iop.KEY_F11, alt=True), cmdTextPager),
        ])



    def getCmdBarEnv(self):
        return eval.Env.fromList([
            ('screenEditor', lambda:cmdScreenEditor(self)),
            ('sfe', lambda:cmdSFE(self)),
            ('repl', lambda:cmdReplEditor(self)),
            ('save', lambda:cmdSave(self)),
            ('winNext', lambda:cmdWinNext(self)),
            ('split', lambda:cmdWinSplit(self)),
            ('music', lambda:cmdMusic(self)),
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


    def updateSound(self):
        try:
            track = self.activeWindow.editor.track
            if track != self.track:
                self.track = track
                self.app.playMedia(track)
        except AttributeError:
            return self


    def getWinCount(self):
        return self.windowList.length()

    def getWMSettings(self):
        editorList = [e.getEditorSettings() for e in self.editorList.toPyExp()]
        return [reader.Symbol('WindowManager'),
                [reader.Symbol('EditorList'),
                 [reader.Symbol('cursor'), self.editorList.cursorAdd],
                 [reader.Symbol('root'), editorList]]]


    def getEditSexp(self):
        curWin = self.windowList.getCurrent()
        curEd = curWin.editor
        return curEd.getEditorSettings()

    @property
    def activeWindow(self):
        return self.windowList.getCurrent()

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
        maxX = self.app.screenCols
        curY = 0
        wins = self.windowList.length()

        screenForWins = self.app.screenRows - 1 #- numberOfBorders
        minYStep = screenForWins / wins
        leftover = screenForWins % wins


        editorTNodeList = self.editorList.root
        windowTNodeList = self.windowList.root

        for winPos, winNode in enumerate(self.windowList.first()):
            if leftover > 0:
                curYStep = minYStep + 1
                leftover -= 1
            else:
                curYStep = minYStep

            newWindow = winNode.child.setPosition(0, curY, maxX, curYStep)
            windowTNodeList = tn.replaceAdd(windowTNodeList, [0, winPos], newWindow)
            curY += curYStep

            editBuffer = winNode.child.editorList
            editor = editBuffer.cursor.child
            editorAdd = editBuffer.cursorAdd
            newEditor = editor.updateSize(maxX, curYStep)

            editorTNodeList = tn.replaceAdd(editorTNodeList, editorAdd, newEditor)

        newwindowList = self.windowList.syncToNewRoot(windowTNodeList)
        self.editorList = buffer.SimpleBuffer(editorTNodeList)
        self.windowList = syncWindowsToEditorList(newwindowList, self.editorList)


    def calculateMsg(self):
        if self.message:
            return self.message
        elif self.activeWindow.message:
            return self.activeWindow.message
        else:
            return ''

    def printToScreen(self, image, posx, posy):
        for y, col in enumerate(image):
            for x, cell in enumerate(col):
                self.app.screenPrint(posx + x, posy + y, cell)


    def draw(self):
        self.calculateWindowPositions()
        maxX = self.app.screenCols
        curY = 0
        wins = self.windowList.length()

        screenForWins = self.app.screenRows - 1  # leave space for cmd bar
        minYStep = screenForWins / wins
        leftover = screenForWins % wins

        for winNode in self.windowList.first():
            window = winNode.child
            if leftover > 0:
                curYStep = minYStep + 1
                leftover -= 1
            else:
                curYStep = minYStep

            if winNode == self.windowList.cursor:
                winImage = window.draw(0, curY, maxX, curYStep, True)
            else:
                winImage = window.draw(0, curY, maxX, curYStep, False)
            self.printToScreen(winImage, 0, curY)
            curY += curYStep

        cmdPosy = screenForWins
        if self.cmdBar:
            cmdImage = self.cmdBar.draw(maxX, 1, isActive=True)
            self.printToScreen(cmdImage, 0, cmdPosy)
        else:
            msg = screen.stringToImage(self.calculateMsg(), maxX, 1)
            self.printToScreen(msg, 0, cmdPosy)


    def matchWindowToClick(self, x, y):
        def matchWin(win):
            return True if win.posx <= x < win.posx + win.maxx and win.posy <= y < win.posy + win.maxy -1 \
                else False

        return self.windowList.findFirst(matchWin)

    # not sure if this is conceptually the right way to go about doing this, but once we've collect all the
    # updates in a newWindowList then this function unpicks it all to get at the various level of changes:
    # newWindow, new editor, new image
    # and then syncs the various parts
    def integrateUpdatedWindowList(self, newWinList):
        newWin = newWinList.cursor.child
        newEditorList = newWin.editorList
        newEditor = newEditorList.cursor.child

        if newEditor.isRootImageEditor() and self.ImageRoot != newEditor.buffer.root:
            newImage = newEditor.buffer.root
            self.ImageRoot = newImage
            if newEditor.updateUndo:
                self.hist = tn.cons(self.ImageRoot.child, self.hist)

            syncedEditorList = syncEditorsToImage(newEditorList, newImage)
        else:
            syncedEditorList = newEditorList

        return self.updateList(
            ('editorList', syncedEditorList),
            ('windowList', syncWindowsToEditorList(newWinList, syncedEditorList)))

    def loadNewImage(self, newImage):
        syncedEditorList = syncEditorsToImage(self.editorList, newImage)
        syncedWindowList = syncWindowsToEditorList(self.windowList, syncedEditorList)

        return self.updateList(
            ('ImageRoot', newImage),
            ('hist', newImage),
            ('editorList', syncedEditorList),
            ('windowList', syncedWindowList))


    def addWindow(self, newWindow):
        newWinList = self.windowList.appendAtCursor(newWindow).curNext()
        return self.integrateUpdatedWindowList(newWinList)

    def replaceWindow(self, newWindow):
        newWinList = self.windowList.replaceAtCursor(newWindow)
        return self.integrateUpdatedWindowList(newWinList)


    def evalCmdBarResult(self, cmdBuffer):
        # Maybe should get done in the actual cmdbar
        cmd = cmdBuffer.toPyExp()
        print cmd

        if cmd and cmd[0] in ('q', 'quit'):
            return 'QUIT-WM'

        result = eval.eval(buffer.BufferSexp(cmdBuffer.root), self.getCmdBarEnv())
        print result

        if isinstance(result, WindowManager):
            return result.update('cmdBar', None)

        self.message = reader.to_string(result)

        return self.updateList(
            ('cmdBar', None))

    def handleCmdBarInput(self, key):
        cmdResult = self.cmdBar.handleKeys(key)
        if cmdResult.returnState == 'ESCAPE':
            return self.update('cmdBar', None)

        elif cmdResult.returnState == 'PRINT':
            return self.evalCmdBarResult(cmdResult.buffer)

        else:
            return self.update('cmdBar', cmdResult)

    def handleMouse(self, mouse):
        try:
            newwindowList = self.matchWindowToClick(mouse.x, mouse.y)
        except ValueError:
            return self
        else:
            resultWin = newwindowList.getCurrent().handleMouse(mouse)
            newwindowList2 = newwindowList.replaceAtCursor(resultWin)
            return self.update('windowList', newwindowList2)


    def handleKeys(self, key):
        if self.cmdBar:
            return self.handleCmdBarInput(key)

        return self.update('message', None).handleKeysMain(key)

    def handleKeysMain(self, key):
        if self.winCmd:
            result = self.wincl.process(key, self)
            ret = result if result else self
            return ret.update('winCmd', False)

        mainResult = self.mainCl.process(key, self)
        if mainResult:
            return mainResult

        else:
            resultWin = self.activeWindow.handleKeys(key)
            resultEd = resultWin.editor

            if resultEd == 'UNDO':
                return cmdUndo(self)

            else:
                return self.replaceWindow(resultWin)


    def loadEditorSettingsFromPyExp(self, pyExp):
        root = tn.TNode(tn.createTNodeExpFromPyExp(pyExp))
        newBuff = buffer.BufferSexp(root)

        return eval.eval(newBuff)

    def cmdWriteAll(self):
        self.cmdWriteImageTS()
        self.cmdWriteEditorSettingsTS()
        return self.update('message', "Image and editor settings saved")
    
    
    def cmdWriteEditorSettingsTS(self):
        # bit of a hack, but basically change the persistence definition at save time as currently difficult to
        # retain with the way objects are set up.
        self.editorList.persist.append('root')
        self.windowList.persist.append('root')
        pyObj = self.serialise()
        text = reader.to_string(pyObj)
        reader.writeLatestFile('editor-settings-fs/', 'EditorSettings', text)
    
        return self.update('message', "Saving Editor settings")
    
    def cmdWriteImageTS(self):
        pyObj = self.ImageRoot.child.toPyNumberedExp()
        text = reader.to_string(pyObj)
        reader.writeLatestFile('imagefs/', 'image', text)
    
        return self.update('message', "Saving Latest Image")
    
    def cmdLoadLatestAll(self):
        pyEditorLoad = reader.readLatestFile('editor-settings-fs/')
        newWM = self.loadEditorSettingsFromPyExp(pyEditorLoad)
        newWM.app = self.app
        return newWM.cmdLoadLatestImage()
    
    def cmdLoadLatestImage(self):
        pyImageLoad = reader.readLatestFile('imagefs/')
    
        pyImage = [0]
        pyImage.append(pyImageLoad)
        imageRoot = tn.createTNodeExpFromPyNumberedExp(pyImage)
    
        return self.loadNewImage(imageRoot)

    def cmdLoadEditorSettings(self):
        pyEditorLoad = reader.readLatestFile('editor-settings-fs/')
        newWM = self.loadEditorSettingsFromPyExp(pyEditorLoad)
        newWM2 = newWM.loadNewImage(self.ImageRoot)
        return newWM2





def cmdWinDown(wm):
    try:
        return wm.update('windowList', wm.windowList.curNext())
    except ValueError:
        return wm

def cmdWinUp(wm):
    try:
        return wm.update('windowList', wm.windowList.curPrev())
    except ValueError:

        return wm

def cmdWinDel(wm):
    if wm.windowList.length() > 1:
        return wm.update('windowList', wm.windowList.deleteAtCursor())
    else:
        return wm

def cmdWinSplit(wm):
    curWin = wm.activeWindow
    newEd = curWin.editor.clone()
    newWin = curWin.addEditor(newEd)
    return wm.addWindow(newWin)

def cmdUndo(wm):
    if wm.hist.next:
        wm.hist = wm.hist.next
        wm.ImageRoot = tn.TNode(wm.hist.child)

        syncedEditorList = syncEditorsToImage(wm.editorList, wm.ImageRoot)

        return wm.updateList(
            ('editorList', syncedEditorList),
            ('windowList', syncWindowsToEditorList(wm.windowList, syncedEditorList)))

def cmdWinNext(wm):
    return wm.updateList(
        ('windowList', wm.windowList.curCycle()),
        ('winCmd', False))

def cmdRunProg(wm):
    return wm.addWindow(window.cmdEditorRunProg(wm.activeWindow))

def cmdOpenWinOnCursor(wm):
    return wm.addWindow(window.cmdNewEditorOnCursor(wm.activeWindow))

def cmdOpenWinInspectProc(wm):
    try:
        return wm.addWindow(window.cmdInspectProcedureCall2(wm.activeWindow))
    except ex.UnappliedProcedureException:
        return wm

def cmdExitWinMode(wm):
    return wm.update('winCmd', False)

def cmdToggleFullscreen(wm):
    print 'fullscreen'
    iop.toggleFullScreen()
    return wm.update('winCmd', False)

def cmdPlayMedia(wm):
    wm.app.playMedia()

def cmdSave(wm):
    wm.writeImage()
    wm.writeEditor()
    print "saving"
    return wm.update('message', "Saving Image")

def cmdStartWinMode(wm):
    return wm.updateList(
        ('message', 'Window Mode'),
        ('winCmd', True))

def cmdStartCmdBar(wm):
    return wm.update('cmdBar', CmdBar())

def cmdScreenEditor(wm):
    print "changing to screen mode"
    return wm.replaceWindow(window.cmdNewScreenEditor(wm.activeWindow))

def cmdTextPager(wm):
    print "changing to text paging mode"
    return wm.replaceWindow(window.cmdNewPager(wm.activeWindow))

def cmdReplEditor(wm):
    winCmd = window.createAddEditorCommand(repl.Repl)
    return wm.replaceWindow(winCmd(wm.activeWindow))

def cmdSFE(wm):
    winCmd = window.createAddEditorCommand(sfe.SimpleFileEditor.fromPath, './')
    return wm.replaceWindow(winCmd(wm.activeWindow))

def cmdMusic(wm):
    winCmd = window.createAddEditorCommand(sfe.SimpleFileEditor.fromPath, 'D:/Music')
    return wm.replaceWindow(winCmd(wm.activeWindow))
