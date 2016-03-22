__author__ = 'chephren'
import reader
import iop
import TNode

wm = None
isa = isinstance


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
        return "(LetSyntaxException " + str(self.value) + ")"
    pass

class SyntaxException(EvalException):
    def __str__(self):
        return "(SyntaxException " + str(self.value) + ")"
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
         'int':lambda x:charToInt(x), 'cat':lambda a,b:a+b,
         'string-ref':lambda str,ref:str[ref],
         'screen-width':lambda :iop.screenWidth(),
         'screen-height': lambda :iop.screenHeight(),
         'make-vector':lambda size,t:list(t) * size,
         'make-string':lambda size,c:str(c) * size,
         'count-wins':lambda :wm().wins
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

            #            def makeClosure(fun, env):
            #                exp, curEnv = fun('inspect')  # makeLambda
            #                return eval(exp, curEnv)

            def makeLambda(*args):
                if args and args[0] == 'inspect':
                    return [expBuf, Env(vars, args[1:], env)]
                else:
                    return eval(expBuf, Env(vars, args, env), False)

        except AttributeError:
            ret = LambdaSyntaxException("Err")
        except LambdaSyntaxException as err:
            ret = err

        else:
            ret = makeLambda
            #ret = makeClosure(makeLambda, )


    elif exprChild.cursor.child == 'let':
    #            if not isa(mapping, TNode):
    #                ret = LetSyntaxException("Bad-Var-Syntax")

        vars = []
        valResults = []

        try:
            #mapping = exprChild.cursor.next.child
            mapping = exprChild.curNext().curChild()

            while True:
                curVar = mapping.curChild().curChild()
                vars.append(curVar)

                curVal = mapping.curChild().curNext()
                closure = Env([curVar], [None], env)
                curValResult = eval(curVal, closure, memoize)
                closure.find(curVar)[curVar] = curValResult
                #closure = Env([curVar], [eval(val, env, memoize)], env)
                valResults.append(curValResult)

                try: mapping = mapping.curNext()
                except ValueError: break

                #                for i in mapping:
                #                    vars.append(i.child.child)
                #                    val = i.child.next
                #                    valResults.append(self.eval(val, env))
        except AttributeError:
            ret = LetSyntaxException("Bad-Var-Syntax")

        else:
            try:
                body = exprChild.curNext().curNext()

            except ValueError:
                ret = LetSyntaxException("NoBody")
            else:
                newEnv = Env(vars, valResults, env)
                ret = eval(body, newEnv, memoize)

    elif exprChild.cursor.child == 'if':

        negative = None
        try:
            cond = exprChild.curNext()
            positive = exprChild.curNext().curNext()
            try:
                negative = exprChild.curNext().curNext().curNext()
            except ValueError: pass
        except ValueError:
            ret = SyntaxException("Bad-If-Expression")
        else:

            condResult = eval(cond, env, memoize)

            if isinstance(condResult, Exception):
                ret = condResult
            elif condResult:    # replace with try
                ret = eval(positive, env, memoize)
            else:
                if negative is not None:
                    ret = eval(negative, env, memoize)
                else:
                    return False

    elif exprChild.cursor.child == 'quote':
        ret = exprChild.curNext().cursorToPySexp()

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
