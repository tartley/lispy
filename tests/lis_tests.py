#!/usr/bin/env python3

from os import path
import operator as op
import sys
from unittest import main, TestCase

# Append parent dir to sys.path so that tests can import from it
sys.path.insert(0, path.abspath(path.join(path.dirname(__file__), '..')))

from lis import (
    atom, Env, eval_expr, eval_string, expr_from_tokens, get_builtins,
    global_env, parse, Symbol, to_string, tokenize,
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
    
    def test_constructor_from_dict(self):
        values = {'d':4, 'e':5, 'f':6}
        self.assertEqual(Env(values), values)

    def test_find(self):
        outer = Env({'def':0})
        inner = Env({'abc':0}, outer)
        self.assertEqual(inner.find('abc'), inner)
        self.assertEqual(inner.find('def'), outer)
        with self.assertRaises(NameError):
            inner.find('ghi')


class TestBuiltins(TestCase):

    def test_add(self):
        add = get_builtins()['+']
        with self.assertRaises(TypeError):
            add()
        self.assertEqual(add(3), 3)
        self.assertEqual(add(3, 2), 5)
        self.assertEqual(add(3, 2, 1), 6)


    def test_sub(self):
        sub = get_builtins()['-']
        with self.assertRaises(TypeError):
            sub()
        self.assertEqual(sub(123), -123)
        self.assertEqual(sub(10, 2), 8)
        with self.assertRaises(TypeError):
            sub(1, 2, 3)


    def test_mul(self):
        mul = get_builtins()['*']
        with self.assertRaises(TypeError):
            mul()
        with self.assertRaises(TypeError):
            mul(123)
        self.assertEqual(mul(3, 2), 6)
        self.assertEqual(mul(4, 3, 2), 24)


    def test_div(self):
        div = get_builtins()['/']
        with self.assertRaises(TypeError):
            div()
        with self.assertRaises(TypeError):
            div(123)
        self.assertEqual(div(10, 2), 5)
        self.assertAlmostEqual(div(10, 3), 3.3333333)
        with self.assertRaises(TypeError):
            div(1, 2, 3)


    def test_display(self):

        calls = []
        def mock_print(*args):
            calls.append(args)

        import lis
        lis.print = mock_print
        try:
            display = get_builtins()['display']
            argslist = [
                (),
                (1,),
                ('a',),
                (1, 'a'),
            ]
            for args in argslist:
                self.assertIsNone(display(*args))
                self.assertEqual(calls[-1], args)
        finally:
            lis.print = print


class TestEval(TestCase):

    def test_variable_reference(self):
        self.assertEqual(eval_expr('x', Env({'x':123})), 123)

    def test_constant_literal(self):
        self.assertEqual(eval_expr(123), 123)

    def test_quote_expr(self):
        self.assertEqual(eval_expr(['quote', 456]), 456)

    def test_if_pred_conseq_alt(self):
        env = Env({'t':True, 'f':False})
        self.assertEqual(eval_expr(['if', 't', 123, 456], env), 123)
        self.assertEqual(eval_expr(['if', 'f', 123, 456], env), 456)

    def test_set_var_expr(self):
        env = Env({'var': 0})
        self.assertIsNone(eval_expr(['set!', 'var', 789], env))
        self.assertEqual(env['var'], 789)

    def test_procedure_invocation(self):
        env = Env({
            'x': op.add,
            'a': 111,
            'b': 222,
        })
        self.assertEqual(eval_expr(['x', 'a', 'b'], env), 333)


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
        self.assertEqual(
            expr_from_tokens(['(', '1', '2', '3', ')']),
            [1, 2, 3]
        )

    def test_expr_from_tokens_returns_first_expression_only(self):
        tokens = ['(', '1', '2', ')', '(', '3', ')']
        self.assertEqual(expr_from_tokens(tokens), [1, 2])
        self.assertEqual(tokens, ['(', '3', ')'])

    def test_parse_single_expr(self):
        self.assertEqual(list(parse('(1 2 3)')), [[1, 2, 3]])

    def test_parse_multiple_expr(self):
        self.assertEqual(list(parse('(1 2)(3)')), [[1, 2], [3]])


class TestRepl(TestCase):

    def test_to_string(self):
        self.assertEqual(to_string(123), '123')
        self.assertEqual(to_string([1, 2, 3]), '(1 2 3)')
        self.assertEqual(to_string([1, [2, 3], 4]), '(1 (2 3) 4)')


class TestEvalString(TestCase):

    def test_eval_string_errors(self):
        with self.assertRaises(SyntaxError) as cm:
            eval_string(')')
        self.assertEqual(str(cm.exception), 'Unexpected ")"')

        with self.assertRaises(SyntaxError) as cm:
            eval_string('(')
        self.assertEqual(str(cm.exception), 'Unexpected EOF mid expression')

    def test_eval_string_literals(self):
        self.assertEqual(eval_string('123'), 123)
        self.assertEqual(eval_string('1.23'), 1.23)

    def test_eval_string_multiple_expressions(self):
        self.assertEqual(eval_string('100 200'), 200)

    def test_eval_string_arithmetic(self):
        data = [
            ('(+ 1 2 (+ 30 40 50) 3)', 126),
            ('(* 2 3 (* 5 6 7) 4)', 5040),
            ('(- 100 (- (- 50 20) 5))', 75),
            ('(/ 360 (/ (/ 60 2) 10))', 120),
        ]
        for string, value in data:
            self.assertEqual(eval_string(string), value)

    def test_eval_string_arithmetic_with_vars(self):
        env = Env({'a':2, 'b':30, 'c':4}, global_env)
        self.assertEqual(eval_string('(+ a 3 (+ b 40 50) c)', env), 129)

    def test_eval_string_quote(self):
        self.assertEqual(eval_string('(quote abc)'), 'abc')
        self.assertEqual(eval_string('(quote 123)'), 123)
        self.assertEqual(eval_string('(quote (1 2 3))'), [1, 2, 3])
        self.assertEqual(eval_string('(quote (+ 2 3))'), ['+', 2, 3])
        
    def test_eval_string_if(self):
        self.assertEqual(eval_string('(if 1 123 456)'), 123)
        self.assertEqual(eval_string('(if 0 123 456)'), 456)
        env = Env({'true':1, 'false':0, 'conseq':123, 'alt':456})
        self.assertEqual(eval_string('(if true conseq undefined)', env), 123)
        self.assertEqual(eval_string('(if false undefined alt)', env), 456)

    def test_eval_string_set(self):
        env = Env({'x':123})
        self.assertIsNone(eval_string('(set! x 456)', env))
        self.assertEqual(env['x'], 456)

        with self.assertRaises(NameError):
            eval_string('(set! y 0)')


if __name__ == '__main__':
    main()

