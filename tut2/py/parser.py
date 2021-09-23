import ply.yacc as yacc
import bxast
import sys
from scanner import tokens

# Expressions

## Variables

def p_expr_ident(p):
    """expr : IDENT"""
    p[0] = bxast.Variable(p[1], [p.lineno(1)])

## Numbers

def p_expr_number(p):
    """expr : NUMBER"""
    p[0] = bxast.Number(p[1], [p.lineno(1)])

## Binary Operators

def p_expr_plus(p):
    """expr : expr PLUS expr"""
    p[0] = bxast.BinopApp(bxast.BinOp('PLUS', [p.lineno(2)]), p[1], p[3], [p.lineno(2)])

def p_expr_minus(p):
    """expr : expr MINUS expr"""
    p[0] = bxast.BinopApp(bxast.BinOp('MINUS', [p.lineno(2)]), p[1], p[3], [p.lineno(2)])

def p_expr_times(p):
    """expr : expr TIMES expr"""
    p[0] = bxast.BinopApp(bxast.BinOp('TIMES', [p.lineno(2)]), p[1], p[3], [p.lineno(2)])

def p_expr_div(p):
    """expr : expr DIV expr"""
    p[0] = bxast.BinopApp(bxast.BinOp('DIV', [p.lineno(2)]), p[1], p[3], [p.lineno(2)])

def p_expr_modulus(p):
    """expr : expr MODULUS expr"""
    p[0] = bxast.BinopApp(bxast.BinOp('MODULUS', [p.lineno(2)]), p[1], p[3], [p.lineno(2)])

def p_expr_bitand(p):
    """expr : expr BITAND expr"""
    p[0] = bxast.BinopApp(bxast.BinOp('BITAND', [p.lineno(2)]), p[1], p[3], [p.lineno(2)])

def p_expr_bitor(p):
    """expr : expr BITOR expr"""
    p[0] = bxast.BinopApp(bxast.BinOp('BITOR', [p.lineno(2)]), p[1], p[3], [p.lineno(2)])

def p_expr_bitxor(p):
    """expr : expr BITXOR expr"""
    p[0] = bxast.BinopApp(bxast.BinOp('BITXOR', [p.lineno(2)]), p[1], p[3], [p.lineno(2)])

def p_expr_bitshl(p):
    """expr : expr BITSHL expr"""
    p[0] = bxast.BinopApp(bxast.BinOp('BITSHL', [p.lineno(2)]), p[1], p[3], [p.lineno(2)])

def p_expr_bitshr(p):
    """expr : expr BITSHR expr"""
    p[0] = bxast.BinopApp(bxast.BinOp('BITSHR', [p.lineno(2)]), p[1], p[3], [p.lineno(2)])

## Unary Operators

def p_expr_uminus(p):
    """expr : MINUS expr %prec UMINUS"""
    p[0] = bxast.UnopApp(bxast.UnOp('UMINUS', [p.lineno(1)]), p[2], [p.lineno(1)])

def p_expr_bitcompl(p):
    """expr : BITCOMPL expr"""
    p[0] = bxast.UnopApp(bxast.UnOp('BITCOMPL', [p.lineno(1)]), p[2], [p.lineno(1)])

## Parentheses

def p_expr_parens(p):
    """expr : LPAREN expr RPAREN"""
    p[0] = p[2]

# Statements

def p_print(p):
    """print : PRINT LPAREN expr RPAREN SEMICOLON"""
    p[0] = bxast.Print(p[3], [p.lineno(1)])

def p_assign(p):
    """assign : IDENT EQ expr SEMICOLON"""
    p[0] = bxast.Assign(bxast.Variable(p[1], [p.lineno(1)]), p[3], [p.lineno(2)])

def p_vardecl(p):
    """vardecl : VAR IDENT EQ expr COLON INT SEMICOLON"""
    p[0] = bxast.Vardecl(bxast.Variable(p[2], [p.lineno(1)]), p[4], [p.lineno(1)])

def p_statement(p):
    """stmt : vardecl
            | assign
            | print"""
    p[0] = p[1]

def p_statements(p):
    """stmts :
             | stmts stmt"""
    if len(p) == 1:
        p[0] = []
    else:
        p[0] = p[1]
        p[0].append(p[2])

# Program

def p_program(p):
    """program : DEF MAIN LPAREN RPAREN LBRACE stmts RBRACE"""
    p[0] = bxast.Program(p[6])

def p_error(p):
    if p:
        print(f"Syntax error on line {p.lineno}")
        sys.exit(1)
    else:
         print("Syntax error at EOF")
         sys.exit(1)

precedence = (
    ('left', 'BITOR'),
    ('left', 'BITXOR'),
    ('left', 'BITAND'),
    ('left', 'BITSHL', 'BITSHR'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIV', 'MODULUS'),
    ('right', 'UMINUS'),
    ('right', 'BITCOMPL')
)

parser = yacc.yacc(start='program')
