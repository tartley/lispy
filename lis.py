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
        '+': lambda *args: reduce(op.add, args),
        '-': sub,
        '*': mul,
        '/': op.truediv,
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
    'Convert list of tokens into an expression'
    if len(tokens) == 0:
        raise SyntaxError('Unexpected EOF while reading')
    token = tokens.pop(0)
    if token == '(':
        expr = []
        while tokens[0] != ')':
            expr.append( expr_from_tokens(tokens) )
        tokens.pop(0) # pop final ')'
        return expr
    elif token == ')':
        raise SyntaxError('unexpected ")"')
    else:
        return atom(token)


def parse(s):
    'Read a Scheme expression from a string'
    return expr_from_tokens(tokenize(s))


# eval

def eval_expr(expr, env=global_env):
    'Evaluate an expression in an environment.'
    if isinstance(expr, Symbol):
        defining_env = env.find(expr)
        if defining_env:
            return defining_env[expr]
        else:
            raise NameError(expr)
    elif not isinstance(expr, list):
        return expr
    elif expr[0] == 'quote':
        _, value = expr
        return value
    elif expr[0] == 'if':
        _, pred, conseq, alt = expr
        return eval_expr((conseq if eval_expr(pred, env) else alt), env)
    elif expr[0] == 'set!':
        (_, var, value) = expr
        env.find(var)[var] = eval_expr(value, env)
    else:
        values = [eval_expr(subexpr, env) for subexpr in expr]
        proc = values.pop(0)
        return proc(*values)


# repl

def to_string(expr):
    if isinstance(expr, list):
        return '(' + ' '.join(map(to_string, expr)) + ')'
    else:
        return str(expr)


def repl(prompt='lis> '):
    while True:
        val = eval_expr(parse(input(prompt)))
        if val is not None:
            print(to_string(val))


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

    if args.sourcefile:
        source = args.sourcefile.read()
        eval_expr(parse(source))


if __name__ == '__main__':
    main(sys.argv)

