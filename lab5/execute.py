from tac import *
import argparse

def execu(fname):
    gvars_, procs_ = dict(), dict()
    for decl in load_tac(fname):
            if isinstance(decl, Gvar): gvars_[decl.name] = decl
            else: procs_[decl.name] = decl
    execute(gvars_, procs_, '@main', [])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fname")
    args = parser.parse_args()
    cfg = execu(args.fname)