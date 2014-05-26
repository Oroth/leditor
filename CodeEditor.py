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
    def handleKeys(self, key):
        result = super(CodeEditor, self).handleKeys(key)
        self.evalBuffer()
        return result

    def draw(self, posx, posy, maxx, maxy, hlcol):


        def drawHorizontal(posx, posy, hlcol, indent=True):
            pen = utility.Pen(posx, posy, maxx, maxy)

            def drawChild(node, nesting, parentCol=libtcod.black):

                if not node.evaled:
                    pen.write("'", parentCol)

                if node.isSubNode():
                    if node.child == "=>":
                        pen.writeNL()
                        # check view
                    if node == self.buffer.cursor:
                        bgcolour = hlcol
                    else:
                        bgcolour = parentCol

                    pen.write('(', bgcolour)
                    drawr(node.child, nesting, bgcolour)
                    pen.write(')', bgcolour)

                elif node.child is not None:
                    output = reader.to_string(node.child)
                    if node == self.buffer.cursor:

                        if self.editing:
                            self.cellEditor.draw(pen)
                        else:
                            pen.write(output, hlcol)

                    else:
                        pen.write(output, parentCol)

                try:
                    if self.revealedNodes[node]:
                        pen.write("=>", parentCol)
                        #pen.write(reader.to_string(node.getValue(self.id)), parentCol)
                        pen.write(reader.to_string(self.nodeValues[node]), parentCol)
                except KeyError: pass


            def drawr(node, nesting, parentCol=libtcod.black, reindent=False):
                drawChild(node, nesting + 1, parentCol)
                #reindent = False

                if node.next and node.next.next:
                    for i in node.next:
                        if i.isSubNode():
                            reindent = True


                if node.next:
                    if indent and reindent:
                        pen.writeNL()
                        #pen.skip(2 * nesting, 0)
                        pen.write(' ' * (2 * nesting), parentCol)

                    # try to avoid hiding the cursor in a cell editor
                    elif node == self.buffer.cursor and self.editing:
                        pen.skip(1, 0)
                    else:
                        pen.write(' ', parentCol)

                    drawr(node.next, nesting, parentCol, reindent)

            if self.buffer.view.isSubNode():
                drawChild(self.buffer.view, 1)
            else:
                pen.write(str(self.buffer.view.child))

        drawHorizontal(posx, posy, hlcol)


class evalIOHandler(CodeEditor):
    def __init__(self, buffer):
        #self.tree = funcTree
        super(evalIOHandler, self).__init__(buffer.root, buffer.viewAdd, buffer.cursorAdd)
        self.keyHistory = []
        self.lastKey = 0
        #self.buffer = buffer
        self.output = ''
        self.evalBuffer()

    def handleKeys(self, key):
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
        pen = utility.Pen(posx, posy, maxx, maxy)
        pen.write(str(self.output))