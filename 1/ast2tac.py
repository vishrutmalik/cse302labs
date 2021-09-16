# -*- coding: utf-8 -*-
"""
Created on Thu Sep  9 14:14:18 2021

@author: user
"""

import json
import sys
import os

# class Munch:
#     def __init__(self):
#         self.instr=[]
#         self.temps={}
#         self.temp_counter=-1
#         self.binop_map = {
#                           "+": 'add',
#                           "-": 'sub',
#                           "/": 'div',
#                           "*": 'mul',
#                           "%": 'mod',
#                           "&": 'and',
#                           "|": 'or',
#                           "^": 'xor',
#                           "<<": 'shl',
#                           ">>": 'shr'
#                          }
#         self.unop_map = {
#                          "-": 'neg',
#                          "~": 'not'
#                         }
        
#     def emit(self, instr):
#         """Append a TAC instruction into self.instrs"""
#         self.instrs.append(instr)
        
#     def new_temp(self):
#         """Return a so far empty TAC temporary"""
#         self.temp_counter += 1
#         return f'%{self.temp_counter}'
    
#     def get_var_temp(self, var):
#         """Get the tempprary associated to [var] if it exists,
#            and assign one if it doesn't"""
#         if var in self.temps:
#             return self.temps[var]
#         else:
#             self.temps[var] = self.new_temp()
#             return self.temps[var]
        
#     def tmm_expr(self, expr, dest):
#         if expr.opcode == 'var':
#             if expr.value not in self.temps: #Don't compile if an unassigned variable is used in an expression!
#                 print(f'ERROR: Uninitialized variable {expr.value}')
#                 exit(1)
#             self.emit(Instruction(dest, 'copy', self.temps[expr.value], None))
#             return
#         if expr.opcode == 'binop':
#             lhs = self.new_temp()
#             self.tmm_expr(expr.kids[0], lhs)
#             rhs = self.new_temp()
#             self.tmm_expr(expr.kids[1], rhs)
#             self.emit(Instruction(dest, self.binop_map[expr.value], lhs, rhs))
#             return
#         if expr.opcode == 'unop':
#             arg = self.new_temp()
#             self.tmm_expr(expr.kids[0], arg)
#             self.emit(Instruction(dest, self.unop_map[expr.value], arg, None))
#             return
    
#     def tmm_stmt(self, stmt):
#         if self.verbose:
#             print(f'Munching statement {stmt}')
#         if stmt.opcode == 'print':
#             arg = self.new_temp()
#             self.tmm_expr(stmt.value, arg)
#             self.emit(Instruction(None, 'print', arg, None))
#             return
#         if stmt.opcode == 'assign':
#             t_dest = self.get_var_temp(stmt.value)
#             self.tmm_expr(stmt.kids[0], t_dest)
#             return
#         print("ERROR: Unknown statement opcode!")
#         exit(1)
        

class Exprc:pass


class Variable(Exprc):
    def __init__(self, name):
        self.name = name


class Number(Exprc):
    def __init__(self, value: int):
        self.value = value


class UnopApp(Exprc):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr



class BinopApp(Exprc):
    def __init__(self, expr1, op, expr2):
        self.expr1 = expr1
        self.op = op
        self.expr2 = expr2



class stmt:pass


class Vardec(stmt):
    def __init__(self, name, value, type):
        self.name = name
        self.value = value
        self.type = type



class Assign(stmt):
    def __init__(self, var: Variable, expr: Exprc):
        self.var = var
        self.expr = expr




class Eval(stmt):
    def __init__(self, expr):
        self.expr = expr


class Call:
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr



class Block:
    def __init__(self, args):
        self.args = args




class Munch:
    def __init__(self, name, args, returntype, block):
        self.name = name
        self.args = args
        self.returntype = returntype
        self.block = block


def json_to_expr(js_obj):
    if js_obj[0] == '<var>':
        return Variable(js_obj[1])
    elif js_obj[0] == '<number>':
        return Number(js_obj[1])
    elif js_obj[0] == '<unop>':
        op = js_obj[1][0][0]
        expr = json_to_expr(js_obj[2][0])
        return UnopApp(op, expr)
    elif js_obj[0] == '<binop>':
        expr1 = json_to_expr(js_obj[1][0])
        op = js_obj[2][0][0]
        expr2 = json_to_expr(js_obj[3][0])
        return BinopApp(expr1, op, expr2)
    elif js_obj[0] == '<eval>':
        return Eval(json_to_expr(js_obj[1][0]))
    elif js_obj[0] == '<call>':
        name = js_obj[1][0]
        expr = json_to_expr(js_obj[2][0][0])
        return Call(name, expr)
    elif js_obj[0] == '<assign>':
        var = json_to_expr(js_obj[1][0])
        expr = json_to_expr(js_obj[2][0])
        return Assign(var, expr)
    elif js_obj[0] == '<vardecl>':
        name = js_obj[1][0]
        value = json_to_expr(js_obj[2][0])
        type = js_obj[3][0]
        return Vardec(name, value, type)

    elif js_obj[0] == '<procdef>':
        name = js_obj[1][0]
        args = js_obj[2]
        returntype = js_obj[3][0][0]
        block = json_to_expr(js_obj[4][0])
        return Munch(name, args, returntype, block)
    elif js_obj[0] == '<block>':
        args = []
        for js in js_obj[1]:
            args.append(json_to_expr(js[0]))
        return Block(args)
    else:
        print(f'Unrecognized <expr> form: {js_obj[0]}')
        raise ValueError


temp_counter = -1
temps = {}
instr_list = []


def new_temp():
    global temp_counter
    temp_counter += 1
    return f"%{temp_counter}"


def emit(instruction):
    instr_list.append(instruction)



def tmm_exec(s: stmt):
    if type(s) == Vardec:
        name, value = s.name, s.value.value
        x = new_temp()
        temps[name] = x
        instr_list.append(
            {"opcode": "const", "args": [value], "result": x})
    elif type(s) == Assign:
        var, expr = s.var, s.expr
        x = temps[var.name]
        top_munch(expr, x)
    elif type(s) == Eval:
        
        s = s.expr
        name, expr = s.name, s.expr
        x = new_temp()
        top_munch(expr, x)
        instr_list.append(
            {"opcode": name, "args": [x], "result": None})
    else:
        print("ERROR: Unknown statement opcode!") 
        exit(1)


def top_munch(e: Exprc, x: str):
    if type(e) == Number:
        emit({"opcode": "const", "args": [e.value], "result": x})
    elif type(e) == Variable:
        emit({"opcode": "copy", "args": [
                    temps[e.name]], "result": x})
    elif type(e) == UnopApp:
        expr = e.expr
        y = new_temp()
        top_munch(expr, y)

        op_map = {
            "UMINUS": "neg",
            "BITCOMPL": "not"
        }

        emit({"opcode": op_map[e.op], "args": [y], "result": x})
    elif type(e) == BinopApp:
        expr1, expr2 = e.expr1, e.expr2
        y = new_temp()
        z = new_temp()
        top_munch(expr1, y)
        top_munch(expr2, z)

        op_map = {
            "PLUS": "add",
            "MINUS": "sub",
            "TIMES": "mul",
            "DIV": "div",
            "MODULUS": "mod",
            "BITAND": "and",
            "BITOR": "or",
            "BITXOR": "xor",
            "BITSHR": "shr",
            "BITSHL": "shl",
        }

        emit({"opcode": op_map[e.op], "args": [y, z], "result": x})
    else:
        print("ERROR: Unknown statement opcode!") 
        exit(1)



def tmm(src):
    stmts = src.block.args
    for s in stmts:
        tmm_exec(s)




# def json_to_instr(js_obj):
#     if js_obj[0][0] == "<vardecl>":
#         return json_to_var(js_obj)
#     elif js_obj[0][0] == "<assign>":
#         return json_to_assign(js_obj)
#     elif js_obj[0][0] == "<eval>":
#         return json_to_print(js_obj)
#     else: print("ERROR: Unknown statement!")
#     exit(1)
        
    
# def json_to_var(js_obj):
#     if js_obj[0][0] == "<vardecl>":
#         return json_to_var(js_obj)
#     elif js_obj[0][0] == "<assign>":
#         return json_to_assign(js_obj)
#     elif js_obj[0][0] == "<eval>":
#         return json_to_print(js_obj)

# def json_to_assign(js_obj):
#     pass

# def json_to_print(js_obj):
#     pass


# def json_to_expr(js_obj):
#     if js_obj[0][0] == '<var>':
#         return Variable(js_obj[1])
#     elif js_obj[0][0] == '<number>':
#         return Number(js_obj[1])
#     elif js_obj[0][0] == '<unop>':
#         op = js_obj[1][0][0] # careful of all the nesting!
#         # OP will be 'UMINUS' or 'BITCOMPL'
#         arg = json_to_expr(js_obj[2]) # recursive call
#         return UnopApp(op, arg)
#     elif js_obj[0] == '<binop>':

    

#
#  def new_temp(self):
#         """Return a so far empty TAC temporary"""
#         self.temp_counter += 1
#         return f'%{self.temp_counter}'
    
#     def get_var_temp(self, var):
#         """Get the tempprary associated to [var] if it exists,
#            and assign one if it doesn't"""
#         if var in self.temps:
#             return self.temps[var]
#         else:
#             self.temps[var] = self.new_temp()
#             return self.temps[var]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} ast_json_file')
        sys.exit(1)
    
    source = sys.argv[1]
    
    with open(source, 'r') as fp:
        js_obj = json.load(fp)['ast'][0][0][0]
    
    ast = json_to_expr(js_obj)
    tmm(ast)
    
    result = [{
    "proc": "@main",
    "body": instr_list
    }]
    
    with open('tacfile.tac.json', 'w') as fp:
        print(json.dumps(result, indent=2), file=fp)

# ajs = None
# with open('../examples/print42.json', 'r') as fp:
#     ajs = json.load(fp)
# # assert isinstance(ajs, list) and len(ajs) == 1, ajs
# # ajs = ajs[0]
# # print(ajs)
# ajs=ajs['ast']
# # print(ajs)
# ajs=ajs[0]
# # print("New one", ajs)
# ajs
