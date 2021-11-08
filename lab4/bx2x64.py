from scanner import lexer
from our_parser import parser
import sys
import json
import ast2tac
import tac2x64

def loadfile(fn):
    with open(fn, 'r') as f:
        ast = parser.parse(f.read(), lexer=lexer)
    return ast


def main():
    for filename in sys.argv[1:]:
        if filename.endswith('.bx'):
            rname = filename[:-3] + ".tac.json"
        else:
            raise ValueError(f'{filename} does not end in .bx')
        
        print(f"{filename} being processed")
        ast=loadfile(filename)
        ast.check_syntax()

        tac = ast2tac.program2tac(ast)
        res = [{"proc": "@main", "body": tac}]
        with open(rname, 'w') as afp:
            json.dump(res, afp, indent=1)
        print(f"{rname} produced")

        tac2x64.compile_tac(rname)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} tacfile.tac.json')
        sys.exit(1)
    main()
    