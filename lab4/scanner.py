# -*- coding: utf-8 -*-
"""
Created on Wed Sep 20 12:35:30 2021
@author: user
"""

import re
import ply.lex as lex
import sys


reserved = {
    # 'print': 'PRINT',
    'def': 'DEF',
    # 'main': 'MAIN',
    'int': 'INT',
    'var': 'VAR',
    'if' : 'IF',
    'else' : 'ELSE',
    'bool' : 'BOOL',
    'while' : 'WHILE',
    'break' : 'BREAK',
    'continue' : 'CONTINUE',
    'true' : 'TRUE',
    'false' : 'FALSE',
    'return' : 'RETURN',
    'void' : 'VOID'
}

tokens = (
    'LPAREN', 'RPAREN', 'SEMICOLON', 'EQ', 'LBRACE', 'RBRACE', 'COLON', 'COMMA',
    'PLUS', 'MINUS', 'TIMES', 'DIV', 'MODULUS',
    'BITAND', 'BITOR', 'BITXOR', 'LT', 'GT', 'BITCOMPL','IDENT', 'NUMBER', 'BOOLNOT', 'BOOLOR', 'BOOLAND', 'BOOLEQ', 'NEQUALS', 'SHL', 'SHR', 'GTE', 'LTE'
) + tuple(reserved.values())


t_ignore = ' \t\f\v\r' 

def t_newline(t):
    r'\n'
    t.lexer.lineno += 1

def t_comment(t):
    r'//[^\n]*\n?'
    t.lexer.lineno += 1

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_SEMICOLON = r';'
t_BOOLEQ = '=='
t_NEQUALS = '!='
t_BOOLNOT = '!'
t_LTE = "<="
t_SHL = "<<"
t_SHR = ">>"
t_GTE = ">="
t_GT = '>'
t_LT = '<'
t_EQ = '='
t_BOOLOR = r'\|\|'
t_BITOR = r'\|'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_COLON = r'\:'
t_COMMA = r','
t_PLUS = r'\+'
t_MINUS = '-'
t_TIMES = r'\*'
t_DIV = '/'
t_MODULUS = '%'
t_BITAND = r'&[^&]'
t_BOOLAND = "&&"
t_BITXOR = r'\^'
t_BITCOMPL = r'\~'


def t_IDENT(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    t.type = reserved.get(t.value, 'IDENT')
    # t.value == whatever the above regex matches
    return t

def t_NUMBER(t):
    r'0|-?[1-9][0-9]*'
    # t.type == 'NUMBER'
    t.value = int(t.value)
    if not (-(1<<63) <= t.value < (1<<63)):
        print(t, f'Error: illegal numerical literal, {t.value} not in range(-1<<63, 1<<63) on line {t.lineno}')
        sys.exit(1)
    return t

# in case if illegal character input
def t_error(t):
    print(t, f'Error: illegal character {t.value[0]} on line {t.lineno}')
    sys.exit(1)

# lexer instance (object)

lexer = lex.lex()

def loadsrc(text):
    """Load some source code directly into the lexer"""
    lexer.input(text)
    lexer.lineno = 1
    lexer.provenance = None


if __name__ == '__main__':
    from os import devnull
    def token_list(source):
        loadsrc(source)
        with open(devnull, 'w') as lexer.errfile:
            toks = []
            while True:
                tok = lexer.token()
                if not tok: break
                toks.append((tok.type, tok.value, tok.lineno, tok.lexpos))
            return toks
