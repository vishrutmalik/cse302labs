from tac import *
import ssagen
from cfg import *
import json
import sys
import argparse

def dse(cfg):
    live_in, live_out = dict(), dict()
    exceptions=["call", "div", "mod"]
    case=True
    while case:
        recompute_liveness(cfg, live_in, live_out)
        case=False
        for instr in cfg.instrs():
            case_i = True
            new_def = False
            for new_temp in instr.defs():
                new_def= True
                if new_temp in live_out[instr]:
                    case_i=False
            if new_def:
                if case_i:
                    if instr.opcode == 'copy':
                        instr.dest = None
                        instr.opcode = 'dead'
                        instr.arg1 = None
                        instr.arg2 = None
                        case=True
                    elif instr.opcode in exceptions:
                       continue
                    else:
                        instr.dest = None
                        instr.opcode = 'dead'
                        instr.arg1 = None
                        instr.arg2 = None
                        case = True

def cpg(cfg):
    nodes = cfg._blockmap
    for node in nodes.values():
        instrs = [instr for instr in node.instrs()]
        if len(node.body)>0:
            for instr in instrs:
                if instr.opcode == 'copy':
                    propogate(cfg, instr.dest, instr.arg1)
                    instr.dest = None
                    instr.opcode = 'dead'
                    if instr.arg1 is not None:
                        instr.arg1 = None
                    if instr.arg2 is not None:
                        instr.arg2 = None

def propogate(cfg, new, old):
    nodes = cfg._blockmap
    for node in nodes.values():
        instrs = [instr for instr in node.instrs()]
        for instr in instrs:
            if instr.dest == new:
                instr.dest = old

            if isinstance(instr.arg1, dict):
                arg1 = {}
                for k,v in instr.arg1.items():
                    if v == new:
                        arg1[k] = old
                    else:
                        arg1[k] = v
                instr.arg1 = arg1
            elif instr.arg1 == new:
                instr.arg1 = old

            if isinstance(instr.arg2, dict):
                arg2 = {}
                for k,v in instr.arg2.items():
                    if v == new:
                        arg2[k] = old
                    else:
                        arg2[k] = v
                instr.arg2 = arg2
            elif instr.arg2 is not None and instr.arg2 == new:
                instr.arg2 = old

def remove_dead(proc):
    new_body = []
    for instr in proc.body:
        if instr.opcode == 'dead':
            continue
        else:
            new_body.append(instr)
    proc.body = new_body

def main(fname, sname):
    tac_obj=load_tac(fname)
    tac=[]
    
    for proc in tac_obj:
        if isinstance(proc, Gvar):
            continue
        proc_name = proc.name
        cfg = infer(proc)
        ssagen.crude_ssagen(proc,cfg)
        dse(cfg)
        cpg(cfg) 
        linearize(proc,cfg)
        remove_dead(proc)
        
        # proc_json = {}
        # proc_json["proc"] = proc_name
        # if len(proc.t_args) >0:
        #     proc_json["args"] = proc["args"]
        # proc_json["body"] = body 

    tac = [proc.js_obj for proc in tac_obj]

    if sname is None:
        print(tac)
    else:
        with open(sname, 'w') as f:
            json.dump(tac, f, indent=2)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fname")
    parser.add_argument("-o")
    args = parser.parse_args()
    
    cfg = main(args.fname, args.o)