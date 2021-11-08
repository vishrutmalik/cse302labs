#!/usr/bin/env python3

"""

Usage: python3 tac2asm.py tacfile.json
Produces: tacfile.s (assembly) and tacfile.exe (executable)
Requires: a working gcc
"""

import json
import sys
import os
from pathlib import Path

binops = {'add': 'addq',
          'sub': 'subq',
          'mul': (lambda ra, rb, rd: [f'movq {ra}, %rax',
                                      f'imulq {rb}',
                                      f'movq %rax, {rd}']),
          'div': (lambda ra, rb, rd: [f'movq {ra}, %rax',
                                      f'cqto',
                                      f'idivq {rb}',
                                      f'movq %rax, {rd}']),
          'mod': (lambda ra, rb, rd: [f'movq {ra}, %rax',
                                      f'cqto',
                                      f'idivq {rb}',
                                      f'movq %rdx, {rd}']),
          'and': 'andq',
          'or': 'orq',
          'xor': 'xorq',
          'shl': (lambda ra, rb, rd: [f'movq {ra}, %r11',
                                      f'movq {rb}, %rcx',
                                      f'salq %cl, %r11',
                                      f'movq %r11, {rd}']),
          'shr': (lambda ra, rb, rd: [f'movq {ra}, %r11',
                                      f'movq {rb}, %rcx',
                                      f'sarq %cl, %r11',
                                      f'movq %r11, {rd}'])}
unops = {'neg': 'negq',
         'not': 'notq'}

# needs to be completed, this runs only for the test example we have
jump_list = ['jmp', 'jz', 'jnz', 'jl', 'jnl', 'jle', 'jnle' ] # Potentially we dont' need that dictionary
jump_map = { 'jmp': (lambda ld: f"jmp {ld}"), 
            'jz': (lambda ra, rd: [f'movq {ra}, %rax',
                                  f"jz %rax, {rd}"]), 
            'jnz': (lambda ra, rd: [f'movq {ra}, %rax',
                                  f"jnz %rax, {rd}"]), 
            'jl': (lambda ra, rd: [f'movq {ra}, %rax',
                                  f"jl %rax, {rd}"]), 
            'jnl': (lambda ra, rd: [f'movq {ra}, %rax',
                                  f"jnl %rax, {rd}"]),
            'jle': (lambda ra, rd: [f'movq {ra}, %rax',
                                  f"jle %rax, {rd}"]),
            'jnle': (lambda ra, rd: [f'movq {ra}, %rax',
                                  f"jnle %rax, {rd}"]) }


arg_reg={'%rdi':0, '%rsi':0, '%rdx':0, '%rcx':0, '%r8':0, '%r9':0}

def lookup_temp(temp, temp_map):
  assert (isinstance(temp, str) and \
          temp[0] == '%' and \
          temp[1:].isnumeric()), temp
  return temp_map.setdefault(temp, f'{-8 * (len(temp_map) + 1)}(%rbp)')

def tac_to_asm(tac_instrs):
  """
  Get the x64 instructions correspondign to the TAC instructions
  """
  temp_map = dict()
  asm = []
  print("instructions are:#########")
  for instr in tac_instrs:
        print(instr)
        print(type(instr))
        opcode = instr['opcode']
        args = instr['args']
        result = instr['result']
        if opcode == 'nop':
            pass
        elif opcode == 'const':
            assert len(args) == 1 and isinstance(args[0], int)
            result = lookup_temp(result, temp_map)
            asm.append(f'movq ${args[0]}, {result}')
        elif opcode == 'copy':
            assert len(args) == 1
            arg = lookup_temp(args[0], temp_map)
            result = lookup_temp(result, temp_map)
            asm.append(f'movq {arg}, %r11')
            asm.append(f'movq %r11, {result}')
        elif opcode in binops:
            assert len(args) == 2
            arg1 = lookup_temp(args[0], temp_map)
            arg2 = lookup_temp(args[1], temp_map)
            result = lookup_temp(result, temp_map)
            proc = binops[opcode]
            if isinstance(proc, str):
                asm.extend([f'movq {arg1}, %r11',
                            f'{proc} {arg2}, %r11',
                            f'movq %r11, {result}'])
            else: asm.extend(proc(arg1, arg2, result))
        elif opcode in unops:
            assert len(args) == 1
            arg = lookup_temp(args[0], temp_map)
            result = lookup_temp(result, temp_map)
            proc = unops[opcode]
            asm.extend([f'movq {arg}, %r11',
                        f'{proc} %r11',
                        f'movq %r11, {result}'])
        elif opcode == 'print':
            assert len(args) == 1
            assert result == None
            arg = lookup_temp(args[0], temp_map)
            asm.extend([f'leaq .lprintfmt(%rip), %rdi',
                        f'movq {arg}, %rsi',
                        f'xorq %rax, %rax',
                        f'callq printf@PLT'])
        elif opcode == 'label':
            assert len(args) == 1
            # print(args[0])
            asm.append(f'{args[0]}:')
        elif opcode in jump_list:
            if opcode == 'jmp':
                #just a simple unconditional jump.
                assert len(args) == 1
                asm.append(f"jmp {args[0][1:]}") # We remove the %
            else:
              assert len(args) == 2
              arg1 = lookup_temp(args[0], temp_map)
              arg_dest = args[1].replace('%', '') # Because we are jumping to a label not a register
              asm.extend([f"cmpq $0, {arg1}", 
                          f"{opcode} {arg_dest}"])
            # else:
            #     assert len(args) == 2
            #     arg1 = lookup_temp(args[0], temp_map)
            #     arg_dest = args[1]   # .replace('%', '') # Because we are jumping to a label not a register
            #     proc = jump_map[opcode]
            #     asm.extend(proc(arg1, arg_dest))
            #     # print("Jump operation not done yet: ", opcode)
        else:
            assert False, f'unknown opcode: {opcode}'
  stack_size = len(temp_map)
  if stack_size % 2 != 0: stack_size += 1 # 16 byte alignment for x64
  asm[:0] = [f'pushq %rbp',
             f'movq %rsp, %rbp',
             f'subq ${8 * stack_size}, %rsp'] \
  #  + [f'// {tmp} in {reg}' for (tmp, reg) in temp_map.items()]
  asm.extend([f'movq %rbp, %rsp',
              f'popq %rbp',
              f'xorq %rax, %rax',
              f'retq'])
  return asm

def compile_tac(fname):
  if fname.endswith('.tac.json'):
    rname = fname[:-9]
  elif fname.endswith('.json'):
    rname = fname[:-5]
  else:
    raise ValueError(f'{fname} does not end in .tac.json or .json')
  tjs = None
  with open(fname, 'rb') as fp:
    tjs = json.load(fp)
  assert isinstance(tjs, list) and len(tjs) == 1, tjs
  tjs = tjs[0]
  assert 'proc' in tjs and tjs['proc'] == '@main', tjs
  asm = []
  print(tac_to_asm(tjs['body']))
  for line in tac_to_asm(tjs['body']):
    if line[:3] == "%.L":
        l = line[1:]
        asm.append(l)
    else:
        asm.append('\t' + line)
    
#   asm = ['\t' + line for line in tac_to_asm(tjs['body'])]
  asm[:0] = [f'\t.section .rodata',
             f'.lprintfmt:',
             f'\t.string "%ld\\n"',
             f'\t.text',
             f'\t.globl main',
             f'main:']
  xname = rname + '.exe'
  sname = rname + '.s'
  with open(sname, 'w') as afp:
    print(*asm, file=afp, sep='\n')
  print(f'{fname} -> {sname}')
  # SINCE WE ARE ONLY MAKING THE ASSEMBLY FILE, WE DON'T EXECUTE THIS
  if sys.platform != "win32":
    # We only create the executable on Linux
    os.system(f'gcc -o {xname} {sname}')
    print(f'{sname} -> {xname}')
  else:
    print("Not making executeable on Windows")

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print(f'Usage: {sys.argv[0]} tacfile.tac.json')
    sys.exit(1)
  compile_tac(sys.argv[1])
