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
            elif len(instr["args"]) == 0:
                args = ""
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
        if len(self.instrs)==0:
            print("Error the instruction list is empty")
            return
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

    def remove_last_instr(self):
        self.instrs.pop()

class CFG:
    def __init__(self,proc,nodes):
        self.proc= proc
        self.nodes=nodes
        self.nodes_to_labels = {node:node.label for node in self.nodes}
        self.labels_to_nodes = {node.label:node for node in self.nodes}
        self.entry = self.nodes[0]
        self.edges=dict()
        self.update_edges()

    def __str__(self):
        res = ""
        for node in self.nodes:
            res += str(node) + "\n"
        return res

    def update_edges(self):
        """
        Update the edges dictionnary using the information stored in the node
        objects
        """
        self.edges=dict()
        for node in self.nodes:
            self.edges[node.label]=node.dests
        self.nodes_to_labels = {node:node.label for node in self.nodes}
        self.labels_to_nodes = {node.label:node for node in self.nodes}

    def next_node(self,node):
        ret=[]
        for lab in node.dests:
            node=self.labels_to_nodes[lab]
            if node not in ret:
                ret.append(node)
        return ret

    def next(self, node):
        """
        Polymorphic function that return the list of successors to a node
        """
        if isinstance(node, str):
            if node in self.labels_to_nodes.keys():
                node = self.labels_to_nodes[node]
            else:
                return []
        return node.dests

    def prev(self, node):
        """
        Polymorphic function that returns the list of predecessors to a node
        """
        if isinstance(node, str):
            label = node
        else:
            label = node.label

        prevs=[]
        for lab, dests in self.edges.items():
            if label in dests:
                prevs.append(lab)
        return prevs

    def new_node(self, node):
        """
        Given a node object, add it to self.nodes and update the edges
        """
        if node not in self.nodes:
            self.nodes.append(node)
            self.update_edges()

    def delete_node(self, node):
        """
        Takes a block or a label and removes it from the cfg
        We assume that the node is disjoint from the rest of the graph
        """
        if isinstance(node, str):
            node = self.labels_to_nodes[node]
        label=node.label
        self.nodes.remove(node)
        del self.edges[label]
        self.update_edges()
        self.entry = self.nodes[0]

    def remove_edge(self,src,dest):
        """
        Given source and destination labels, remove the corresponding edge to
        self.edges
        """
        if dest in self.edges[src]:
            self.edges[src].remove(dest)

    def add_edge(self,src,dest):
        """
        Given source and destination labels, add the corresponding edge to
        self.edges
        """
        if dest not in self.edges[src]:
            self.edges[src].append(dest)

    def aux_uce(self, node_label, visited):
        visited.add(node_label)
        for nbr_label in self.next(node_label):
            if nbr_label not in visited:
                self.aux_uce(nbr_label, visited)

    def uce(self):
        visited = set()
        self.aux_uce(self.entry.label, visited)

        to_delete = []
        for node in self.nodes:
            if node.label not in visited:
                to_delete.append(node)

        for node in to_delete:
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
                if instr["opcode"] in implied and \
                   instr["args"][0] == temporary:
                    newline = {"opcode":"jmp",
                               "args":[instr["args"][1]],
                               "result":None}
                    B2.replace_line(i, newline)
                    B2.remove_lines(i+1, -1)
                    break
                if instr["opcode"] in negated and \
                   instr["args"][0] == temporary:
                    to_delete.append(i)

            for i in to_delete[::-1]:
                B2.remove_lines(i, i+1)


    def jp2(self):
        for node in self.nodes:
            self.jp2_node(node)

        for node in self.nodes:
            node.update_jumps()

        self.update_edges()
        self.uce()

    def coalesce_aux(self):
        # print(self.edges)
        i=1
        nl=[]
        jl=[]
        for label in self.edges.keys():
            # print(i,label)
            i+=1
            if len(self.edges[label]) ==1 and self.prev(self.labels_to_nodes[self.edges[label][0]])==[label]:
                # print("ok")
                nl.append(label)
                nl.append(self.edges[label][0])
                jl.append(nl)
                nl=[]
        return jl
    
    def coalesce(self):
        jl=self.coalesce_aux()
        init_len=len(jl)
        while init_len>0:
            # print(jl)
            ls=jl[0]
            if len(ls)==2:
                # print(ls)
                label=ls[0]
                # print("Before this operation, my label is", self.labels_to_nodes[label].instrs[0])
                linstr=self.labels_to_nodes[label].last_instr()
                # print("And my last instr is",linstr)
                if linstr["opcode"]=='jmp':
                    self.labels_to_nodes[label].remove_last_instr()
                new_body=self.labels_to_nodes[self.edges[label][0]].instrs
                # print(new_body[0])
                del new_body[0]
                self.labels_to_nodes[label].append_instrs(new_body)
                # print("After this operation, my label is", self.labels_to_nodes[label].instrs[0])
                for edg in self.edges[self.edges[label][0]]:
                    self.edges[label].append(edg)
                self.delete_node(self.labels_to_nodes[self.edges[label][0]])
                self.edges[label].remove(ls[1])
                self.update_edges()
            init_len-=1
            jl=self.coalesce_aux()    
        # print(self.edges)
        # print(self.labels_to_nodes['%.L4'].instrs)



    def jp1_aux(self):
        """creates a node list of all the linear sequences inside the cfg"""
        init_len=len(self.nodes)
        nl=[]
        jl=[]
        for i in range(0,init_len):
            node=self.nodes[i]
            nl.append(node)
            if len(node.dests)==1 and self.prev(self.nodes[i+1])[-1]==node.label and node.last_instr()["opcode"] == "jmp":
                continue
            else:
                jl.append(nl)
                nl=[]
        return jl
                

    def jp1(self):
        jl=self.jp1_aux()
        for ls in jl:
            if len(ls)>2:
                first=jl[0]
                first.remove_lines(-2,-1)
                label=ls[-1].label()
                first.append_instrs({'opcode': 'jmp', 'args': [label], 'result': None})
                self.uce()


    def serialize(self):
        visited=set()
        body=[]
        nl=[self.entry]
        ret_node=[]
        while len(nl)>0:
            node=nl.pop()
            if node in visited:
                continue
            if len(node.dests)-len(node.cond_jumps)==0:
                ret_node.append(node)
                continue
            visited.add(node)
            body+=node.instrs
            nl.extend(self.next_node(node))
        while len(ret_node)>0:
            node=ret_node.pop()
            if node in visited:
                continue
            visited.add(node)
            body+=node.instrs
            body=filter_fallthrough(body)
        return body

def filter_fallthrough(body):
    new_body=[]
    init_length=len(body)
    for i in range(0, init_length):
        if body[i]["opcode"]=='jmp':
            arg=body[i]["args"][-1]
            if body[i+1]["opcode"]=="label" and body[i+1]["args"][-1]==arg:
                continue
        new_body.append(body[i])
    return new_body