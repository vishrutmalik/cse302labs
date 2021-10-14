import sys

class Node:
    def __init__(self,label,body=None):
        self.label=label
        self.instrs= body if body is not None else []
        self.size = len(self.instrs)
        self.dests=[]
        self.cond_jumps=[]
        self.update_jumps()

    def __str__(self):
        res = ""
        for instr in self.instrs:
            if len(instr["args"]) == 1:
                args = instr["args"][0]
            else:
                arg1 = instr["args"][0]
                arg2 = instr["args"][1]
                args = f"{arg1}, {arg2}"
            opcode = instr["opcode"]
            if instr["result"] is None:
                res += f"{opcode} {args}\n"
            else:
                result = instr["result"]
                res += f"{result} = {opcode} {args}\n"
        return res

    def last_instr(self):
        return self.instrs[-1]

    def append_instrs(self,instrs):
        for instr in instrs:
            self.instrs.append(instr)

    def update_jumps(self):
        self.dests = []
        self.cond_jumps = []
        for i, instr in enumerate(self.instrs):
            instruction = instr["opcode"]
            args = instr["args"]
            if instruction[0]=='j':
                if instruction != "jmp":
                    self.cond_jumps.append((instruction, args[0], args[1], i))
                if args[-1] not in self.dests:
                    self.dests.append(args[-1])
        self.remove_modified_jumps()

    def remove_modified_jumps(self):
        temp = self.cond_jumps.copy()
        for jump in temp:
            for line in range(jump[3]+1, self.size):
                if self.instrs[line]["result"] == jump[1]:
                    self.cond_jumps.remove(jump)
                    break

    def replace_line(self, lineno, newline):
        self.instrs[lineno] = newline

    def remove_lines(self, startline, endline):
        if endline == -1:
            self.instrs = self.instrs[:startline]
        else:
            assert startline < endline
            self.instrs = self.instrs[:startline] + self.instrs[endline:]


class CFG:
    def __init__(self,proc,nodes):
        self.proc= proc
        self.nodes=nodes
        self.nodes_to_labels = {node:node.label for node in self.nodes}
        self.labels_to_nodes = {node.label:node for node in self.nodes}
        self.entry = self.nodes[0]
        self.edges=dict()
        self.update_edges()


    def update_edges(self):
        self.edges=dict()
        for node in self.nodes:
            self.edges[node.label]=node.jumps

    def next(self, node):
        return self.edges[node.label]

    def prev(self, node):
        prevs=[]
        for lab in self.edges.keys():
            if node.label in self.edges[lab]:
                prevs.append(lab)
        return prevs

    def new_node(self, node):
        if node not in self.nodes:
            self.nodes.append(node)
            self.update_edges()

    def delete_node(self, node):
        if node in self.nodes:
            for dest in self.edges[node.label]:
                self.remove_edge(node.label,dest)
            for nd in self.nodes:
                if node.label in self.edges[nd]:
                    self.remove_edge(nd.label, node.label)
            self.nodes.remove(node)

    def remove_edge(self,src,dest):
        if dest in self.edges[src]:
            self.edges[src].remove(dest)

    def add_edge(self,src,dest):
        if dest not in self.edges[src]:
            self.edges[src].append(dest)

    def aux_uce(self, node, visited):
        visited.add(node)
        for nbr_label in self.next(node):
            neighbour = self.labels_to_nodes[nbr_label]
            if neighbour not in visited:
                self.aux_uce(neighbour, visited)

    def uce(self):
        visited = set()
        self.aux_uce(self.entry, visited)
        for node in self.nodes:
            if node not in visited:
                self.delete_node(node)
        self.update_edges()

    def jp2_node(self, node):
        implications = {"jz":["jz"], "jl":["jl", "jle", "jnz"], "jle":["jle"],
                        "jnz":["jnz"], "jnl":["jnl"], "jnle":["jnle", "jnl",
                                                              "jnz"]}
        negations = {"jz":["jl", "jnle", "jnz"], "jl":["jnl", "jnle", "jz"],
                     "jle":["jnle"], "jnz":["jz"], "jnl":["jl"], "jnle":["jz",
                                                                         "jl",
                                                                         "jle"]}
        for jump, temporary, dest, _ in node.cond_jumps:
            B2 = self.labels_to_nodes[dest]
            implied = implications[jump]
            negated = negations[jump]
            if self.prev(B2) != [node.label]:
                break
            # we store lines to delete to later remove them in reverse order
            to_delete = []
            for i, instr in enumerate(B2.instrs):
                if instr["result"] == temporary:
                    break
                if instr["opcode"] in implications and \
                   instr["args"][0] == temporary:
                    newline = {"opcode":"jmp",
                               "args":[instr["args"][1]],
                               "result":None}
                    B2.replace_line(i, newline)
                    B2.remove_lines(i+1, -1)
                    B2.update_jumps()
                    break
                if instr["opcode"] in negations:
                    to_delete.append(i)
            for i in to_delete[::-1]:
                B2.remove_lines(i, i+1)

    def jp2(self):
        for node in self.nodes:
            self.jp2_node(node)
        self.uce()

    def coalesce(self):
        #we just shift the properties to the parent node after removing jmp instr
        for label in self.edges.keys():
            if len(self.edges[label]) ==1 and self.prev(self.labels_to_nodes(self.edges[label][0]))==[label]:
                linstr=self.labels_to_nodes[label].last_instr()
                if linstr["opcode"]=='jmp':
                    self.labels_to_nodes[label].remove_lines(-2,-1)
                new_body=self.labels_to_nodes[self.edges[label]].instrs
                self.labels_to_nodes[self.edges[label]].append_instrs(new_body)
                for edg in self.edges[self.edges[label][0]]:
                    self.edges[label].append(edg)
                self.delete_node(self.labels_to_nodes[self.edges[label][0]])
                self.update_edges()