import json
import sys
from bxast import *

TOTAL_VARIABLES = 0


def expression_to_code_t(e, x, local_vars):
    """
    input: an expression e and a temporary x
    output: a list of arrays of length 3 each containing:
        - an opcode
        - arguments
        - a temporary to store the result
        Which represent the expression
    """
    global TOTAL_VARIABLES

    if isinstance(e, Number):
        return [{"opcode":"const", "args":[e.value],  "result":x}]

    if isinstance(e, Variable):
        return [{"opcode":"copy", "args":[local_vars[e.name]], "result":x}]

    if isinstance(e, BinopApp):
        op_names = {"PLUS": "add",
                    "MINUS": "sub",
                    "TIMES": "mul",
                    "DIV": "div",
                    "MODULUS": "mod",
                    "BITAND": "and",
                    "BITOR": "or",
                    "BITXOR": "xor",
                    "BITSHL": "shl",
                    "BITSHR": "shr"
                    }
        y = f"%{TOTAL_VARIABLES}"
        TOTAL_VARIABLES += 1
        z = f"%{TOTAL_VARIABLES}"
        TOTAL_VARIABLES += 1
        e1 = expression_to_code_t(e.arg1, y, local_vars)
        e2 = expression_to_code_t(e.arg2, z, local_vars)
        return e1 + e2 + [{"opcode":op_names[e.op.op], "args":[y, z],
                           "result":x}]

    if isinstance(e, UnopApp):
        op_names = {"UMINUS": "neg", "BITCOMPL": "not"}
        y = f"%{TOTAL_VARIABLES}"
        TOTAL_VARIABLES += 1
        e1 = expression_to_code_t(e.arg, y, local_vars)
        return e1 + [{"opcode":op_names[e.op.op], "args":[y], "result":x}]

    print(f"Unrecognized expression type: {type(e)}")
    raise ValueError


def statement_to_code_t(s, local_vars):
    """
    input: a statement s and a dict mapping declared variables to temporaries
    output: a list of arrays of length 3 each containing:
        - an opcode
        - arguments
        - a temporary to store the result
        Which represent the statement
    """
    global TOTAL_VARIABLES

    if isinstance(s, Assign):
        x = local_vars[s.variable.name]
        return expression_to_code_t(s.expression, x, local_vars)

    if isinstance(s, Print):
        x = f"%{TOTAL_VARIABLES}"
        TOTAL_VARIABLES += 1
        e1 = expression_to_code_t(s.expression, x, local_vars)
        return e1 + [{"opcode":"print", "args":[x], "result":None}]

    if isinstance(s, Vardecl):
        y = f"%{TOTAL_VARIABLES}"
        local_vars[s.variable.name] = y
        TOTAL_VARIABLES += 1
        x = f"%{TOTAL_VARIABLES}"
        TOTAL_VARIABLES += 1
        e1 = expression_to_code_t(s.expression, x, local_vars)
        return e1 + [{"opcode":"copy", "args":[x], "result":y}]

    print(f"Unrecognized statement type: {type(s)}")
    raise ValueError


def expression_to_code_b(e, local_vars):
    """
    input: an expression e and a temporary x
    output: a list of arrays of length 3 each containing:
        - an opcode
        - arguments
        - a temporary to store the result
        Which represent the expression
    """
    global TOTAL_VARIABLES

    if isinstance(e, Number):
        x = f"%{TOTAL_VARIABLES}"
        TOTAL_VARIABLES += 1
        return (x, [{"opcode":"copy", "args":[e.value], "result":x}])

    if isinstance(e, Variable):
        return (local_vars[e.name], [])

    if isinstance(e, BinopApp):
        op_names = {"PLUS": "add",
                    "MINUS": "sub",
                    "TIMES": "mul",
                    "DIV": "div",
                    "MODULUS": "mod",
                    "BITAND": "and",
                    "BITOR": "or",
                    "BITXOR": "xor",
                    "BITSHL": "shl",
                    "BITSHR": "shr"
                    }
        y, L1 = expression_to_code_b(e.arg1, local_vars)
        z, L2 = expression_to_code_b(e.arg2, local_vars)
        x = f"%{TOTAL_VARIABLES}"
        TOTAL_VARIABLES += 1
        return (x, L1 + L2 + [{"opcode":op_names[e.op.op], "args":[y, z],
                               "result":x}])

    if isinstance(e, UnopApp):
        op_names = {"UMINUS": "neg", "BITCOMPL": "not"}
        y, L1 = expression_to_code_b(e.arg, local_vars)
        x = f"%{TOTAL_VARIABLES}"
        TOTAL_VARIABLES += 1
        return (x, L1 + [{"opcode":op_names[e.op.op], "args":[y], "result":x}])

    print(f"Unrecognized expression type: {type(e)}")
    raise ValueError


def statement_to_code_b(s, local_vars):
    """
    input: a statement s and a dict mapping declared variables to temporaries
    output: a list of arrays of length 3 each containing:
        - an opcode
        - arguments
        - a temporary to store the result
        Which represent the statement
    """
    global TOTAL_VARIABLES

    if isinstance(s, Assign):
        y, L = expression_to_code_b(s.expression, local_vars)
        return L + [{"opcode":"copy", "args":[y],
                     "result":local_vars[s.variable.name]}]

    if isinstance(s, Print):
        x, L = expression_to_code_b(s.expression, local_vars)
        return L + [{"opcode":"print", "args":[x], "result":None}]

    if isinstance(s, Vardecl):
        y = f"%{TOTAL_VARIABLES}"
        local_vars[s.variable.name] = f"%{TOTAL_VARIABLES}"
        TOTAL_VARIABLES += 1
        x, L = expression_to_code_b(s.expression,local_vars)
        return L + [{"opcode":"const", "args":[x], "result":y}]


def maximal_munch(js_obj, td_flag=True):
    """
    input: a json object describing a procedure
    output: a list of arrays of length 3 each containing:
        - an opcode
        - arguments
        - a temporary to store the result
        Which represent the procedure
    """
    global TOTAL_VARIABLES

    payload = js_obj["ast"][0]
    procedure = json_to_procedure(payload[0])

    code = []
    localvars = {}

    if td_flag:
        for statement in procedure.statements:
            code += statement_to_code_t(statement, localvars)
    else:
        for statement in procedure.statements:
            code += statement_to_code_b(statement, localvars)

    return code


def run(fname, td_flag=True):
    if fname.endswith('.json'):
        rname = fname[:-5] + ".tac.json"
    else:
        raise ValueError(f'{fname} does not end in .json')

    with open(fname, 'r') as fp:
        js_obj = json.load(fp)

    code = maximal_munch(js_obj, td_flag)
    res = [{"proc": "@main", "body": code}]
    with open(rname, 'w') as afp:
        json.dump(res, afp, indent=1)

def program2tac(ast):
    tac = []
    localvars = {}
    for statement in ast.statements:
        tac += statement_to_code_t(statement, localvars)
    return tac


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Incorrect number of arguments,correct usage is\n"
              "\tpython3 ast2tac.py file.json")
        raise ValueError
    if len(sys.argv) == 2:
        fname = sys.argv[1]
        run(fname)

    elif len(sys.argv) == 3:
        fname = sys.argv[2]
        if sys.argv[1] == "--tmm":
            run(fname, True)

        elif sys.argv[1] == "--bmm":
            run(fname, False)

        else:
            print("Correct usage ispython3 ast2tac.py {--tmm, bmm} file.json")

    else:
        print(
            f"Incorrect number of arguments, expected 2-3 got {len(sys.argv)}")
