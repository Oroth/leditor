from unittest import TestCase, main

import eval

class TestEval(TestCase):
    def test_eval1(self):
        result = eval.evalString("(+ 2 2)")
        self.assertEqual(result, 4)

    def test_evalObj(self):
        result = eval.evalString("(obj (a 15))")
        self.assertEqual(type(result), eval.Obj)

    def test_let(self):
        result = eval.evalString("(let ((a 15) (b 16)) (+ a b))")
        self.assertEqual(result, 31)

    def test_let2(self):
        result = eval.evalString("(let ((o (obj (aa 15)))) (+ 11 11))")
        self.assertEqual(result, 22)

    def test_eval2(self):
        txt = "(let ((o (obj (aa 22)))) (o (quote aa)))"
        result = eval.evalString(txt)
        self.assertEqual(result, 22)

    def test_eval3(self):
        txt = "(let ((o (obj (aa 22) (f (^ (x) aa))))) (((o (quote update)) \"aa\" 33) (quote aa)))"
        result = eval.evalString(txt)
        self.assertEqual(result, 33)

    def test_eval4(self):
        txt = "(let ((o (obj (aa 22) (f (^ (x) aa))))) ((((o (quote update)) \"aa\" 33) (quote f)) 10))"
        result = eval.evalString(txt)
        self.assertEqual(result, 33)