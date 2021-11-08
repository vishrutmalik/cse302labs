import json
import sys
from bxast import *

TOTAL_VARIABLES = 0
TOTAL_LABELS = 0

class Muncher():
    def __init__(self):
        self.local_vars = [{}]
        self.break_stack = []
        self.continue_stack = []

    def __getitem__(self, key):
        for dic in reversed(self.local_vars):
            res = dic.get(key)
            if res is not None:
                return res

    def __setitem__(self, key, value):
        self.local_vars[-1][key] = value
    
    def add_scope(self):
        self.local_vars.append({})
    
    def remove_scope(self):
        self.local_vars.pop()
    
    def reset(self):
        # get rid of all scopes except for the global scope
        while len(self.local_vars) > 1:
            self.local_vars.pop()

        self.break_stack = []
        self.continue_stack = []


def fresh():
    global TOTAL_VARIABLES
    x = f"%{TOTAL_VARIABLES}"
    TOTAL_VARIABLES += 1
    return x

def fresh_label():
    global TOTAL_LABELS
    L = f"%.L{TOTAL_LABELS}"
    TOTAL_LABELS += 1
    return L

def bool_expr_to_code(x, Lt, Lf, local_vars):
    if isinstance(x, Bool):
        if x.value == "true":
            return [{"opcode":"jmp", "args":[Lt], "result":None}]
        elif x.value == "false":
            return [{"opcode":"jmp", "args":[Lf], "result":None}]
        else:
            print(f"Unrecognized boolean value: {x.value}, line {x.location[0]}")
            sys.exit(1)

    if isinstance(x, BinopApp):
        if x.arg1.type_ == "int":
            op_to_jmp = {"EQUALS": "jz",
                        "NEQUALS": "jnz",
                        "LT": "jl",
                        "LTE": "jle",
                        "GT": "jnle",
                        "GTE": "jnl"}
            jump = op_to_jmp[x.op.name]
            t1 = fresh()
            t2 = fresh()
            e1 = expression_to_code(x.arg1, t1, local_vars)
            e2 = expression_to_code(x.arg2, t2, local_vars)
            return e1 + e2 + [{"opcode":"sub", "args":[t1, t2], "result":t1},
                                {"opcode":jump, "args":[t1, Lt], "result":None},
                                {"opcode":"jmp", "args":[Lf], "result":None}]

        if x.arg2.type_ == "bool":
            if x.op.name == "BOOLAND":
                Li = fresh_label()
                e1 = bool_expr_to_code(x.arg1, Li, Lf, local_vars)
                e2 = bool_expr_to_code(x.arg2, Lt, Lf, local_vars)
                return e1 + [{"opcode":"label", "args":[Li], "result":None}] + e2

            if x.op.name == "BOOLOR":
                Li = fresh_label()
                e1 = bool_expr_to_code(x.arg1, Lt, Li, local_vars)
                e2 = bool_expr_to_code(x.arg2, Lt, Lf, local_vars)
                return e1 + [{"opcode":"label", "args":[Li], "result":None}] + e2

            if x.op.name == "EQUALS":
                Lz = fresh_label()
                Lo = fresh_label()
                e1 = bool_expr_to_code(x.arg1, Lz, Lo, local_vars)
                ez = bool_expr_to_code(x.arg2, Lt, Lf, local_vars)
                eo = bool_expr_to_code(x.arg2, Lf, Lt, local_vars)
                return e1 +\
                       [{"opcode":"label", "args":[Lz], "result":None}] +\
                       ez +\
                       [{"opcode":"label", "args":[Lo], "result":None}] +\
                       eo

            if x.op.name == "NEQUALS":
                Lz = fresh_label()
                Lo = fresh_label()
                e1 = bool_expr_to_code(x.arg1, Lz, Lo, local_vars)
                ez = bool_expr_to_code(x.arg2, Lf, Lt, local_vars)
                eo = bool_expr_to_code(x.arg2, Lt, Lf, local_vars)
                return e1 +\
                       [{"opcode":"label", "args":[Lz], "result":None}] +\
                       ez +\
                       [{"opcode":"label", "args":[Lo], "result":None}] +\
                       eo

            print(f"Unrecognized boolean expression name {x.op.name}, line {x.location[0]}")
            sys.exit(1)

        print(f"Unrecognized boolean operator argument type {x.arg1.type_}, line {x.location[0]}")
        sys.exit(1)

    if isinstance(x, UnopApp):
        if x.op.name == "BOOLNOT":
            return bool_expr_to_code(x.arg, Lf, Lt, local_vars)

        print(f"Unrecognized unary operator {x.op.name}")
        sys.exit(1)


def expression_to_code(e, x, local_vars):
    """
    input: an expression e and a temporary x
    output: a list of arrays of length 3 each containing:
        - an opcode
        - arguments
        - a temporary to store the result
        Which represent the expression
    """
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
        y = fresh()
        z = fresh()
        e1 = expression_to_code(e.arg1, y, local_vars)
        e2 = expression_to_code(e.arg2, z, local_vars)
        return e1 + e2 + [{"opcode":op_names[e.op.name], "args":[y, z],
                           "result":x}]

    if isinstance(e, UnopApp):
        op_names = {"UMINUS": "neg", "BITCOMPL": "not"}
        y = fresh()
        e1 = expression_to_code(e.arg, y, local_vars)
        return e1 + [{"opcode":op_names[e.op.name], "args":[y], "result":x}]

    if isinstance(e, ProcCall):
        res = []
        for i, arg in enumerate(e.args):
            if isinstance(arg, Variable):
                y = local_vars[arg.name]
                res.append({"opcode":"param", "args": [i+1, y], "result":None})
            else:
                y = fresh()
                e = expression_to_code(arg, y, local_vars)
                res += e
                res.append({"opcode":"param", "args":[i+1, y], "result":None})
        
        name = '@' + e.proc_name
        res.append({"opcode":"call", "args":[name, len(e.args)], "result":x})


    print(f"Unrecognized expression type: {type(e)}, line {e.location[0]}")
    sys.exit(1)


def statement_to_code(s, local_vars: Muncher):
    """
    input: a statement s and a dict mapping declared variables to temporaries
    output: a list of arrays of length 3 each containing:
        - an opcode
        - arguments
        - a temporary to store the result
        Which represent the statement
    """
    if isinstance(s, Assign):
        x = local_vars[s.variable.name]
        if s.expression.type_ == "bool":
            t = fresh()
            Lt = fresh_label()
            Lf = fresh_label()
            e1 = bool_expr_to_code(s.expression, Lt, Lf, local_vars)
            return [{"opcode":"const", "args":[0], "result":t}] +\
                   e1 +\
                   [{"opcode":"label", "args":[Lt], "result":None},
                    {"opcode":"const", "args":[1], "result":t},
                    {"opcode":"label", "args":[Lf], "result":None},
                    {"opcode":"copy", "args":[t], "result":x}]

        if s.expression.type_ == "int":
            return expression_to_code(s.expression, x, local_vars)

        else:
            print(f"Unrecognized assign type {s.type_}, line {s.location[0]}")
            sys.exit(1)

    if isinstance(s, Vardecl):
        res = []
        for variable, expression in s.variables:
            y = fresh()
            local_vars[variable.name] = y

            if isinstance(expression, Variable):
                x = local_vars[expression.name]
                res += [{"opcode":"copy", "args":[x], "result":y}] 
                continue

            x = fresh()
            e1 = expression_to_code(expression, x, local_vars)

            res += e1 + [{"opcode":"copy", "args":[x], "result":y}]
        return res

    if isinstance(s, Block):
        res = []
        local_vars.add_scope()
        for statement in s.statements:
            res += statement_to_code(statement, local_vars)
        local_vars.remove_scope()
        return res

    if isinstance(s, Ifelse):
        Lt = fresh_label()
        Lf = fresh_label()
        Lo = fresh_label()
        e1 = bool_expr_to_code(s.condition, Lt, Lf, local_vars)
        s1 = statement_to_code(s.block, local_vars)
        s2 = statement_to_code(s.optelse, local_vars)
        return e1 +\
            [{"opcode":"label", "args":[Lt], "result":None}] +\
               s1 +\
               [{"opcode":"jmp", "args":[Lo], "result":None},
                {"opcode":"label", "args":[Lf], "result":None}] +\
               s2 +\
               [{"opcode":"label", "args":[Lo], "result":None}]

    if isinstance(s, While):
        Lhead = fresh_label()
        Lbod = fresh_label()
        Lend = fresh_label()
        local_vars.break_stack.append(Lend)
        local_vars.continue_stack.append(Lhead)
        e1 = bool_expr_to_code(s.condition, Lbod, Lend, local_vars)
        s1 = statement_to_code(s.block, local_vars)
        local_vars.break_stack.pop()
        local_vars.continue_stack.pop()
        return [{"opcode":"label", "args":[Lhead], "result":None}] +\
               e1 +\
               [{"opcode":"label", "args":[Lbod], "result":None}] +\
               s1 +\
               [{"opcode":"jmp", "args":[Lhead], "result":None},
                {"opcode":"label", "args":[Lend], "result":None}]

    if isinstance(s, Jump):
        if s.type_ == "break":
            return [{"opcode":"jmp", "args":[local_vars.break_stack[-1]], "result":None}]

        if s.type_ == "continue":
            return [{"opcode":"jmp", "args":[local_vars.continue_stack[-1]], "result":None}]

        print(f"Unrecognized jump type {s.type_}, line {s.location[0]}")
        sys.exit(1)
    
    if isinstance(s, Eval):
        x = fresh()
        return expression_to_code(s.expression, x, local_vars)
    
    if isinstance(s, Return):
        if s.expression is None:
            return [{"opcode":"ret", "args":[], "result":None}]
        
        if isinstance(s.expression, Variable):
            x = local_vars[s.expression.name]
            e1 = []
        else:
            x = fresh()
            e1 = expression_to_code(s.expression, x, local_vars)

        if isinstance(s.expression, ProcCall):
            return e1 + [{"opcode":"ret", "args":[], "result":None}]
        
        return e1 + [{"opcode":"ret", "args":[x], "result":None}]
    
    print(f"Unrecognized statement type: {type(s)}, line {s.location[0]}")
    sys.exit(1)


def global_to_code(vardecl: GlobalVardecl, local_vars: Muncher):
    res = []
    for variable, expression in vardecl.variables:
        name = '@' + variable.name
        local_vars[variable.name] = name
        res.append({"var": name, "init": expression.value})
    return res 


def procdecl_to_code(procdecl: Procdecl, local_vars: Muncher):
    procname = '@' + procdecl.name

    local_vars.reset()
    local_vars.add_scope()
    procargs = []
    for arg in procdecl.params:
        procargs.append('%' + arg.name)
        local_vars[arg.name] = '%' + arg.name
    body = []
    for statement in procdecl.statements:
        body += statement_to_code(statement, local_vars)
    local_vars.remove_scope()
    return {"proc": procname, "args": procargs, "body": body}


def program2tac(ast: GlobalScope):
    tac = []
    localvars = Muncher()
    for global_var in ast.global_vars:
        tac += global_to_code(global_var, localvars)
    for procdecl in ast.procedures:
        tac.append(procdecl_to_code(procdecl, localvars))
    return tac
