__author__ = 'chephren'
import Editors
import screen
import buffer
import iop
import reader
import eval
import misc
from reader import Symbol


class CodeEditor(Editors.TreeEditor):
    def __init__(self, aBuffer=None, zippedNodes={}):
        super(CodeEditor, self).__init__(aBuffer, zippedNodes)
        self.statusDescription = reader.Symbol('CodeEditor')
        self.env = eval.global_env
        self.vars = None
        self.context = None
        self.parent = None
        self.printingMode = 'code'
        self.printingModeOptions = ['code', 'horizontal', 'vertical']
        self.evalCursorMode = 'active'
        self.evalCursorModeOptions = ['active', 'disabled']
        self.nodeValues = {}

    @classmethod
    def fromBufferParts(cls, root, viewAdd=[0], cursorAdd=[0], zippedNodes={}):
        newBuffer = buffer.BufferSexp(root, viewAdd, cursorAdd)
        return cls(newBuffer, zippedNodes)


    def storeNodeValue(self, node, val, env=None):
        self.nodeValues[node] = (val, env)

    def getNodeValue(self, node):
        if node in self.nodeValues:
            val, env = self.nodeValues[node]
            return val

    def hasNodeValue(self, node):
        return True if node in self.nodeValues else False

    def getNodeEnv(self, node):
        if node in self.nodeValues:
            val, env = self.nodeValues[node]
            return env

    def evalBuffer(self):
        eval.eval(buffer.BufferSexp(self.buffer.root), self.env, self.storeNodeValue)

    def syncWithImage(self, newImageRoot):
        if newImageRoot != self.buffer.root:
            # special case when we have a newly created buffer
            if self.buffer.emptyBuffer():
                newBuffer = self.buffer.indexNewRoot(newImageRoot)
            else:
                newBuffer =  self.buffer.syncToNewRoot(newImageRoot)
            newSelf = self.updateBuffer(newBuffer)
            newSelf.evalBuffer()
            return newSelf

        else:
            return self

    def updateStatusBar(self):
        self.statusBar.updateStatus(
            [self.statusDescription, self.buffer.viewAdd, self.buffer.cursorAdd,
            [Symbol('nodeID'), self.buffer.cursor.nodeID],
            [Symbol('=>'), self.getNodeValue(self.buffer.cursor)]])


    # a bit of a hack, necessary because everything is handled in handleKeys. We need to make sure that
    # the codeEditor returns with a newly evaluated buffer if there were any significant changes.
    def handleKeys(self, key):
        result = self.handleKeysInitial(key)
        if result != 'UNDO' and result.updateUndo:
            result.evalBuffer()  # updating imperatively

        return result


    def handleKeysMain(self, key):
        # evaluate the current context
        if key.code() == iop.KEY_ENTER and not self.editing:

            nodeValue = self.getNodeValue(self.buffer.cursor)
            if key.shift():
                result = self.updateList(
                    ('buffer', self.buffer.appendAtCursor(nodeValue).curNext()),
                    ('yankBuffer', nodeValue),
                    ('updateUndo', True))
            else:
                self.statusBar.updateMessage('Result to buffer')
                result = self.update('yankBuffer', nodeValue)

        elif key.code() == iop.KEY_F2:
            newCursorMode = misc.cycleThroughList(self.evalCursorMode, self.evalCursorModeOptions)
            result = self.update('evalCursorMode', newCursorMode)

        # Create a repl like environment to evaluate code in
        elif key.code() == iop.KEY_F8:
            newBuff = self.buffer.curChild().curLast()
            newBuff = newBuff.viewToCursor().curChild().curLast()
            self.printingMode = 'vertical'
            self.topLine = 0
            return self.update('buffer', newBuff)

        # elif key.char() == '>':
        #     curNode = self.buffer.cursor
        #     if curNode.isSubNode():
        #         args = []
        #         if curNode.child.next:
        #             for i in curNode.child.next:
        #                 args.append(self.nodeValues[i])
        #
        #         (newTree, env) = self.nodeValues[curNode.child]('inspect', *args)
        #
        #         newEd = InspectionEditor(newTree.root, newTree.rootToCursorAdd(),
        #                                       zippedNodes=self.zippedNodes)
        #
        #         newEd.context = self.buffer
        #         newEd.contextParent = self.id    # not really needed?
        #         newEd.env = env
        #         newEd.evalBuffer()
        #         return newEd
        #    else:
        #        return self


        else:
            result = super(CodeEditor, self).handleKeysMain(key)


        return result


class InspectionEditor(CodeEditor):
    def __init__(self, *args, **kwargs):
        super(InspectionEditor, self).__init__(*args, **kwargs)
        self.statusDescription = reader.Symbol('InspectionEditor')

    def evalBuffer(self):
        eval.eval(buffer.BufferSexp(self.buffer.root, self.buffer.viewAdd), self.env, self.storeNodeValue)

    def updateStatusBar(self):
        self.statusBar.updateStatus(
            [self.statusDescription,
            [[Symbol(key), value] for key, value in self.env.items()],
            [Symbol('='), self.getNodeValue(self.buffer.cursor)]])


class ProgInspectionEditor(InspectionEditor):
    def __init__(self, *args, **kwargs):
        super(InspectionEditor, self).__init__(*args, **kwargs)
        self.statusDescription = reader.Symbol('InspectionEditor')
        self.progID = None

    #def syncArgsToProgInput(self, input):
    #    self.env = eval.Env(self.env.vars, )





class evalIOHandler(CodeEditor):
    def __init__(self, aBuffer=None):
        super(evalIOHandler, self).__init__(aBuffer)
        self.keyHistory = []
        self.lastKey = 0
        self.output = ''
        self.evalBuffer()
        self.mode = 'prog'
        self.function = self.getNodeValue(self.buffer.cursor)


    def handleKeysProg(self, key):
        if key.isPrintable():
            self.keyHistory.append(key.char())
            self.lastKey = key.char()

        handleKeysMethod = self.function.call('handleKeys')
        self.function = handleKeysMethod.call(self.lastKey)

        return self


    def handleKeys(self, key):
        if key.code() == iop.KEY_TAB:
            self.mode = 'inspect' if self.mode == 'prog' else 'prog'

        elif self.mode == 'prog':
            return self.handleKeysProg(key)

        else:
            return super(evalIOHandler, self).handleKeys(key)

    def handleMouse(self, mouse):
        return self


    def drawProg(self, maxx, maxy, isActive=False):
        if self.lastKey != 0:
            if hasattr(self.function, 'call'):
                drawFunc = self.function.call('draw')
                self.output = drawFunc.call(0, 0)
            else:
                self.output = "Not a function" #ProgException(self.function, "Not a Function")
        return screen.stringToImage(self.output, maxx, maxy, self.colourScheme.bgCol, self.colourScheme.identifierCol)


    def draw(self, maxx, maxy, isActive=False):
        if self.mode == 'prog':
            return self.drawProg(maxx, maxy)
        else:
            return super(evalIOHandler, self).draw(maxx, maxy, isActive)

    def updateStatusBar(self):
        self.statusBar.updateStatus(
            [self.statusDescription,
            [[Symbol(key), value] for key, value in self.env.items()],
            [Symbol('='), self.getNodeValue(self.buffer.cursor)]])