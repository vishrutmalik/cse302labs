import unittest
import os
from cfg import *
from tac_cfopt import *

dirname, filename = os.path.split(os.path.abspath(__file__))

class testUce(unittest.TestCase):
    def setUp(self):
        fname = "./examples/dead_code.tac.json"

        with open(fname, 'r') as f:
            js_obj = json.load(f)

        proc = js_obj[0]
        new_proc = add_labels(proc)
        proc_name = new_proc["proc"]
        blocks = proc_to_blocks(new_proc)
        blocks = add_jumps(blocks)
        nodes = create_nodes(blocks)
        self.cfg = CFG(proc_name, nodes)


    def test_edges_init(self):
        expected_edges = {'%.L1': ['%.L4'],
                         '%.L2': ['%.L3'],
                         '%.L3': ['%.L4'],
                         '%.L4': ['%.L5'],
                         '%.L5': []}
        self.assertEqual(self.cfg.edges, expected_edges)

    def test_edges_node_removal(self):
        self.cfg.delete_node("%.L2")
        self.assertFalse(self.cfg.labels_to_nodes["%.L2"] in self.cfg.nodes)

    def test_uce_skip_two(self):
        expected_edges = {'%.L1': ['%.L4'],
                          '%.L4': ['%.L5'],
                          '%.L5': []}
        self.cfg.uce()
        self.assertEqual(self.cfg.edges, expected_edges)
        self.assertEqual(len(self.cfg.nodes), 3)

    def tearDown(self):
        del self.cfg

class testJP2(unittest.TestCase):

    def prepfile(self, fname):
        with open(fname, 'r') as f:
            js_obj = json.load(f)

        proc = js_obj[0]
        new_proc = add_labels(proc)
        proc_name = new_proc["proc"]
        blocks = proc_to_blocks(new_proc)
        blocks = add_jumps(blocks)
        nodes = create_nodes(blocks)
        return CFG(proc_name, nodes)

    def setUp(self):
        fname1 = "./examples/cond_jmps.tac.json"
        self.cfg1 = self.prepfile(fname1)

        fname2 = "./examples/cond_jmps2.tac.json"
        self.cfg2 = self.prepfile(fname2)

        fname3 = "./examples/cond_update_temp.tac.json"
        self.cfg3 = self.prepfile(fname3)

    def test_jp2_implied(self):
        self.cfg1.jp2()
        self.assertEqual(len(self.cfg1.nodes), 5)

        node2 = self.cfg1.labels_to_nodes["%.L2"]
        expected_jmp = {"opcode":"jmp", "args":["%.L3"], "result":None}

        self.assertEqual(node2.instrs[1], expected_jmp)
        self.assertEqual(len(node2.instrs), 2)

    def test_jp2_negated(self):
        self.cfg2.jp2()
        self.assertEqual(len(self.cfg2.nodes), 4)

        node2 = self.cfg2.labels_to_nodes["%.L2"]
        expected_jmp = {"opcode":"jmp", "args":["%.L30"], "result":None}

        self.assertEqual(node2.instrs[1], expected_jmp)
        self.assertEqual(len(node2.instrs), 2)

    def test_updating_temporary(self):
        self.cfg3.jp2()
        self.assertEqual(len(self.cfg2.nodes), 5)

        node2 = self.cfg3.labels_to_nodes["%.L2"]
        expected_jmp = {"opcode":"jz", "args":["%1", "%.L3"], "result":None}
        self.assertEqual(node2.instrs[2], expected_jmp)
        self.assertEqual(len(node2.instrs), 4)


    def tearDown(self):
        del self.cfg1
        del self.cfg2
        del self.cfg3


class testCoalescing(unittest.TestCase):
    
    def prepfile(self, fname):
        with open(fname, 'r') as f:
            js_obj = json.load(f)

        proc = js_obj[0]
        new_proc = add_labels(proc)
        proc_name = new_proc["proc"]
        blocks = proc_to_blocks(new_proc)
        blocks = add_jumps(blocks)
        nodes = create_nodes(blocks)
        return CFG(proc_name, nodes)

    def setUp(self):
            fname1 = "./examples/coalescing.tac.json"
            self.cfg1 = self.prepfile(fname1)

    def test_coalesce_nodes(self):
        self.assertEqual(len(self.cfg1.nodes), 5)
        self.cfg1.coalesce()
        self.assertEqual(len(self.cfg1.nodes), 3)
    
    def tearDown(self):
        del self.cfg1


class testSerialization(unittest.TestCase):
    
    def prepfile(self, fname):
        with open(fname, 'r') as f:
            js_obj = json.load(f)

        proc = js_obj[0]
        new_proc = add_labels(proc)
        proc_name = new_proc["proc"]
        blocks = proc_to_blocks(new_proc)
        blocks = add_jumps(blocks)
        nodes = create_nodes(blocks)
        return CFG(proc_name, nodes)

    def setUp(self):
            fname1 = "./examples/fib20.tac.json"
            self.cfg1 = self.prepfile(fname1)

            fname2 = "./examples/cond_jmps2.tac.json"
            self.cfg2 = self.prepfile(fname2)

            fname3 = "./examples/cond_update_temp.tac.json"
            self.cfg3 = self.prepfile(fname3)

    def test_remove_jmp(self):
        self.cfg1.uce()
        self.cfg1.jp2()
        self.cfg1.coalesce()
        res = self.cfg1.serialize()

        jmp_count_init = 0
        for node in self.cfg1.nodes:
            for instr in node.instrs:
                if instr["opcode"] == "jmp":
                    jmp_count_init += 1
        self.assertEqual(jmp_count_init, 3)

        jmp_count = 0
        for line in res:
            if line["opcode"] == "jmp":
                jmp_count += 1
        
        self.assertEqual(jmp_count, 2)
    
    def tearDown(self):
        del self.cfg1
        del self.cfg2
        del self.cfg3

if __name__ == "__main__":
    unittest.main()
