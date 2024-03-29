#!/usr/bin/env python3

from argparse import ArgumentParser, FileType
import sys
from functools import reduce
import operator as op


# Symbol

Symbol = str


# Env


class Env(dict):
    '''
    Stores the name-value pairs of a context.
    Construct as either: Env({'a': 123}) or Env(params=('a',), args=(123,))
    '''
    def __init__(self, values=None, outer=None):
        if values:
            self.update(values)
        self.outer = outer

    def find(self, var):
        if var in self:
            return self
        elif self.outer:
            return self.outer.find(var)
        raise NameError('Unbound variable "%s"' % (var,))


# built-ins

def sub(*args):
    if len(args) == 1:
        return -args[0]
    if len(args) == 2:
        return args[0] - args[1]
    raise TypeError(''-' needs 1 or 2 args, not %d %s' % (len(args), args,))


def mul(*args):
    if len(args) > 1:
        return reduce(op.mul, args)
    raise TypeError(''*' needs 2 or more args, not %d %s' % (len(args), args,))


def get_builtins():
    return {
        # logical
        'not': op.not_,

        # arithmetic
        '+': lambda *args: reduce(op.add, args),
        '-': sub,
        '*': mul,
        '/': op.truediv,

        # comparison
        '=': op.eq,
        'equal?': op.eq,
        'eq?': op.is_,
        '>': op.gt,
        '<': op.lt,
        '>=': op.ge,
        '<=': op.le, 

        # pairs
        'cons': lambda x,y: [x]+y,
        'car': lambda x: x[0],
        'cdr': lambda x: x[1:],

        # lists
        'length': len,
        'append': op.add,
        'list': lambda *x: list(x),

        # is-a
        'list?': lambda x: isinstance(x,list), 
        'null?': lambda x: x==[],
        'symbol?':lambda x: isinstance(x, Symbol),
        
        # IO
        'display': print,
    }


global_env = Env(get_builtins())


# parse

def tokenize(s):
    'Convert string into a list of tokens'
    return s.replace('(', ' ( ').replace(')', ' ) ').split()


def atom(token):
    'Convert a token into an atom'
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token)


def expr_from_tokens(tokens):
    "Pop a complete expression from the start of 'tokens', and return it."
    if len(tokens) == 0:
        raise SyntaxError('Unexpected EOF at start of expression')
    token = tokens.pop(0)
    if token == '(':
        expr = []
        while tokens and tokens[0] != ')':
            expr.append( expr_from_tokens(tokens) )
        if len(tokens) == 0:
            raise SyntaxError('Unexpected EOF mid expression')
        tokens.pop(0) # discard final ')'
        return expr
    elif token == ')':
        raise SyntaxError('Unexpected ")"')
    else:
        return atom(token)


def parse(s):
    'Yield a sequence of Scheme expressions from a string'
    tokens = tokenize(s)
    while tokens:
        yield expr_from_tokens(tokens)


# eval

def eval_expr(expr, env=global_env):
    'Evaluate an expression in an environment. Defines special forms.'

    if isinstance(expr, Symbol):
        defining_env = env.find(expr)
        if defining_env:
            return defining_env[expr]
        else:
            raise NameError(expr)

    elif not isinstance(expr, list):
        # constant literal
        return expr

    elif expr[0] == 'quote':
        # (quote <value>)
        _, value = expr
        return value

    elif expr[0] == 'if':
        # (if <predicate> <consequent> <alternate>)
        _, pred, conseq, alt = expr
        return eval_expr((conseq if eval_expr(pred, env) else alt), env)

    elif expr[0] == 'set!':
        # (set! <name> <value>)
        (_, name, value) = expr
        env.find(name)[name] = eval_expr(value, env)

    elif expr[0] == 'define':
        # (define <name> <value>)
        (_, name, value) = expr
        env[name] = eval_expr(value, env)

    elif expr[0] == 'lambda':
        # (lambda (<arg> [<arg>...]) <body>) or (lambda <arg> <body>)
        (_, args, body) = expr
        return lambda *params: eval_expr(body, Env(zip(args, params), env))

    elif expr[0] == 'begin':
        # (begin <expr> [<expr>...])
        if len(expr) <= 1:
            raise SyntaxError('"begin" with no contents')
        for subexpr in expr[1:]:
            val = eval_expr(subexpr, env)
        return val

    else:
        # procedure invocation, (<proc> arg1 arg2...)
        values = [eval_expr(subexpr, env) for subexpr in expr]
        proc = values.pop(0)
        if callable(proc):
            return proc(*values)
        else:
            raise TypeError(
                'Expression "%s" (%s) not callable in "%s"'
                % (expr[0], type(proc).__name__, to_string(expr))
            )


def eval_string(string, env=global_env):
    value = None
    for expr in parse(string):
        value = eval_expr(expr, env)
    return value


# repl

def to_string(expr):
    if isinstance(expr, list):
        return '(' + ' '.join(map(to_string, expr)) + ')'
    else:
        return str(expr)


def repl(prompt='lis> '):
    while True:
        try:
            value = eval_string(input(prompt))
        except EOFError:
            break
        if value is not None:
            print(to_string(value))
    print()


# command-line processing

def get_parser():
    parser = ArgumentParser(
        description='Load data into the Rangespan catalog')
    parser.add_argument('-v', '--version',
        action='store_true',
        help='Show version number and exit.'
    )
    parser.add_argument(
        'sourcefile',
        nargs='?',
        type=FileType('rU'),
        default=sys.stdin,
        help='Lispy source code filename.')
    return parser


VERSION = '0.1'

def main(argv):

    parser = get_parser()
    args = parser.parse_args()

    if args.version:
        print('v%s' % (VERSION,))
        sys.exit(0)

    if sys.stdin.isatty() and args.sourcefile == sys.stdin:
        repl()
    else:
        eval_string(args.sourcefile.read())


if __name__ == '__main__':
    main(sys.argv)

