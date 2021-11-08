import unittest
import os, sys
from bxast import BinopApp, Vardecl
dirname, filename = os.path.split(os.path.abspath(__file__))

from scanner import lexer, loadsrc
from parser import parser

class testParser(unittest.TestCase):
    def test_parse_diagonal(self):
        fname = "diagonal.bx"
        with open(f"{dirname}/examples/{fname}", 'r') as f:
            ast = parser.parse(f.read(), lexer=lexer)
            ast.check_syntax()
            lexer.lineno = 1

    def test_parse_arithops(self):
        fname = "lab1/arithops.bx"
        with open(f"{dirname}/examples/{fname}", 'r') as f:
            ast = parser.parse(f.read(), lexer=lexer)
            lexer.lineno = 1

    def test_parse_boolops(self):
        fname = "boolops.bx"
        with open(f"{dirname}/examples/{fname}", 'r') as f:
            ast = parser.parse(f.read(), lexer=lexer)
            ast.check_syntax()
            lexer.lineno = 1


    def test_parse_scopevars(self):
        fname = "scopevars.bx"
        with open(f"{dirname}/examples/{fname}", 'r') as f:
            ast = parser.parse(f.read(), lexer=lexer)
            ast.check_syntax()
            lexer.lineno = 1

class testPrecedence(unittest.TestCase):
    def setUp(self):
        with open(f"{dirname}/examples/smallcond2.bx", 'r') as f:
            boolast = parser.parse(f.read(), lexer=lexer)
            boolast.check_syntax()
        self.booland = boolast.procedures[0].statements[2].condition

        with open(f"{dirname}/examples/lab2/arithops.bx", 'r') as f:
            ast = parser.parse(f.read(), lexer=lexer)
            ast.check_syntax()
        self.plus = ast.procedures[0].statements[4].variables[0][1]

    def test_precedence_bool(self):
        self.assertIsInstance(self.booland, BinopApp)
        self.assertEqual(self.booland.op.name, "BOOLAND")

    def test_precedence_arith(self):
        self.assertIsInstance(self.plus, BinopApp)
        self.assertEqual(self.plus.op.name, "PLUS")
        times = self.plus.arg1
        self.assertIsInstance(times, BinopApp)
        self.assertEqual(times.op.name, "TIMES")

class expectedSyntaxError(unittest.TestCase):
    @unittest.expectedFailure
    def test_parses_incorectop(self):
        fname = "incorectop.bx"
        with open(f"{dirname}/regression/{fname}") as fn:
            ast = parser.parse(fn.read(), lexer=lexer)
            ast.check_syntax()
            lexer.lineno = 1

if __name__ == "__main__":
    unittest.main()
