__author__ = 'chephren'
import Editors
import utility
import libtcodpy as libtcod
import reader
import TNode

isa = isinstance

#Symbol = str

class EvalException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "(EvalException " + self.value + ")"
    #    def __repr__(self):
#        return ["Err:", self.value]

class LookUpException(EvalException):
    def __str__(self):
        return "(LookUpException " + self.value + ")"
    pass

class DivZeroException(EvalException):
    def __init__(self):
        pass

    def __str__(self):
        return "(DivZeroException)"
    pass

class LetSyntaxException(EvalException):
    def __str__(self):
        return "(LetSyntaxException)"
    pass

class LambdaSyntaxException(EvalException):
    def __str__(self):
        return "(LambdaSyntaxException)"
    pass

class NonProcException(EvalException):
    def __str__(self):
        return "(NonProcException " + str(self.value) + ")"
    pass

class TypeException(EvalException):
    def __str__(self):
        return "(TypeException " + str(self.value) + ")"
    pass

class Env(dict):
    "An environment: a dict of {'var':val} pairs, with an outer Env."
    def __init__(self, parms=(), args=(), outer=None):
        self.update(zip(parms,args))
        self.outer = outer
    def find(self, var):
        "Find the innermost Env where var appears."
        if var in self:
            return self
        elif self.outer:
            return self.outer.find(var)
        else:
            raise LookUpException(var)


def charToInt(char):
    try:
        return int(char)
    except ValueError:
        raise TypeError

def add_globals(env):
    "Add some Scheme standard procedures to an environment."
    import math, operator as op
    env.update(vars(math)) # sin, sqrt, ...
    env.update(
        {'+':op.add, '-':op.sub, '*':op.mul, '/':op.div, 'not':op.not_,
         '>':op.gt, '<':op.lt, '>=':op.ge, '<=':op.le, '=':op.eq,
         'equal?':op.eq, 'eq?':op.is_, 'length':len, 'cons':lambda x,y:[x]+y,
         'car':lambda x:x[0],'cdr':lambda x:x[1:], 'append':op.add,
         'list':lambda *x:list(x), 'list?': lambda x:isa(x,list),
         'null?':lambda x:x==[], 'symbol?':lambda x: isa(x, reader.Symbol),
         'int':lambda x:charToInt(x)
         #,'^':lambda *vars,*body: (lambda *args: eval(body, Env(vars, args, global_env)))
        })
    return env

global_env = add_globals(Env())

def eval(exprBuf, env=global_env, memoize=None):
    #self.calcEnv()
    #x = expr.child
    exprChild = exprBuf.curChild()
    ret = None

    if not exprBuf.cursor.evaled:
        ret = exprBuf.cursorToPySexp()

    elif isa(exprChild, reader.Symbol):             # variable reference
        try:
            ret = env.find(exprChild)[exprChild]
        except EvalException as ex:
            ret = ex
    elif not isa(exprChild, TNode.Buffer):         # constant literal
        ret = exprChild

    elif exprChild.cursor.child == '^':         # (lambda (var*) exp)

        try:
            vars = exprChild.cursor.next.child.toPySexp()
            #check if list of symbols:

            #exp = exprChild.cursor.next.next
            expBuf = exprChild.curNext().curNext()
            #if not exp:
            #raise LambdaSyntaxException("NoBody")

            def constructLambda(*args):
                if args and args[0] == 'inspect':
                    return [expBuf, Env(vars, args[1:], env)]
                else:
                    return eval(expBuf, Env(vars, args, env), False)

        except AttributeError:
            ret = LambdaSyntaxException("Err")
        except LambdaSyntaxException as err:
            ret = err

        else:
            ret = constructLambda


    elif exprChild.cursor.child == 'let':
    #            if not isa(mapping, TNode):
    #                ret = LetSyntaxException("Bad-Var-Syntax")

        vars = []
        valResults = []

        try:
            #mapping = exprChild.cursor.next.child
            mapping = exprChild.curNext().curChild()

            while True:
                vars.append(mapping.curChild().curChild())
                val = mapping.curChild().curNext()
                valResults.append(eval(val, env, memoize))
                try: mapping = mapping.curNext()
                except ValueError: break

            #                for i in mapping:
            #                    vars.append(i.child.child)
            #                    val = i.child.next
            #                    valResults.append(self.eval(val, env))
        except AttributeError:
            ret = LetSyntaxException("Bad-Var-Syntax")

        else:
            #body = exprChild.cursor.next.next
            body = exprChild.curNext().curNext()
            if body:    # replace with try
                ret = eval(body, Env(vars, valResults, env), memoize)
            else:
                ret = LetSyntaxException("NoBody")

    elif exprChild.cursor.child == 'if':

        #try:
        cond = exprChild.curNext()
        positive = exprChild.curNext().curNext()
        negative = exprChild.curNext().curNext().curNext()

        condResult = eval(cond, env, memoize)

        if isinstance(condResult, Exception):
            ret = condResult
        elif condResult:    # replace with try
            ret = eval(positive, env, memoize)
        else:
            ret = eval(negative, env, memoize)

    else:  # i.e. a procedure call
        childExpr = []
        procExpr = exprChild
        while True:
            childExpr.append(eval(procExpr, env, memoize))
            try: procExpr = procExpr.curNext()
            except ValueError: break

        #            for i in exprChild.cursor:
        #                childExpr.append(self.eval(i, env, memoize))

        #exps = [eval(exp, env) for exp in childExpr]
        for i in childExpr:
            if isinstance(i, Exception):
                ret = i
                break
        else:
            proc = childExpr.pop(0)
            if hasattr(proc, '__call__'):
                try:
                    ret = proc(*childExpr)
                except ZeroDivisionError:
                    ret = DivZeroException()
                except TypeError:
                    ret = TypeException(childExpr)
            else:
                ret = NonProcException(proc)



    if memoize:
        memoize(exprBuf.cursor, ret)
        #self.nodeValues[exprBuf.cursor] = ret

    return ret


class CodeEditor(Editors.TreeEditor):
    def __init__(self, *args, **kwargs):
        super(CodeEditor, self).__init__(*args, **kwargs)
        self.showValues = True
        self.env = global_env
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
        eval(TNode.Buffer(self.buffer.root, self.buffer.viewAdd), self.env, self.storeNodeValue)


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

        #if self.showValues:


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
            self.output = self.function(chr(self.lastKey))
        pen = utility.Pen(posx, posy, maxx, maxy)
        pen.write(str(self.output))