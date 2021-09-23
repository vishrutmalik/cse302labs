import json
import sys

class BinOp():
    def __init__(self, op, location=None):
        self.op = op
        self.names = {
            "PLUS": "+",
            "MINUS": "-",
            "TIMES": "*",
            "DIV": "/",
            "MODULUS": "%",
            "BITAND": "&",
            "BITOR": "|",
            "BITXOR": "^",
            "BITSHL": "<<",
            "BITSHR": ">>"
        }
        self.location = location

    def __str__(self):
        return self.names[self.op]

    def to_json(self):
        return [[self.op], []]


class UnOp():
    def __init__(self, op, location=None):
        self.op = op
        self.names = {"UMINUS": "-", "BITCOMPL": "~"}
        self.location = location

    def __str__(self):
        return self.names[self.op]

    def to_json(self):
        return [[self.op], []]


def json_to_op(js_obj):
    js_obj = js_obj[0]  # ignore location

    if js_obj[0] in ["PLUS", "MINUS", "TIMES", "DIV", "MODULUS",
                     "BITAND", "BITOR", "BITXOR", "BITSHL", "BITSHR"]:
        return BinOp(js_obj[0])

    elif js_obj[0] in ["UMINUS", "BITCOMPL"]:
        return UnOp(js_obj[0])

    else:
        print(f"{js_obj[0]} is not an operator")
        raise ValueError


class Expr:
    pass


class Variable(Expr):
    def __init__(self, name, location=None):
        self.name = name
        self.location = location

    def __str__(self):
        return self.name

    def to_json(self):
        return [["<var>", self.name], []]
    
    def check_syntax(self, declared_vars):
        if self.name not in declared_vars.keys():
            if self.location is not None:
                print(f"Error: undeclared variable \"{self.name}\" on line {self.location[0]}")
            else:
                print(f"Error: undeclared variable \"{self.name}\"")
            sys.exit(1)


class Number(Expr):
    def __init__(self, value, location=None):
        self.value = value
        self.location = location

    def __str__(self):
        return str(self.value)

    def to_json(self):
        return [["<number>", self.value], []]
    
    def check_syntax(self, declared_vars):
        if not (0 <= self.value < 2**63):
            if self.location is not None:
                print(f"Error: integer value on line {self.location[0]} does not fit within 63 bits: {self.value}")
            else:
                print(f"Error: integer value does not fit within 63 bits: {self.value}")
            sys.exit(1)


class UnopApp(Expr):
    def __init__(self, op, arg, location=None):
        self.op = op
        self.arg = arg
        self.location = location

    def __str__(self):
        return f"({str(self.op)} {str(self.arg)})"

    def to_json(self):
        return [["<unop>",
                 self.op.to_json(),
                 self.arg.to_json()
                 ], []]
    
    def check_syntax(self, declared_vars):
        self.arg.check_syntax(declared_vars)


class BinopApp(Expr):
    def __init__(self, op, arg1, arg2, location=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.location = location

    def __str__(self):
        return f"({str(self.arg1)} {str(self.op)} {str(self.arg2)})"

    def to_json(self):
        return [["<binop>",
                 self.arg1.to_json(),
                 self.op.to_json(),
                 self.arg2.to_json()
                 ], []]
    
    def check_syntax(self, declared_vars):
        self.arg1.check_syntax(declared_vars)
        self.arg2.check_syntax(declared_vars)



def json_to_expr(js_obj):
    js_obj = js_obj[0]  # ignore location

    if js_obj[0] == '<var>':
        return Variable(js_obj[1])

    elif js_obj[0] == '<number>':
        return Number(js_obj[1])

    elif js_obj[0] == '<unop>':
        op = json_to_op(js_obj[1])
        arg = json_to_expr(js_obj[2])  # recursive call
        return UnopApp(op, arg)

    elif js_obj[0] == '<binop>':
        arg1 = json_to_expr(js_obj[1])  # recursive call
        op = json_to_op(js_obj[2])  # aux function for op
        arg2 = json_to_expr(js_obj[3])  # recursive call
        return BinopApp(op, arg1, arg2)

    else:
        print(f'Unrecognized <expr> form: {js_obj[0]}')
        raise ValueError


class Statement():
    pass


class Vardecl(Statement):
    def __init__(self, variable, expression=Number(0), location=None, type="INT"):
        self.variable = variable
        self.expression = expression
        self.type = type
        self.location = location

    def __str__(self):
        return f"{str(self.type)} {str(self.variable)} = {str(self.expression)}"

    def to_json(self):
        return [[
            "<vardecl>",
            [self.variable.name, []],
            [self.expression.to_json(), []],
            [[self.type], []]
        ], []]

    def check_syntax(self, declared_vars):
        if self.variable.name in declared_vars.keys():
            if self.variable.location is not None:
                print(f"Error: variable already declared: \"{self.variable.name}\" on line {self.variable.location[0]}")
                print(f"Info: initial declaration on line {declared_vars[self.variable.name].location[0]}")
            else:
                print(f"Error: variable already declared: \"{self.variable.name}\"")
            sys.exit(1)
        else:
            self.expression.check_syntax(declared_vars)
            declared_vars[self.variable.name] = self.variable

def json_to_vardecl(js_obj):
    js_obj = js_obj[0]  # ignore location

    if js_obj[0] != "<vardecl>":
        print(f"{js_obj[0]} is not a variable declaration")
        raise ValueError

    variable = Variable(js_obj[1][0])
    expression = json_to_expr(js_obj[2])
    type_ = js_obj[3][0][0]

    return Vardecl(variable, expression, type_)


class Assign(Statement):
    def __init__(self, variable, expr, location=None):
        self.variable = variable
        self.expression = expr
        self.location = location

    def __str__(self):
        return f"{str(self.variable)} = {str(self.expression)}"

    def to_json(self):
        return [[
            "<assign>",
            self.variable.to_json(),
            self.expression.to_json()
        ], []]
    
    def check_syntax(self, declared_vars):
        if self.variable.name in declared_vars.keys():
            self.expression.check_syntax(declared_vars)
        else:
            if self.location is not None:
                print(f"Variable not declared: \"{self.variable.name}\" on line {self.variable.location[0]}")
            else:
                print(f"Variable not declared: \"{self.variable.name}\"")
            sys.exit(1)


def json_to_assign(js_obj):
    js_obj = js_obj[0]  # ignore location

    if js_obj[0] != "<assign>":
        print(f"{js_obj[0]} is not an assignment")
        raise ValueError

    variable = Variable(js_obj[1][0][1])
    expression = json_to_expr(js_obj[2])  # aux function for expr

    return Assign(variable, expression)


class Print(Statement):
    def __init__(self, expr, location=None):
        self.expression = expr
        self.location = location

    def __str__(self):
        return f"print {str(self.expression)}"

    def to_json(self):
        return [[
            "<eval>",
            [[
                "<call>",
                ["print", []]
                [self.expression.to_json()]
            ], []]
        ], []]
    
    def check_syntax(self, declared_vars):
        self.expression.check_syntax(declared_vars)


def json_to_print(js_obj):
    js_obj = js_obj[0]  # ignore location
    if js_obj[1][0][1][0] != "print":
        print(f"{js_obj[1][0][1][0]} is not a print statement")
        raise ValueError

    expression = json_to_expr(js_obj[1][0][2][0])  # aux function for expr

    return Print(expression)


def json_to_statement(js_obj):
    if js_obj[0][0] == "<vardecl>":
        return json_to_vardecl(js_obj)

    elif js_obj[0][0] == "<assign>":
        return json_to_assign(js_obj)

    elif js_obj[0][0] == "<eval>":
        return json_to_print(js_obj)

    else:
        print(f"Statement not recognized: {js_obj[0][0]}")
        raise ValueError


class Program():
    def __init__(self, statements, name="main", rtt="VOID"):
        self.name = name
        self.return_type = rtt
        self.statements = statements

    def __str__(self):
        res = "\n".join(str(statement)
                        for statement in self.statements)
        return res
    
    def check_syntax(self):
        declared_vars = {}
        for statement in self.statements:
            statement.check_syntax(declared_vars)


def json_to_procedure(js_obj):
    js_obj = js_obj[0]  # ignore location

    if js_obj[0] != "<procdef>":
        print(f"{js_obj[0]} is not a procedure")
        raise ValueError

    statements = []
    for line in js_obj[4][0][1]:
        statements.append(json_to_statement(line))

    return Program(statements)
