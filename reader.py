from __future__ import division
import re
__author__ = 'chephren'

def readFile(fname):
    f = open(fname, 'r')
    ret = read(f.read())
    f.close()
    return ret

#def read(s):
#    "Read a Scheme expression from a string."
#    return read_from(tokenize(s))



def loadFile(filename):
    "Eval every expression from a file."
    inport = InPort(open(filename))
    return read(inport)
#        except Exception as e:
#            print '%s: %s' % (type(e).__name__, e)

isa = isinstance

class Symbol(str):
    def __getslice__(self, *args, **kargs):
        return Symbol(super(Symbol, self).__getslice__(*args, **kargs))


def Sym(s, symbol_table={}):
    "Find or create unique Symbol entry for str s in symbol table."
    if s not in symbol_table: symbol_table[s] = Symbol(s)
    return symbol_table[s]

_quote, _if, _set, _define, _lambda, _begin, _definemacro, = map(Sym,
    "quote   if   set!  define   lambda   begin   define-macro".split())

_quasiquote, _unquote, _unquotesplicing = map(Sym,
    "quasiquote   unquote   unquote-splicing".split())


class InPort(object):
    "An input port. Retains a line of chars."
    tokenizer = r'''\s*(,@|[('`,)]|"(?:[\\].|[^\\"])*"|;.*|[^\s('"`,;)]*)(.*)'''
    def __init__(self, file):
        self.file = file; self.line = ''
    def next_token(self):
        "Return the next token, reading new text into line buffer if needed."
        while True:
            if self.line == '': self.line = self.file.readline()
            if self.line == '': return eof_object
            token, self.line = re.match(InPort.tokenizer, self.line).groups()
            if token != '' and not token.startswith(';'):
                return token


eof_object = Symbol('#<eof-object>') # Note: uninterned; can't be read

def readchar(inport):
    "Read the next character from an input port."
    if inport.line != '':
        ch, inport.line = inport.line[0], inport.line[1:]
        return ch
    else:
        return inport.file.read(1) or eof_object

def read(inport):
    "Read a Scheme expression from an input port."
    def read_ahead(token):
        if '(' == token:
            L = []
            while True:
                token = inport.next_token()
                if token == ')': return L
                else: L.append(read_ahead(token))
        elif ')' == token: raise SyntaxError('unexpected )')
        elif token in quotes: return [quotes[token], read(inport)]
        elif token is eof_object: raise SyntaxError('unexpected EOF in list')
        else: return atom(token)
        # body of read:
    token1 = inport.next_token()
    return eof_object if token1 is eof_object else read_ahead(token1)

quotes = {"'":_quote, "`":_quasiquote, ",":_unquote, ",@":_unquotesplicing}

def atom(token):
    'Numbers become numbers; #t and #f are booleans; "..." string; otherwise Symbol.'
    if token == '#t': return True
    elif token == '#f': return False
    elif isa(token, str) and len(token) > 0 and token[0] == '"':
        return token[1:-1].decode('string_escape')
    try: return int(token)
    except ValueError:
        try: return float(token)
        except ValueError:
            try: return complex(token.replace('i', 'j', 1))
            except ValueError:
                return Symbol(token)

def to_string(x):
    "Convert a Python object back into a Lisp-readable string."
    if x is True: return "#t"
    elif x is False: return "#f"
    elif isa(x, Symbol): return str(x)
    elif isa(x, str): return '"%s"' % x.encode('string_escape').replace('"',r'\"')
    elif isa(x, (list, tuple)): return '('+' '.join(map(to_string, x))+')'
    elif isa(x, complex): return str(x).replace('j', 'i')
    elif isa(x, dict): return '(dict (quote ('+' '.join(map(to_string, x.items()))+')))'
    elif x is None: return '()'
    else: return str(x)
