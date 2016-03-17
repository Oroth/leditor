__author__ = 'chephren'
import Editors
import utility
import libtcodpy as libtcod
import reader
import TNode
import Eval
#from main import wm




class CodeEditor(Editors.TreeEditor):
    def __init__(self, *args, **kwargs):
        super(CodeEditor, self).__init__(*args, **kwargs)
        self.showValues = True
        self.env = Eval.global_env
        self.vars = None
        self.context = None
        self.parent = None
        #self.value = TNode.copyTNodeAsNewTreeClass(self.buffer.cursor, evalNode.EvalNode)
        self.nodeValues = {}

    def storeNodeValue(self, node, val):
        self.nodeValues[node] = val

    def evalBuffer(self):
        #self.eval(self.buffer, self.env)
        #if self.context:
            #parent = findWin(self.parentID)
            #vals = parent.nodeValues[args]
            #self.env = Env(self.vars, vals, parent.env)
        Eval.eval(TNode.Buffer(self.buffer.root, self.buffer.viewAdd), self.env, self.storeNodeValue)


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
        if key.vk == libtcod.KEY_ENTER and not self.editing:

            nodeValue = self.nodeValues[self.buffer.cursor]
            if key.shift:
                result = self.updateList(
                    ('buffer', self.buffer.appendAtCursor(nodeValue).curNext()),
                    ('yankBuffer', nodeValue),
                    ('updateUndo', True))
            else:
                self.statusBar.displayMessage('Result to buffer')
                result = self.update('yankBuffer', nodeValue)

        # Create a repl like environment to evaluate code in
        elif key.vk == libtcod.KEY_F8:
            newBuff = self.buffer.curChild().curLast()
            newBuff = newBuff.viewToCursor().curChild().curLast()
            #newBuff = newBuff.appendAtCursor([reader.Symbol('newNode')]).curNext()
            self.printingMode = 'vertical'
            self.topLine = 0
            return self.update('buffer', newBuff)


        else:
            result = super(CodeEditor, self).handleKeys(key, mouse)

        self.evalBuffer()   # updating imperatively?
        return result


class evalIOHandler(CodeEditor):
    def __init__(self, buffer):
        #self.tree = funcTree
        super(evalIOHandler, self).__init__(buffer.root, buffer.viewAdd, buffer.cursorAdd)
        self.keyHistory = []
        self.lastKey = 0
        #self.buffer = buffer
        self.output = ''
        self.evalBuffer()

    def handleKeys(self, key, mouse):
        if key.c != 0:
            self.keyHistory.append(chr(key.c))
            self.lastKey = key.c

            #self.function = eval(self.buffer)
            #self.output = self.function(int(chr(key.c)))

        return self


    def draw(self, posx, posy, maxx, maxy, hlcol=None):
        self.function = self.nodeValues[self.buffer.cursor]
        if self.lastKey != 0:
            #self.output = self.function(chr(self.lastKey))
            self.output = self.function(self.keyHistory)
        pen = utility.Pen(posx, posy, maxx, posy+maxy)
        pen.write(str(self.output))