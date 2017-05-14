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
            (Key.c('l'), 'cmdEditorNext'),
            (Key.c('h'), 'cmdEditorPrev'),
            (Key.c('d'), 'cmdEditorDel'),
            (Key.c('>'), 'cmdInspectProcedureCall'),
            (Key.c('?'), 'cmdEditorDisplayHelp'),
            (Key.c('r'), 'cmdRunEditorObj'),
            (Key.vk(iop.KEY_SPACE), 'cmdEditorRunProg'),
            (Key.vk(iop.KEY_ENTER), 'cmdNewEditorOnCursor')
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



    def cmdNewScreenEditor(self):
        newEd = screenEditor.ScreenEditor(self.maxx, self.maxy)
        return self.update('editorList', self.editorList.appendAtCursor(newEd).curNext())


    def cmdNewFileEditor(self):
        newEd = fileEditor.FileEditor.fromPath('./')
        return self.update('editorList', self.editorList.appendAtCursor(newEd).curNext())


    def cmdNewPager(self):
        file, pathList = self.editorList.getCurrent().buffer.getNVSListAtCursor()
        pathText = '.\\' + '\\'.join(pathList)
        newEd = pager.Pager.fromFile(pathText)

        return self.update('editorList', self.editorList.appendAtCursor(newEd).curNext())

    def cmdNewRepl(self):
        newEd = repl.Repl()
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

    def cmdRunEditorObj(self):
        curEd = self.getEditor()
        imageRoot = curEd.buffer.root
        evalBuffer = buffer.BufferSexp(imageRoot, curEd.buffer.rootToCursorAdd())
        prog = lispObjEditor.LispObjEditor(eval.eval(evalBuffer))

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