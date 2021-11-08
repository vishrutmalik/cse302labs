import unittest
import os, sys
dirname, filename = os.path.split(os.path.abspath(__file__))

from scanner import lexer, loadsrc

class TestTokenStream(unittest.TestCase):
    def test_lexes(self):
        files = ["diagonal.bx", "boolops.bx", "lab2/arithops.bx"]

        for file in files:
            with open(f"{dirname}/../examples/{file}", 'r') as f:
                loadsrc(f.read())

            while True:
                tok = lexer.token()
                if not tok: 
                    break      # No more input

class testLexerLineno(unittest.TestCase):
    def test_endline_comment(self):
        linenb = 0
        with open(f"{dirname}/../examples/lab2/interstitialcomment.bx", 'r') as fn:
            loadsrc(fn.read())
        while True:
            tok = lexer.token()
            if tok:
                linenb = tok.lineno
            if not tok: 
                self.assertEqual(linenb, 5)
                break      # No more input
    def test_middle_comment(self):
        linenb = 0
        with open(f"{dirname}/../examples/lab2/middlecomment.bx", 'r') as fn:
            loadsrc(fn.read())
        while True:
            tok = lexer.token()
            if tok:
                linenb = tok.lineno
            if not tok: 
                self.assertEqual(linenb, 4)
                break      # No more input

    def test_firstline_comment(self):
        linenb = 0
        with open(f"{dirname}/../examples/lab2/simplecomment.bx", 'r') as fn:
            loadsrc(fn.read())
        while True:
            tok = lexer.token()
            if tok:
                linenb = tok.lineno
            if not tok:
                self.assertEqual(linenb, 4)
                break      # No more input

class testLexerBehaviour(unittest.TestCase):
    def test_lexing_scopevars(self):
        fname = "scopevars.bx"
        with open(f"{dirname}/../examples/{fname}") as fn:
            loadsrc(fn.read())
        res = []
        while True:
            tok = lexer.token()
            if tok:
                res.append(tok.type)
            if not tok:
                break
        tokenlist = ['DEF',
                     'MAIN',
                     'LPAREN',
                     'RPAREN',
                     'LBRACE',
                     'VAR',
                     'IDENT',
                     'EQ',
                     'NUMBER',
                     'COLON',
                     'INT',
                     'SEMICOLON',
                     'LBRACE',
                     'PRINT',
                     'LPAREN',
                     'IDENT',
                     'RPAREN',
                     'SEMICOLON',
                     'RBRACE',
                     'RBRACE']
        self.assertEqual(tokenlist, res)
