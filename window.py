import funobj as fo
import iop
from iop import Key
import leditor_exceptions as ex
import reader, buffer, eval, lispObjEditor, CodeEditor
import cmdList
import fileEditor, screenEditor, pager, repl
import simpleFileEditor as sfe
import Editors
import screen


class Window(fo.FuncObject):
    def __init__(self, editorList=None, x=0, y=0, width=25, height=25):
        self.posx, self.posy = x, y
        self.maxx, self.maxy = width, height
        self.editorList = editorList

        self.winMessage = None
        self.statusBar = Editors.StatusBar()
        self.persist = ['editorList']

    def setPosition(self, newPosx, newPosy, newMaxx, newMaxy):
        return self.updateList(
            ('posx', newPosx),
            ('posy', newPosy),
            ('maxx', newMaxx),
            ('maxy', newMaxy))

    def draw(self, posx, posy, maxx, maxy, isActive):
        #return self.editor.draw(maxx, maxy, isActive)
        editorImage = self.editor.draw(maxx, maxy, isActive)

        finalImage =[None] * maxy

        screen.overlayLinesOnImage(finalImage, 0, editorImage)

        statusBar = Editors.StatusBar.fromStatusList(self.status())
        #if self.statusBar:
        statusImage = statusBar.draw(maxx, 1, isActive=False)
        screen.overlayLinesOnImage(finalImage, maxy - 1, statusImage)

        return finalImage

    def status(self):
        return self.editor.status()

    @property
    def message(self):
        if self.winMessage:
            return self.winMessage
        else:
            return self.editor.message

    @property
    def editor(self):
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

    def handleMouse(self, mouse):
        relativePositionMouse = mouse.getMouseWithRelativePosition(self.posx, self.posy)
        newEditor = self.editor.handleMouse(relativePositionMouse)
        return self.update('editorList', self.editorList.replaceAtCursor(newEditor))

    def handleKeys(self, key):
        newEditor = self.editor.handleKeys(key)
        return self.updateList(
            ('editorList', self.editorList.replaceAtCursor(newEditor)))


class StdWindow(Window):
    def __init__(self, *args, **kargs):
        super(StdWindow, self).__init__(*args, **kargs)
        self.editorCmd = False
        self.editModeCL = cmdList.CmdList([
            (Key.c('l'), cmdEditorNext),
            (Key.c('h'), cmdEditorPrev),
            (Key.c('d'), cmdEditorDel),
            (Key.c('>'), cmdInspectProcedureCall),
            (Key.c('?'), cmdEditorDisplayHelp),
            (Key.c('r'), cmdRunEditorObj),
            (Key.vk(iop.KEY_SPACE), cmdEditorRunProg),
            (Key.vk(iop.KEY_ENTER), cmdNewEditorOnCursor)
        ])

    def handleKeys(self, key):
        if self.editorCmd:
            result = self.editModeCL.process(key, self)
            if result:
                return result.updateList(
                    ('editorCmd', False),
                    ('winMessage', None))

            if key.isPrintable() or key.code == iop.KEY_ESCAPE:
                return self.updateList(
                    ('editorCmd', False),
                    ('winMessage', None))
            else:
                return self

        elif key.char == 'b' and key.ctrl():
            return self.updateList(
                ('editorCmd', True),
                ('winMessage', "--Buffer Command--"))

        else:
            return super(StdWindow, self).handleKeys(key)



def cmdNewScreenEditor(window):
    newEd = screenEditor.ScreenEditor(window.maxx, window.maxy)
    return window.addEditor(newEd)

def cmdNewFileEditor(window):
    newEd = fileEditor.FileEditor.fromPath('./')
    return window.addEditor(newEd)

def cmdNewSFE(window):
    newEd = sfe.SimpleFileEditor.fromPath('./')
    return window.addEditor(newEd)

def cmdNewPager(window):
    file, pathList = window.editor.buffer.getNVSListAtCursor()
    pathText = '.\\' + '\\'.join(pathList)
    newEd = pager.Pager.fromFile(pathText)

    return window.addEditor(newEd)

def cmdNewRepl(window):
    return window.addEditor(repl.Repl())

def cmdNewEditorOnCursor(window):
    newEd = window.editor.updateBuffer(window.editor.buffer.viewToCursor())
    return window.addEditor(newEd)

def cmdInspectProcedureCall(window):
    try:
        return window.cmdInspectProcedureCall2()
    except ex.UnappliedProcedureException:
        return window


def cmdInspectProcedureCall2(window, proc=None, args=None):
    curEd = window.editor
    procedure = window.editor.buffer.cursor if proc is None else proc

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

        return window.addEditor(newEd)

    else:
        raise ex.UnappliedProcedureException(procValue)


def cmdEditorDisplayHelp(window):
    curEd = window.editor

    rootObj = curEd.getNodeValue(curEd.buffer.root)
    helpResult = rootObj.call(reader.Symbol('help')).call("all")
    newBuff = rootObj.updateVarSource('evalBuffer', helpResult)
    newEd = CodeEditor.CodeEditor(newBuff.viewToCursor())
    newEd.printingMode = 'vertical'
    newEd.evalCursorMode = 'disabled'

    return window.addEditor(newEd)

def cmdEditorRunProg(window):
    curEd = window.editor
    imageRoot = curEd.buffer.root
    evalBuffer = buffer.BufferSexp(imageRoot, curEd.buffer.rootToCursorAdd())
    #evalBuffer = curEd.buffer.viewToCursor()

    #procedure = window.getEditor().buffer.cursor
    #procValue = curEd.getNodeValue(procedure.child)
    #newTree, env = procValue.inspect(*args2)
    #newEd = CodeEditor.InspectionEditor(newTree.root, newTree.rootToCursorAdd())

    prog = CodeEditor.evalIOHandler(evalBuffer)
    return window.addEditor(prog)

def cmdRunEditorObj(window):
    curEd = window.editor
    imageRoot = curEd.buffer.root
    evalBuffer = buffer.BufferSexp(imageRoot, curEd.buffer.rootToCursorAdd())
    prog = lispObjEditor.LispObjEditor(eval.eval(evalBuffer))

    return window.addEditor(prog)

def cmdEditorNext(window):
    return window.update('editorList', window.editorList.curCycle())

def cmdEditorPrev(window):
    return window.update('editorList', window.editorList.curCyclePrev())

def cmdEditorDel(window):
    if window.editorList.length() > 1:
        return window.update('editorList', window.editorList.deleteAtCursor())
    else:
        return window

