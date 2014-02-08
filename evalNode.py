__author__ = 'chephren'
import TNode

isa = isinstance

class Symbol(str): pass

class Env(dict):
    "An environment: a dict of {'var':val} pairs, with an outer Env."
    def __init__(self, parms=(), args=(), outer=None):
        self.update(zip(parms,args))
        self.outer = outer
    def find(self, var):
        "Find the innermost Env where var appears."
        return self if var in self else self.outer.find(var)

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
         'null?':lambda x:x==[], 'symbol?':lambda x: isa(x, Symbol)})
    return env

class EvalNode(TNode.TNode):


    def calcValue(self):

        x = self.child
        env = self.env
        if isa(x, Symbol):             # variable reference
            ret = env.find(x)[x]
        elif not isa(x, list):         # constant literal
            ret = x
        elif x[0] == 'quote':          # (quote exp)
            (_, exp) = x
            ret = exp
        elif x[0] == 'if':             # (if test conseq alt)
            (_, test, conseq, alt) = x
            ret = eval((conseq if eval(test, env) else alt), env)
        elif x[0] == 'set!':           # (set! var exp)
            (_, var, exp) = x
            env.find(var)[var] = eval(exp, env)
        elif x[0] == 'define':         # (define var exp)
            (_, var, exp) = x
            env[var] = eval(exp, env)
        elif x[0] == 'lambda':         # (lambda (var*) exp)
            (_, vars, exp) = x
            ret = lambda *args: eval(exp, Env(vars, args, env))
        elif x[0] == 'begin':          # (begin exp*)
            for exp in x[1:]:
                val = eval(exp, env)
            ret = val
        else:                          # (proc exp*)
            exps = [eval(exp, env) for exp in x]
            proc = exps.pop(0)
            ret = proc(*exps)

        self.value = ret