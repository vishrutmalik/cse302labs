import json
from os import error
import sys

binop_dict = {
    "PLUS": ("+", "int", "int"),
    "MINUS": ("-", "int", "int"),
    "TIMES": ("*", "int", "int"),
    "DIV": ("/", "int", "int"),
    "MODULUS": ("%", "int", "int"),
    "BITAND": ("&", "int", "int"),
    "BITOR": ("|", "int", "int"),
    "BITXOR": ("^", "int", "int"),
    "BITSHL": ("<<", "int", "int"),
    "BITSHR": (">>", "int", "int"),
    "LT": ("<", "int", "bool"),
    "GT": (">", "int", "bool"),
    "LTE": ("<=", "int", "bool"),
    "GTE": (">=", "int", "bool"),
    "EQUALS": ("==", ["int", "bool"], "bool"),
    "NEQUALS": ("!=", ["int", "bool"], "bool"),
    "BOOLAND": ("&&", "bool", "bool"),
    "BOOLOR": ("||", "bool", "bool")
}

unop_dict = {
    "UMINUS": ("-", "int", "int"),
    "BITCOMPL": ("~", "int", "int"),
    "BOOLNOT": ("!", "bool", "bool")
}

valid_types = ["int", "bool", "void"]

def error_message(error_msg, loc=None):
    if loc is not None:
        print(f"Error: {error_msg} on line {loc[0]}")
    else:
        print(f"Error: {error_msg}")
    sys.exit(1)


class CheckState():
    def __init__(self, global_decls, proc_decls):
        self.declared_vars = [global_decls]
        self.declared_procs = proc_decls
        self.in_loop = False
        self.rtt = None


class BinOp():
    def __init__(self, op: str, location=None):
        self.name = op
        self.argtype_ = binop_dict[op][1]
        self.rettype_ = binop_dict[op][2]
        self.location = location

    def __str__(self):
        return binop_dict[self.name][0]


class UnOp():
    def __init__(self, op: str, location=None):
        self.name = op
        self.argtype_ = unop_dict[self.name][1]
        self.rettype_ = unop_dict[self.name][2]
        self.location = location

    def __str__(self):
        return unop_dict[self.name][0]


class Expr:
    pass


class Variable(Expr):
    def __init__(self, name: str, location=None):
        self.name = name
        self.location = location
        self.type_ = None

    def __str__(self):
        return self.name
    
    def get_type(self, declared_vars):
        for i in reversed(declared_vars):
            if self.name in i.keys():
                return i[self.name].type_

    def check_syntax(self, current_state: CheckState):
        # check if the variable referenced is declared
        var_type = self.get_type(current_state.declared_vars)
        if var_type is None:
            error_message(f"undeclared variable {self.name}", self.location)
        if var_type not in valid_types:
            error_message(f"invalid variable type: {var_type}", self.location)
        if var_type == "void":
            error_message(f"variable {self.name} cannot be of type void", self.location)
        self.type_ = var_type


class Param():
    def __init__(self, name: str, type_, location=None):
        self.name = name
        self.location = location 
        self.type_ = type_
    
    def __str__(self):
        return f"{self.name}: {self.type_}"
    
    def get_type(self):
        return self.type_

    def check_syntax(self, current_state):
        # declaration twice in the same scope
        if self.name in current_state.declared_vars[-1].keys():
            if current_state.declared_vars[self.name].location is not None:
                print(f"Info: initial declaration on line {current_state.declared_vars[self.name].location[0]}")
            error_message(f"variable already declared: {self.name}", self.location)

        current_state.declared_vars[-1][self.name] = self


class Number(Expr):
    def __init__(self, value: int, location=None):
        self.value = value
        self.location = location
        self.type_ = "int"

    def __str__(self):
        return str(self.value)

    def check_syntax(self, current_state):
        if not -2**63 < self.value < 2**63:
            error_message(f"integer value {self.value} does not fit within 63 bits", self.location)
        self.type_ = "int"


class Bool(Expr):
    def __init__(self, value, location=None):
        self.value = value
        self.location = location
        self.type_ = None

    def __str__(self):
        return self.value
    
    def check_syntax(self, current_state: CheckState):
        self.type_ = "bool"


class UnopApp(Expr):
    def __init__(self, op, arg, location=None):
        self.op = op
        self.arg = arg # expr
        self.location = location
        self.type_ = None

    def __str__(self):
        return f"({str(self.op)} {str(self.arg)})"

    def check_syntax(self, current_state: CheckState):
        self.arg.check_syntax(current_state)
        if isinstance(self.op.argtype_, list):
            if self.arg.type_ not in self.op.argtype_:
                error_message(f"Incorrect operation {self.op} on type {self.arg.type_}", self.location)
        else:
            if self.arg.type_ != self.op.argtype_:
                error_message(f"Incorrect operation {self.op} on type {self.arg.type_}", self.location)
        self.type_ = self.op.rettype_


class BinopApp(Expr):
    def __init__(self, op, arg1, arg2, location=None):
        self.op = op
        self.arg1 = arg1 # expr
        self.arg2 = arg2 # expr
        self.location = location
        self.type_ = None

    def __str__(self):
        return f"({str(self.arg1)} {str(self.op)} {str(self.arg2)})"
    
    def check_syntax(self, current_state: CheckState):
        self.arg1.check_syntax(current_state)
        self.arg2.check_syntax(current_state)
        if (self.arg1.type_ == self.arg2.type_):
            if isinstance(self.op.argtype_, list):
                if self.arg1.type_ not in self.op.argtype_:
                    error_message(f"Incorrect operation {self.op} on type {self.arg1.type_} and {self.arg2.type_}", self.location)
            else:
                if self.arg1.type_ != self.op.argtype_:
                    error_message(f"Incorrect operation {self.op} on type {self.arg1.type_} and {self.arg2.type_}", self.location)
        else:
            error_message(f"Incorrect operation {self.op} on type {self.arg1.type_} and {self.arg2.type_}", self.location)
        self.type_ = self.op.rettype_


class ProcCall(Expr):
    def __init__(self, proc_name: str, args: list[Expr], location=None):
        self.proc_name = proc_name 
        self.args = args
        self.location = location
        self.type_ = None

    def __str__(self):
        arglist = ", ".join(str(arg) for arg in self.args)
        return f"{self.proc_name}({arglist})"

    def check_syntax(self, current_state: CheckState):
        for arg in self.args:
            arg.check_syntax(current_state)
        
        if self.proc_name == "print":
            if len(self.args) != 1:
                error_message(f"Incorrect number of args ({len(self.args)}) given for print: 1 expected", self.location)
            
            arg = self.args[0]
            if arg.type_ == "int":
                self.proc_name = "__bx_print_int"
            elif arg.type_ == "bool":
                self.proc_name = "__bx_print_bool"
            else:
                error_message(f"Unprintable type: {arg.type_}", self.location)

            self.type_ = "void" 
            return

        typelist = [arg.type_ for arg in self.args]

        print(current_state.declared_procs.keys())
        print(self.proc_name)
        if self.proc_name not in current_state.declared_procs.keys():
            error_message(f"undeclared procedure: {self.proc_name}", self.location)

        proc_type, arg_types = current_state.declared_procs[self.proc_name]
        if typelist != arg_types:
            error_message(f"Incorrect call to procedure {self.proc_name}: incorrect argument type(s)", self.location)
        
        self.type_ = proc_type


class Statement():
    pass


class Vardecl(Statement):
    def __init__(self, variables: list[tuple[Variable, Expr]], type_, location=None):
        self.variables = variables
        self.location = location
        self.type_ = type_
        self.return_ = False

    def __str__(self):
        res = ""
        for variable, expression in self.variables:
            res += f"{str(self.type_)} {str(variable)} = {str(expression)}"
        return res 

    def check_syntax(self, current_state: CheckState):
        for variable, expression in self.variables:
            expression.check_syntax(current_state)

            # declaration twice in the same block
            if variable.name in current_state.declared_vars[-1].keys():
                if current_state.declared_vars[variable.name].location is not None:
                    print(f"Info: initial declaration on line {current_state.declared_vars[variable.name].location[0]}")
                error_message(f"variable already declared: {variable.name}", self.location)

            # changing type of variable after declaration
            if self.type_ != expression.type_:
                error_message(f"cannot declare {expression.type_} value as {self.type_}", self.location)

            current_state.declared_vars[-1][variable.name] = self

class Assign(Statement):
    def __init__(self, variable: Variable, expr, location=None):
        self.variable = variable
        self.expression = expr # expr
        self.location = location
        self.return_ = False

    def __str__(self):
        return f"{str(self.variable)} = {str(self.expression)}"

    def check_syntax(self, current_state: CheckState):
        self.variable.check_syntax(current_state)
        self.expression.check_syntax(current_state)

        if self.variable.type_ != self.expression.type_:
            if self.expression.type_ == "void":
                error_message(f"Tried to assign subroutine to variable {self.variable.name}", self.location)
            error_message(f"Variable {self.variable.name} with type {self.variable.type_}, \
                        is assigned to expression of type {self.expression.type_}", self.location)


class Ifelse(Statement):
    def __init__(self, condition, block, optelse, location=None):
        self.condition = condition # bool expr
        self.block = block 
        self.return_ = False
        if optelse is not None:
            self.optelse = optelse
        else:
            self.optelse = Block([])
        self.location = location

    def __str__(self):
        if self.optelse == None:
            return f"if ({self.condition})" + str(self.block)
        return f"if ({self.condition})" + str(self.block) \
            + "\n else " + str(self.optelse)
    
    def check_syntax(self, current_state: CheckState):
        self.condition.check_syntax(current_state)
        self.block.check_syntax(current_state)
        self.optelse.check_syntax(current_state)
        if (self.condition.type_ != "bool"):
            error_message("condition of a if statement must be a boolean", self.location)
        
        # if there is a return on all paths then set return_ to true
        if self.block.return_ and self.optelse.return_:
            self.return_ = True


class While(Statement):
    def __init__(self, condition, block, location=None):
        self.condition = condition
        self.block = block
        self.location = location
        self.return_ = False

    def __str__(self):
        return f"while ({self.condition})" + "{\n" + str(self.block) + "}"
    
    def check_syntax(self, current_state: CheckState):
        self.condition.check_syntax(current_state)
        current_state.in_loop = True
        self.block.check_syntax(current_state)
        current_state.in_loop = False
        if (self.condition.type_ != "bool"):
            error_message("condition of a while statement must be a boolean", self.location)


class Jump(Statement):
    def __init__(self, type_, location=None):
        self.type_ = type_
        self.location = location
        self.return_ = False

    def __str__(self):
        return str(self.type_)

    def check_syntax(self, current_state: CheckState):
        # check if this is within a loop
        if not current_state.in_loop:
            error_message("the \"{self.type_}\" statement is not within the body of a loop", self.location)


class Block(Statement):
    def __init__(self, stmts):
        self.return_ = False
        if stmts is not None:
            self.statements = stmts
        else:
            self.statements = []

    def __str__(self):
        return "{\n" + "\n".join([f"\t{str(i)}" for i in self.statements]) + "\n}"
    
    def check_syntax(self, current_state: CheckState):
        current_state.declared_vars.append(dict())
        for s in self.statements:
            s.check_syntax(current_state)

            # flag to indicate if block contains a return
            if isinstance(s, Return):
                self.return_ = True
        current_state.declared_vars.pop()


class Eval(Statement):
    def __init__(self, expression, location=None):
        self.expression = expression
        self.location = location
        self.return_ = False 

    def __str__(self):
        return f"{str(self.expression)};"
    
    def check_syntax(self, current_state: CheckState):
        self.expression.check_syntax(current_state)


class Return(Statement):
    def __init__(self, expression, location=None):
        self.expression = expression 
        self.location = location
        self.return_ = True
    
    def __str__(self):
        res = "return"
        if self.expression is not None:
            res += f" {str(self.expression)}"
        return res
    
    def check_syntax(self, current_state: CheckState):
        # if no return argument, then check that we are in a subroutine
        if self.expression is None:
            if current_state.rtt != "void":
                error_message("no value provided for return where one was expected", self.location)
            return 

        self.expression.check_syntax(current_state)
        # if we are in a subroutine, check that expression is void
        if current_state.rtt == "void" and self.expression.type_ != "void":
            error_message(f"returning value in subroutine: {str(self.expression)}", self.location)
        
        # more generally, check that expression matches return type
        if current_state.rtt != self.expression.type_:
            error_message(f"expression {str(self.expression)} does not match return type", self.location)
                

class Procdecl(Statement):
    def __init__(self, name: str, params: list[Param], statements: Block, rtt, location=None):
        self.name = name
        self.params = params
        self.argtype = [param.type_ for param in params] 
        self.return_type = rtt
        self.statements = [statement for statement in statements.statements]
        self.location = location

    def __str__(self):
        res = "\n".join(str(statement)
                        for statement in self.statements)
        return res
    
    def get_type(self, proc_decls):
        if self.name in proc_decls.keys():
            if proc_decls[self.variable.name].location is not None:
                print(f"Info: initial declaration on line {proc_decls[self.variable.name].location[0]}")
            error_message(f"procedure already declared: {self.variable.name}", self.location)

        proc_decls[self.name] = (self.argtype, self.return_type)

    def check_syntax(self, current_state: CheckState):
        saw_return = False
        current_state.declared_vars.append(dict())
        current_state.rtt = self.return_type

        if self.name.startswith("__bx_"):
            error_message("Tried to define procedure starting with reserved keyword __bx_", self.location)

        for param in self.params:
            param.check_syntax(current_state)

        for statement in self.statements:
            statement.check_syntax(current_state)
            if statement.return_:
                saw_return = True
        
        if self.return_type != "void":
            if not saw_return:
                error_message(f"{self.name}: return not found on all code paths", self.location)

        current_state.declared_vars.pop()


class GlobalVardecl(Statement):
    def __init__(self, variables: list[tuple[Variable, Expr]], type_, location=None):
        self.variables = variables
        self.location = location
        self.type_ = type_

    def __str__(self):
        res = ""
        for variable, expr in self.variables:
            res += f"{str(self.type_)} {str(variable)} = {str(expr)}"
        return res 

    def check_syntax(self, global_decls):
        for variable, expr in self.variables:
            # check that the type is valid
            if self.type_ not in valid_types:
                error_message(f"invalid variable type: {self.type_}", self.location)

            # check that value is number
            if isinstance(expr, Number):
                if not 0 <= expr.value < 2**63:
                    error_message(f"integer value {expr.value} does not fit within 63 bits", self.location)
            else:
                error_message(f"global variable value {str(expr)} is not a number", self.location)

            # declaration twice
            if variable.name in global_decls.keys():
                if global_decls[variable.name].location is not None:
                    print(f"Info: initial declaration on line {global_decls[variable.name].location[0]}")
                error_message(f"variable already declared: {variable.name}", self.location)

            global_decls[variable.name] = self


class GlobalScope():
    def __init__(self, declarations):
        self.procedures = []
        self.global_vars = []

        for declaration in declarations:
            if isinstance(declaration, Procdecl):
                self.procedures.append(declaration)
            elif isinstance(declaration, GlobalVardecl):
                self.global_vars.append(declaration)
    
    def __str__(self):
        res = "\n".join(str(global_var)
                        for global_var in self.global_vars)
        res += "\n".join(str(procedure)
                        for procedure in self.procedures)
        return res
    
    def check_syntax(self):
        global_declarations = {}
        for global_var in self.global_vars:
            global_var.check_syntax(global_declarations)
        procedure_declarations = {}
        for procdecl in self.procedures:
            procdecl.get_type(procedure_declarations)

        if "main" not in procedure_declarations.keys():
            error_message("no main procedure found")

        current_state = CheckState(global_declarations, procedure_declarations) 
        for procedure in self.procedures:
            procedure.check_syntax(current_state)
