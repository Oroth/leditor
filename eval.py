import sys
import traceback

import funobj as fo
import tn, buffer
import reader
import leditor_exceptions as ex


wm = None
isa = isinstance

def evalString(str):
    ps = reader.parse(str)
    buf = buffer.BufferSexp(tn.TNode(ps))
    return eval(buf)

# file io
def deserialiseClass(module_name, cls_name, lst):
    try:
        cls = getattr(sys.modules[module_name], cls_name)
        obj = cls.fromFile(lst)
        return obj
    except Exception as e:
        traceback.print_stack()
        raise DeserialiseException(e)


class DeserialiseException(ex.GeneralException): pass

class EvalException(ex.GeneralException): pass

class LookUpException(EvalException): pass

class DivZeroException(EvalException): pass

class LetSyntaxException(EvalException): pass

class SyntaxException(EvalException): pass

class ListException(EvalException): pass

class LambdaSyntaxException(EvalException): pass

class NonProcException(EvalException): pass

class TypeException(EvalException): pass


class fnEnv(fo.FuncObject):
    def __init__(self, lst, outer=None):
        self.dict = dict(lst)
        self.outer = outer

    def find(self, var):
        if var in self.dict:
            return self.dict
        elif self.outer:
            return self.outer.find(var)
        else:
            raise LookUpException(var)

    def updateDict(self, var, val):
        newDict = dict(self.dict)
        newDict[var] = val
        return self.update('dict', newDict)


class Env(dict):
    "An environment: a dict of {'var':val} pairs, with an outer Env."
    def __init__(self, parms=(), args=(), outer=None):
        self.update(zip(parms,args))
        self.outer = outer

    @classmethod
    def fromList(cls, lst, outer=None):
        (parms, args) = zip(*lst)
        return cls(parms, args, outer)

    def find(self, var):
        "Find the innermost Env where var appears."
        if var in self:
            return self
        elif self.outer:
            return self.outer.find(var)
        else:
            raise LookUpException(var)

    def extend(self, var, val):
        if var in self:
            raise LookUpException(var)
        else:
            pass


def charToInt(char):
    try:
        return int(char)
    except ValueError:
        raise TypeError

def carPrimitive(lst):
    try:
        return lst[0]
    except IndexError:
        return ListException('CAR')

def cdrPrimitive(lst):
    try:
        return lst[1:]
    except IndexError:
        return ListException('CDR')

def add_globals(env):
    "Add some Scheme standard procedures to an environment."
    import math, operator as op
    env.update(vars(math)) # sin, sqrt, ...
    env.update(
        {'+':op.add, '-':op.sub, '*':op.mul, '/':op.div, 'not':op.not_,
         '>':op.gt, '<':op.lt, '>=':op.ge, '<=':op.le, '=':op.eq,
         'equal?':op.eq, 'eq?':op.is_, 'length':len, 'cons':lambda x,y:[x]+y,
         'car':carPrimitive,'cdr':cdrPrimitive, 'append':op.add,
         'list':lambda *x:list(x),
         'dict':lambda x:dict(x),
         'list?': lambda x:isa(x,list),
         'null?':lambda x:x==[],
         'symbol?':lambda x: isa(x, reader.Symbol),
         'int':lambda x:charToInt(x),
         'cat':lambda a,b:a+b,
         'string-ref':lambda str,ref:str[ref],
         'string-from':lambda str,ref:str[ref:],
         'string-left':lambda str, ref:str[:ref],
         #'screen-width':lambda :iop.screenWidth(),
         #'screen-height':lambda :iop.screenHeight(),
         'make-vector':lambda size,t:list(t) * size,
         'make-string':lambda size,c:str(c) * size,
         'count-wins':lambda :wm().getWinCount(),
         #'class':lambda mod_name, cls_name, lst :wm().deserialiseClass(mod_name, cls_name, lst)
         'class':deserialiseClass
         #,'^':lambda *vars,*body: (lambda *args: eval(body, Env(vars, args, global_env)))
        })
    return env


global_env = add_globals(Env())


class Closure(fo.FuncObject):
    def __init__(self, type, expBuf, vars, parentEnv):
        self.type = type
        self.expBuf = expBuf
        self.vars = vars
        self.env = parentEnv

    def inspect(self, *args):
        return self.expBuf, Env(self.vars, args, self.env)

    def call(self, *args):
        env = Env(self.vars, args, self.env)
        evalResult = eval(self.expBuf, env, False)
        return evalResult

class Obj(Closure):
    def __init__(self, vars, varExps, vals, valExps, parentEnv=None):
        #self.vars = vars
        #self.varExps = varExps
        #self.vals = vals
        #self.valExps = valExps
        #selfEnv = Env(['self'], [self], parentEnv)

        if vars:
            self.valExpEnv = dict(zip(vars, valExps))
            self.env = fnEnv(zip(vars, vals), parentEnv)
        else:
            self.env = None

    def inspect(self):
        pass

    def inspectVar(self, var):
        return self.valExpEnv[var]

    def updateVar(self, var, val):
        newValExpEnv = dict(self.valExpEnv)
        newValExpEnv[var] = buffer.BufferSexp(tn.TNode(val))
        newEnv = self.env.updateDict(var, val)
        return self.updateList(
            ('env', newEnv),
            ('valExpEnv', newValExpEnv))


    def updateVarSource(self, var, newExp):
        varSource = self.valExpEnv[var]
        return varSource.replaceAtCursor(newExp)

    #
    # def toExp(self):
    #     mappingExp = zip(self.varExps, self.valExps)
    #     pyExp = [reader.Symbol('Obj'), mappingExp]
    #     return tn.createTNodeExpFromPyExp(pyExp)

    def call(self, methodName):
        try:
            if methodName == 'update':
                print 'updating'
                return self.updateVar

            # should potentially change it to only re-evaluate if it is a method.
            #ret = self.env.find(methodName)[methodName]
            valExp = self.valExpEnv[methodName]
            ret = eval(valExp, self.env)
        except (LookUpException, KeyError):
            ret = LookUpException(methodName)
        return ret

def isidentifier(exp):
    return isinstance(exp, reader.Symbol)

def islambda(exp):
    return exp.curChildExp() == '^'

def eval(exprBuf, env=global_env, memoize=None):

    exprChild = exprBuf.curChildExp()

    if exprBuf.cursor.quoted:
        ret = exprBuf.cursorToPyExp()

    elif isidentifier(exprChild):             # variable reference
        try:
            ret = env.find(exprChild)[exprChild]
        except EvalException as ex:
            ret = ex

    elif not isa(exprChild, buffer.BufferSexp):         # constant literal
        ret = exprChild

    elif islambda(exprChild):         # (lambda (var*) exp)
        ret = specialFormLambda(exprChild, env, memoize)

    elif exprChild.cursor.child == 'let':
        ret = specialFormLet(exprChild, env, memoize)

    elif exprChild.cursor.child == 'if':
        ret = specialFormIf(exprChild, env, memoize)

    elif exprChild.cursor.child == 'cond':
        ret = specialFormCond(exprChild, env, memoize)

    elif exprChild.cursor.child == 'obj':
        ret = specialFormObj(exprChild, env, memoize)

    elif exprChild.cursor.child == 'quote':
        ret = exprChild.curNext().cursorToPyExp()



    else:  # i.e. a procedure call
        ret = callProcedure(exprChild, env, memoize)

    if memoize:
        memoize(exprBuf.cursor, ret, env)

    return ret

def callProcedure(expBuf, env, memoize):
    childExpr = []
    procExpr = expBuf
    #childExpr = [eval(i, env, memoize) for i in procExpr]
    while True:
        childExpr.append(eval(procExpr, env, memoize))
        try: procExpr = procExpr.curNext()
        except ValueError: break

    for i in childExpr:
        if isinstance(i, Exception):
            return i

    else:
        proc = childExpr.pop(0)
        if isinstance(proc, Closure):
            procVal = proc.call
        elif hasattr(proc, '__call__'):
            procVal = proc
        else:
            return NonProcException(proc)

        try:
            ret = procVal(*childExpr)
        except ZeroDivisionError:
            ret = DivZeroException()
        except TypeError:
            ret = TypeException(childExpr)

    return ret

def specialFormLambda(expBuf, env, memoize):
    try:
        varExp = expBuf.curNext()
        if varExp.onSubNode():
            vars = varExp.cursor.child.toPyExp()
            #vars = expBuf.cursor.next.child.toPyExp()
        else:
            vars = []
        #if not isList(vars):
        #    raise LambdaSyntaxException("Bad Vars Arg")
        bodyExp = expBuf.curNext().curNext()
        ret = Closure('lambda', bodyExp, vars, env)

    except AttributeError:
        ret = LambdaSyntaxException("Err")
    except LambdaSyntaxException as err:
        ret = err

    return ret

def specialFormLet(expBuf, env, memoize):
    valResults = []

    try:
        mapping = expBuf.curNext().curChildExp()

        #build closure
        vars = [pair.child.child for pair in mapping.cursor]
        closure = Env(vars, [None]*len(vars), env)

        pair = mapping
        while True:
            curVal = pair.curChild().curNext()
            curVar = pair.curChild().curChildExp()
            curValResult = eval(curVal, closure, memoize)
            closure.find(curVar)[curVar] = curValResult
            valResults.append(curValResult)
            try:
                pair = pair.curNext()
            except ValueError: break

    except  (AttributeError, ValueError):
        ret = LetSyntaxException("Bad-Var-Syntax")

    else:
        try:
            body = expBuf.curNext().curNext()

        except ValueError:
            ret = LetSyntaxException("NoBody")
        else:
            newEnv = Env(vars, valResults, env)
            ret = eval(body, newEnv, memoize)

    return ret

def specialFormObj(expBuf, env, memoize):
    valResults = []
    valExps = []
    try:
        mapping = expBuf.curNext()
        varExps = [pair.child for pair in mapping.cursor]
        #valExps = [pair.child.next for pair in mapping.cursor]

        #build closure
        vars = []
        for pair in mapping.cursor:
            var = pair.child
            if var.isSubNode():
                raise AttributeError
            else:
                vars.append(var.child)

        selfObj = Obj(None, None, None, None)
        selfClosure = Env(['self', 'update'], [selfObj, selfObj.updateVar], env)

        #closure = Env(vars, [None]*len(vars), selfClosure)
        closure = fnEnv(zip(vars, [None]*len(vars)), selfClosure)

        pair = mapping

        while True:
            curVal = pair.curChild().curNext()
            valExps.append(curVal)
            curVar = pair.curChild().curChildExp()
            curValResult = eval(curVal, closure, memoize)

            closure.find(curVar)[curVar] = curValResult
            valResults.append(curValResult)
            try:
                pair = pair.curNext()
            except ValueError: break

    except  (AttributeError, ValueError):
        ret = LetSyntaxException("Bad-Var-Syntax")
    except LookUpException as e:
        ret = e

    else:
        #newEnv = Env(vars, valResults, env)
        # def Obj(methodName):
        #     try:
        #         ret = newEnv.find(methodName)[methodName]
        #     except LookUpException:
        #         ret = LookUpException(methodName)
        #     return ret

        #ret = Obj

        selfObj.vars = vars
        selfObj.varExps = varExps
        selfObj.vals = valResults
        selfObj.valExps = valExps
        selfObj.valExpEnv = dict(zip(vars, valExps))
        selfObj.env = closure
        return selfObj
        #ret = Obj(vars, varExps, valResults, valExps)


    return ret


def specialFormIf(expBuf, env, memoize):
    negative = None
    try:
        cond = expBuf.curNext()
        positive = expBuf.curNext().curNext()
        try:
            negative = expBuf.curNext().curNext().curNext()
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
                ret = False

    return ret

def specialFormCond(expBuf, env, memoize):

    try:
        condPair = expBuf.curNext()
        while True:
            test = condPair.curChildExp()
            positive = test.curNext()
            testResult = eval(test, env, memoize)

            if isinstance(testResult, Exception):
                return testResult
            elif testResult:    # replace with try
                return eval(positive, env, memoize)
            else:
                try:
                    condPair = condPair.curNext()
                except ValueError:
                    return False

    except ValueError:
        return SyntaxException("Bad Cond Expression")
    except AttributeError:
        return SyntaxException("Bad Cond Expression")
