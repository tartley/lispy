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

    def test_cons_should_prepend_to_existing_list(self):
        cons = get_builtins()['cons']
        self.assertEqual(cons(1, [2, 3]), [1, 2, 3])

    def test_cons_is_unable_to_make_a_pair_like_it_ought_to(self):
        cons = get_builtins()['cons']
        with self.assertRaises(TypeError) as cm:
            cons(1, 2)

    def test_car(self):
        car = get_builtins()['car']
        self.assertEqual(car([1, 2, 3]), 1)

    def test_cdr(self):
        cdr = get_builtins()['cdr']
        self.assertEqual(cdr([1, 2, 3]), [2, 3])

    def test_list(self):
        list_ = get_builtins()['list']
        self.assertEqual(list_(1, 2, 3), [1, 2, 3])

    def test_islist(self):
        islist = get_builtins()['list?']
        self.assertFalse(islist(1))
        self.assertFalse(islist('a'))
        self.assertTrue(islist([1]))

    def test_isnull(self):
        isnull = get_builtins()['null?']
        self.assertFalse(isnull(1))
        self.assertFalse(isnull('a'))
        self.assertFalse(isnull([1]))
        self.assertTrue(isnull([]))

    def test_issymbol(self):
        issymbol = get_builtins()['symbol?']
        self.assertFalse(issymbol(1))
        self.assertFalse(issymbol([1]))
        self.assertFalse(issymbol([]))
        self.assertTrue(issymbol('a'))

    def test_operators(self):
        data = [
            ('not', op.not_),
            ('/', op.truediv),
            ('=', op.eq),
            ('equal?', op.eq),
            ('eq?', op.is_),
            ('>', op.gt),
            ('<', op.lt),
            ('>=', op.ge),
            ('<=', op.le), 
            ('length', len),
            ('append', op.add),
            ('display', print),
        ]
        for name, expected in data:
            actual = get_builtins()[name]
            self.assertIs(actual, expected, 'bad "%s"' % (name,))


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
        with self.assertRaises(SyntaxError) as cm:
            expr_from_tokens([])
        self.assertEqual(str(cm.exception), 'Unexpected EOF at start of expression')

        with self.assertRaises(SyntaxError) as cm:
            expr_from_tokens(['('])
        self.assertEqual(str(cm.exception), 'Unexpected EOF mid expression')

        with self.assertRaises(SyntaxError) as cm:
            expr_from_tokens([')'])
        self.assertEqual(str(cm.exception), 'Unexpected ")"')


    def test_expr_from_tokens(self):
        self.assertEqual(
            expr_from_tokens(['(', '1', '2', '3', ')']),
            [1, 2, 3]
        )

        with self.assertRaises(SyntaxError) as cm:
            eval_string('(')
        with self.assertRaises(SyntaxError):
            expr_from_tokens([')'])
        self.assertEqual(str(cm.exception), 'Unexpected ")"')

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


class TestEvalExpr(TestCase):

    def test_eval_expr_constant_literals(self):
        self.assertEqual(eval_expr(123), 123)
        self.assertEqual(eval_expr(1.23), 1.23)

    def test_eval_expr_variable_reference(self):
        self.assertEqual(eval_expr('x', Env({'x':123})), 123)

    def test_eval_expr_quote(self):
        self.assertEqual(eval_expr(['quote', 123]), 123)
        self.assertEqual(eval_expr(['quote', 'abc']), 'abc')
        self.assertEqual(eval_expr(['quote', ['+', 2, 3]]), ['+', 2, 3])

    def test_eval_expr_if(self):
        self.assertEqual(eval_expr(['if', 1, 123, 456]), 123)
        self.assertEqual(eval_expr(['if', 0, 123, 456]), 456)

    def test_eval_expr_if_evaluates_pred_conseq_and_alt(self):
        env = Env({'t':1, 'f':0, 'conseq':123, 'alt':456})
        self.assertEqual(eval_expr(['if', 't', 'conseq', 'undef'], env), 123)
        self.assertEqual(eval_expr(['if', 'f', 'undef', 'alt'], env), 456)

    def test_eval_expr_set(self):
        env = Env({'var': 0})
        self.assertIsNone(eval_expr(['set!', 'var', 789], env))
        self.assertEqual(env['var'], 789)

    def test_eval_expr_set_modified_defining_env(self):
        outer = Env({'var': 0})
        inner = Env({}, outer)
        self.assertIsNone(eval_expr(['set!', 'var', 789], inner))
        self.assertEqual(inner, {})
        self.assertEqual(outer, {'var': 789})

    def test_eval_expr_set_raises_on_new(self):
        with self.assertRaises(NameError):
            eval_expr(['set!', 'new_variable', 0])

    def test_eval_expr_define(self):
        env = Env({'var': 0})
        self.assertIsNone(eval_expr(['define', 'var', 789], env))
        self.assertEqual(env['var'], 789)

    def test_eval_expr_define_modifies_current_env(self):
        outer = Env({'var': 0})
        inner = Env({}, outer)
        self.assertIsNone(eval_expr(['define', 'var', 789], inner))
        self.assertEqual(inner, {'var': 789})
        self.assertEqual(outer, {'var': 0})

    def test_eval_expr_lambda(self):
        procedure = eval_expr(['lambda', 'x', ['+', 'x', 4]])
        self.assertEqual(procedure(10), 14)

        procedure = eval_expr(['lambda', ['x'], ['+', 'x', 4]])
        self.assertEqual(procedure(10), 14)

        procedure = eval_expr(['lambda', ['x', 'y'], ['+', 'x', 'y', 4]])
        self.assertEqual(procedure(10, 20), 34)

    def test_eval_expr_begin(self):
        with self.assertRaises(SyntaxError):
            eval_expr(['begin'])

        self.assertEqual(eval_expr(['begin', 1, 2, 3]), 3)

    def test_eval_expr_proc(self):
        env = Env({'x': op.add, 'a': 111, 'b': 222})
        self.assertEqual(eval_expr(['x', 'a', 'b'], env), 333)
        
        with self.assertRaises(TypeError) as cm:
            eval_expr(['a', 'b'], env)
        self.assertEqual(
            str(cm.exception),
            'Expression "a" (int) not callable in "(a b)"')


class TestToString(TestCase):

    def test_to_string(self):
        self.assertEqual(to_string(123), '123')
        self.assertEqual(to_string([1, 2, 3]), '(1 2 3)')
        self.assertEqual(to_string([1, [2, 3], 4]), '(1 (2 3) 4)')


class TestEvalString(TestCase):

    def test_eval_string(self):
        data = [
            ('100', 100),
            ('100 200', 200),
            ('(+ 1 2 (+ 30 40 50) 3)', 126),
            ('(* 2 3 (* 5 6 7) 4)', 5040),
            ('(- 100 (- (- 50 20) 5))', 75),
            ('(/ 360 (/ (/ 60 2) 10))', 120),
        ]
        for string, value in data:
            self.assertEqual(eval_string(string), value)

    def test_eval_string_with_vars(self):
        env = Env({'a':2, 'b':30, 'c':4}, global_env)
        self.assertEqual(eval_string('(+ a 3 (+ b 40 50) c)', env), 129)

    def test_eval_string_lambda(self):
        proc = eval_string('(lambda (x) (+ x 4))')
        self.assertEqual(proc(10), 14)

    def test_eval_string_define_procedure(self):
        area = eval_string('''
            (define pi 3.14159)
            (define area (lambda (r) (* pi (* r r))))
            (area 3)
        ''')
        self.assertEqual(area, 28.27431)

    def test_eval_string_recursion(self):
        area = eval_string('''
            (define fact (lambda n (if (<= n 1) 1 (* n (fact (- n 1))))))
            (fact 10)
        ''')
        self.assertEqual(area, 3628800)

        expected = 93326215443944152681699238856266700490715968264381621468592963895217599993229915608941463976156518286253697920827223758251185210916864000000000000000000000000
        self.assertEqual(eval_string('(fact 100)'), expected)

    def test_eval_string_car_cdr(self):
        count = eval_string('''
            (define first car)
            (define rest cdr)
            (define count (
                lambda (item L)
                    (if L
                        (+ (equal? item (first L)) (count item (rest L)))
                        0
                    )
            ) )
            (count 0 (list 0 1 2 3 0 0))
        ''')
        self.assertEqual(count, 3)

        count2 = eval_string('''
            (count
                (quote the)
                (quote (the more the merrier the bigger the better))
            )
        ''')
        self.assertEqual(count2, 4)


if __name__ == '__main__':
    main()

