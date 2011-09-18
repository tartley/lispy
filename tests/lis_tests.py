#!/usr/bin/env python3

from unittest import main, TestCase

import fixpath
from lis import (
    atom, Env, eval_expr, expr_from_tokens, parse, Symbol, to_string, tokenize,
)


class TestSymbol(TestCase):

    def test_symbol_isa_string(self):
        self.assertTrue(isinstance(Symbol(), str))


class TestEnv(TestCase):

    def test_env_isa_dict(self):
        self.assertTrue(isinstance(Env(), dict))

    def test_constructor_defaults(self):
        env = Env()
        self.assertEqual(env, {})
        self.assertIsNone(env.outer)
    
    def test_constructor_from_tuples(self):
        outer = Env()
        inner = Env(('a', 'b', 'c'), (1, 2, 3), outer)
        self.assertEqual(inner, {'a':1, 'b':2, 'c':3})
    
    def test_constructor_from_dict(self):
        values = {'d':4, 'e':5, 'f':6}
        self.assertEqual(Env(values), values)

    def test_find(self):
        outer = Env(('def',), (0,))
        inner = Env(('abc',), (0,), outer)
        self.assertEqual(inner.find('abc'), inner)
        self.assertEqual(inner.find('def'), outer)
        self.assertIsNone(inner.find('ghi'))


class TestEval(TestCase):

    def test_variable_reference(self):
        self.assertEqual(eval_expr('x', Env(('x',), (123,))), 123)

    def test_constant_literal(self):
        self.assertEqual(eval_expr(123), 123)

    def test_quote_expr(self):
        self.assertEqual(eval_expr(['quote', 456]), 456)

    def test_if_pred_conseq_alt(self):
        env = Env(('t', 'f'), (True, False))
        self.assertEqual(eval_expr(['if', 't', 123, 456], env), 123)
        self.assertEqual(eval_expr(['if', 'f', 123, 456], env), 456)

    def test_set_var_expr(self):
        env = Env(('var',), (0,))
        self.assertIsNone(eval_expr(['set!', 'var', 789], env))
        self.assertEqual(env['var'], 789)

   
class TestParse(TestCase):

    def test_tokenise(self):
        self.assertEqual(
            tokenize('(set var 123)'),
            ['(', 'set', 'var', '123', ')']
        )

    def test_atom(self):
        self.assertEqual(atom('123'), 123)
        self.assertEqual(atom('123.456'), 123.456)
        self.assertEqual(atom('abc'), Symbol('abc'))

    def test_expr_from_tokens_raises(self):
        with self.assertRaises(SyntaxError):
            expr_from_tokens([])
        with self.assertRaises(SyntaxError):
            expr_from_tokens([')'])

    def test_expr_from_tokens(self):
        self.assertEqual(expr_from_tokens(['(', '1', '2', '3', ')']), [1, 2, 3])

    def test_read(self):
        self.assertEqual(parse('( 1 2 3 )'), [1, 2, 3])


class TestRepl(TestCase):

    def test_to_string(self):
        self.assertEqual(to_string(123), '123')
        self.assertEqual(to_string([1, 2, 3]), '(1 2 3)')
        self.assertEqual(to_string([1, [2, 3], 4]), '(1 (2 3) 4)')


if __name__ == '__main__':
    main()

