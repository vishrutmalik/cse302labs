import argparse
import os

from scanner import lexer
from parser import parser
dirname, filename = os.path.split(os.path.abspath(__file__))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fname")
    args = parser.parse_args()

    with open(f"{dirname}/../examples/{args.fname}", 'r') as f:
            ast = parser.parse(f.read(), lexer=lexer)
            ast.check_syntax()
            lexer.lineno = 1