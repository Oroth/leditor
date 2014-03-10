__author__ = 'chephren'
import Editors
import utility
import libtcodpy as libtcod
import reader
import TNode

isa = isinstance

#class Symbol(str): pass
Symbol = str

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
         'null?':lambda x:x==[], 'symbol?':lambda x: isa(x, Symbol)

         #,'^':lambda *vars,*body: (lambda *args: eval(body, Env(vars, args, global_env)))
        })
    return env

global_env = add_globals(Env())


class CodeEditor(Editors.TreeEditor):
    def __init__(self, *args, **kwargs):
        super(CodeEditor, self).__init__(*args, **kwargs)
        self.showValues = True
        self.env = None
        self.context = None
        #self.value = TNode.copyTNodeAsNewTreeClass(self.buffer.cursor, evalNode.EvalNode)
        self.nodeValues = {}

    def evalBuffer(self):
        self.eval(self.buffer.view, self.env)

    def eval(self, expr, env=global_env, memoize=True):
        #self.calcEnv()
        x = expr.child
        ret = None

#        if not self.evaled and not ignoreQuote:
#            ret = self.activeToPySexp()

        if isa(x, Symbol):             # variable reference
            try:
                ret = env.find(x)[x]
            except EvalException as ex:
                ret = ex
                #self.displayValue = True
        elif not isa(x, TNode.TNode):         # constant literal
            ret = x

        elif x.child == '^':         # (lambda (var*) exp)

            try:
                vars = x.next.child.toPySexp()
                #check if list of symbols:

                exp = x.next.next
                if not exp:
                    raise LambdaSyntaxException("NoBody")

                def constructLambda(*args):
                    if args and args[0] == 'inspect':
                        return [exp, Env(vars, args[1:], env)]
                    else:
                        return self.eval(exp, Env(vars, args, env), False)

            except AttributeError:
                ret = LambdaSyntaxException("Err")
            except LambdaSyntaxException as err:
                ret = err

            else:
                ret = constructLambda


        elif x.child == 'let':
        #            if not isa(mapping, TNode):
        #                ret = LetSyntaxException("Bad-Var-Syntax")

            vars = []
            valResults = []

            try:
                mapping = x.next.child
                for i in mapping:
                    vars.append(i.child.child)
                    val = i.child.next
                    valResults.append(self.eval(val, env))
            except AttributeError:
                ret = LetSyntaxException("Bad-Var-Syntax")

            else:
                body = x.next.next
                if body:
                    ret = self.eval(body, Env(vars, valResults, env))
                else:
                    ret = LetSyntaxException("NoBody")

        else:  # i.e. a Tnode
            childExpr = []
            for i in x:
                childExpr.append(self.eval(i, env, memoize))

            #exps = [eval(exp, env) for exp in childExpr]
            for i in childExpr:
                if isinstance(i, LookUpException):
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

                    #self.displayValue = True

        if memoize:
            self.nodeValues[expr] = ret

        return ret



    def draw(self, posx, posy, maxx, maxy, hlcol):

        if self.showValues:
            self.evalBuffer()

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

                if not node.previous and node.next and node.next.next:
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
