__author__ = 'chephren'
import TNode
from Cells import Cell

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

#def vau(clos_env, vars, call_env_sym, body):
#    def closure(call_env, *args):
#        new_env = Env(zip(vars, args), clos_env)
#        new_env[sym] = call_env
#        return eval(body, new_env)
#    return closure

class Closure():
    def __init__(self, clos_env, vars, sym, body):
        self.clos_env = clos_env
        self.vars = vars
        self.sym = sym
        self.body = body

    def __call__(self, call_env, *args):
        new_env = Env(zip(self.vars, args), self.clos_env)
        new_env[self.sym] = call_env
        if not 'self' in args: new_env['self'] = self #safe recursion
        return eval(self.body, new_env)

    def __repr__(self):
        return "vau (%s)"%(','.join(self.vars),)

class EvalNode(TNode.TNode):

    def __init__(self, *args, **kwargs):
        super(EvalNode, self).__init__(*args, **kwargs)

        self.value = None
        self.env = None
        self.history = None

        self.value = {}

    def setValue(self, id, val):
        self.value[id] = val

    def getValue(self, id):
        if self.value.has_key(id):
            return self.value[id]
        else: return None

    def calcEnv(self):
        self.env = global_env

#    def calcValue(self):
#
#        self.calcEnv()
#        x = self.child
#        env = self.env
#        ret = None
#
#        if isa(x, Symbol):             # variable reference
#            ret = env.find(x)[x]
#        elif not isa(x, list):         # constant literal
#            ret = x
#        elif x[0] == 'quote':          # (quote exp)
#            (_, exp) = x
#            ret = exp
#        elif x[0] == 'if':             # (if test conseq alt)
#            (_, test, conseq, alt) = x
#            ret = eval((conseq if eval(test, env) else alt), env)
#        elif x[0] == 'set!':           # (set! var exp)
#            (_, var, exp) = x
#            env.find(var)[var] = eval(exp, env)
#        elif x[0] == 'define':         # (define var exp)
#            (_, var, exp) = x
#            env[var] = eval(exp, env)
#        elif x[0] == 'lambda':         # (lambda (var*) exp)
#            (_, vars, exp) = x
#            ret = lambda *args: eval(exp, Env(vars, args, env))
#        elif x[0] == 'begin':          # (begin exp*)
#            for exp in x[1:]:
#                val = eval(exp, env)
#            ret = val
#        else:                          # (proc exp*)
#            exps = [eval(exp, env) for exp in x]
#            proc = exps.pop(0)
#            ret = proc(*exps)
#
#        self.value = ret

    def calcValue(self, id, env=global_env):
        #self.value = self.eval(env)
        self.setValue(id, self.eval(id, env))

    def eval(self, id, env=global_env, memoize=True, ignoreQuote=False):

        #self.calcEnv()
        x = self.child
        ret = None

        if not self.evaled and not ignoreQuote:
            ret = self.activeToPySexp()

        elif isa(x, Symbol):             # variable reference
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
                        return exp.eval(id, Env(vars, args, env), False)

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
                    valResults.append(val.eval(id, env))
            except AttributeError:
                ret = LetSyntaxException("Bad-Var-Syntax")

            else:
                body = x.next.next
                if body:
                    ret = body.eval(id, Env(vars, valResults, env))
                else:
                    ret = LetSyntaxException("NoBody")

        else:  # i.e. a Tnode
            childExpr = []
            for i in self.child:
                childExpr.append(i.eval(id, env, memoize))

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
            self.setValue(id, ret)

        return ret


