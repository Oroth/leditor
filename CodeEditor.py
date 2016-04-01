__author__ = 'chephren'
import Editors
import utility
import buffer
import iop
import reader
import eval


class CodeEditor(Editors.TreeEditor):
    def __init__(self, *args, **kwargs):
        super(CodeEditor, self).__init__(*args, **kwargs)
        self.statusDescription = reader.Symbol('CodeEditor')
        self.showValues = True
        self.env = eval.global_env
        self.vars = None
        self.context = None
        self.parent = None
        self.nodeValues = {}

    def storeNodeValue(self, node, val):
        self.nodeValues[node] = val

    def evalBuffer(self):
        eval.eval(buffer.BufferSexp(self.buffer.root), self.env, self.storeNodeValue)


    def syncWithImage(self, newImageRoot):
        if newImageRoot != self.buffer.root:
            newSelf = self.update('buffer', self.buffer.syncToNewRoot(newImageRoot))
            newSelf.evalBuffer()
            return newSelf
        else:
            return self

    # a bit of a hack, necessary because everything is handled in handleKeys. We need to make sure that
    # the codeEditor returns with a newly evaluated buffer if there were any significant changes.
    def handleKeys(self, key, mouse):

        # evaluate the current context
        if key.code() == iop.KEY_ENTER and not self.editing:

            nodeValue = self.nodeValues[self.buffer.cursor]
            if key.shift():
                result = self.updateList(
                    ('buffer', self.buffer.appendAtCursor(nodeValue).curNext()),
                    ('yankBuffer', nodeValue),
                    ('updateUndo', True))
            else:
                self.statusBar.displayMessage('Result to buffer')
                result = self.update('yankBuffer', nodeValue)

        # Create a repl like environment to evaluate code in
        elif key.code() == iop.KEY_F8:
            newBuff = self.buffer.curChild().curLast()
            newBuff = newBuff.viewToCursor().curChild().curLast()
            self.printingMode = 'vertical'
            self.topLine = 0
            return self.update('buffer', newBuff)

        else:
            result = super(CodeEditor, self).handleKeys(key, mouse)

        self.evalBuffer()   # updating imperatively?
        return result


class InspectionEditor(CodeEditor):
    def __init__(self, *args, **kwargs):
        super(InspectionEditor, self).__init__(*args, **kwargs)
        self.statusDescription = reader.Symbol('InspectionEditor')

    def evalBuffer(self):
        eval.eval(buffer.BufferSexp(self.buffer.root, self.buffer.viewAdd), self.env, self.storeNodeValue)


class evalIOHandler(CodeEditor):
    def __init__(self, buffer):
        super(evalIOHandler, self).__init__(buffer.root, buffer.viewAdd, buffer.cursorAdd)
        self.keyHistory = []
        self.lastKey = 0
        self.output = ''
        self.evalBuffer()

    def handleKeys(self, key, mouse):
        if key.char() != 0:
            self.keyHistory.append(key.char())
            self.lastKey = key.char()

        return self

    def draw(self, posx, posy, maxx, maxy, hlcol=None):
        self.function = self.nodeValues[self.buffer.cursor]
        if self.lastKey != 0:
            self.output = self.function(self.keyHistory)
        pen = utility.Pen(posx, posy, maxx, posy+maxy)
        pen.write(str(self.output))