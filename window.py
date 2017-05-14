import CodeEditor
import buffer
import cmdList
import eval
import fileEditor
import funobj as fo
import iop
import leditor_exceptions as ex
import lispObjEditor
import pager
import reader
import repl
import screenEditor
from iop_libtcod import Key


class Window(fo.FuncObject):
    def __init__(self, editorList=None, x=0, y=0, width=25, height=25):
        self.posx, self.posy = x, y
        self.maxx, self.maxy = width, height
        self.editorList = editorList
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

        self.message = None

        self.persist = ['editorList']

    def setPosition(self, newPosx, newPosy, newMaxx, newMaxy):
        return self.updateList(
            ('posx', newPosx),
            ('posy', newPosy),
            ('maxx', newMaxx),
            ('maxy', newMaxy))


    def draw(self, posx, posy, maxx, maxy, isActive):
        return self.getEditor().draw(maxx, maxy, isActive)


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

    def handleMouse(self, mouse):
        relativePositionMouse = mouse.getMouseWithRelativePosition(self.posx, self.posy)
        newEditor = self.getEditor().handleMouse(relativePositionMouse)
        return self.update('editorList', self.editorList.replaceAtCursor(newEditor))


    def handleKeys(self, key):
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

        elif key.char == 'b' and key.ctrl():
            return self.updateList(
                ('editorCmd', True),
                ('message', "--Buffer Command--"))

        else:
            newEditor = self.getEditor().handleKeys(key)
            return self.updateList(
                ('editorList', self.editorList.replaceAtCursor(newEditor)))




def cmdNewScreenEditor(window):
    newEd = screenEditor.ScreenEditor(window.maxx, window.maxy)
    return window.update('editorList', window.editorList.appendAtCursor(newEd).curNext())


def cmdNewFileEditor(window):
    newEd = fileEditor.FileEditor.fromPath('./')
    return window.update('editorList', window.editorList.appendAtCursor(newEd).curNext())


def cmdNewPager(window):
    file, pathList = window.editorList.getCurrent().buffer.getNVSListAtCursor()
    pathText = '.\\' + '\\'.join(pathList)
    newEd = pager.Pager.fromFile(pathText)

    return window.update('editorList', window.editorList.appendAtCursor(newEd).curNext())

def cmdNewRepl(window):
    newEd = repl.Repl()
    return window.update('editorList', window.editorList.appendAtCursor(newEd).curNext())


def cmdNewEditorOnCursor(window):
    newEd = window.getEditor().clone()
    newEd2 = newEd.update('buffer', newEd.buffer.viewToCursor())

    return window.update('editorList', window.editorList.appendAtCursor(newEd2).curNext())

def cmdInspectProcedureCall(window):
    try:
        return window.cmdInspectProcedureCall2()
    except ex.UnappliedProcedureException:
        return window


def cmdInspectProcedureCall2(window, proc=None, args=None):
    curEd = window.getEditor()
    procedure = window.getEditor().buffer.cursor if proc is None else proc

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

        return window.update('editorList', window.editorList.appendAtCursor(newEd).curNext())

    else:
        raise ex.UnappliedProcedureException(procValue)


def cmdEditorDisplayHelp(window):
    curEd = window.getEditor()

    rootObj = curEd.getNodeValue(curEd.buffer.root)
    helpResult = rootObj.call(reader.Symbol('help')).call("all")
    newBuff = rootObj.updateVarSource('evalBuffer', helpResult)
    newEd = CodeEditor.CodeEditor(newBuff.viewToCursor())
    newEd.printingMode = 'vertical'
    newEd.evalCursorMode = 'disabled'

    return window.update('editorList', window.editorList.appendAtCursor(newEd).curNext())

def cmdEditorRunProg(window):
    curEd = window.getEditor()
    imageRoot = curEd.buffer.root
    evalBuffer = buffer.BufferSexp(imageRoot, curEd.buffer.rootToCursorAdd())

    #procedure = window.getEditor().buffer.cursor
    #procValue = curEd.getNodeValue(procedure.child)
    #newTree, env = procValue.inspect(*args2)
    #newEd = CodeEditor.InspectionEditor(newTree.root, newTree.rootToCursorAdd())

    prog = CodeEditor.evalIOHandler(evalBuffer)
    newEditorList =  window.editorList.appendAtCursor(prog).curNext()

    return window.update('editorList', newEditorList)

def cmdRunEditorObj(window):
    curEd = window.getEditor()
    imageRoot = curEd.buffer.root
    evalBuffer = buffer.BufferSexp(imageRoot, curEd.buffer.rootToCursorAdd())
    prog = lispObjEditor.LispObjEditor(eval.eval(evalBuffer))

    newEditorList =  window.editorList.appendAtCursor(prog).curNext()

    return window.update('editorList', newEditorList)

def cmdEditorNext(window):
    return window.update('editorList', window.editorList.curCycle())


def cmdEditorPrev(window):
    return window.update('editorList', window.editorList.curCyclePrev())


def cmdEditorDel(window):
    if window.editorList.length() > 1:
        return window.update('editorList', window.editorList.deleteAtCursor())
    else:
        return window

