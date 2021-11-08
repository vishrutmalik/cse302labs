import unittest
from tac_cfopt import *

class testLoadingFull(unittest.TestCase):
    def setUp(self):
        fname = "./examples/cond_jmps.tac.json"

        with open(fname, 'r') as f:
            js_obj = json.load(f)

        self.proc = js_obj[0]

    def test_no_additional_labels(self):
        proc = add_labels(self.proc)

        label_count = 0
        labels = set()
        for instr in proc["body"]:
            if instr["opcode"] == "label":
                label = instr["args"][0]
                if label not in labels:
                    label_count += 1
                    labels.add(label)

        self.assertEqual(label_count, 5)

    def test_blocks(self):
        proc = add_labels(self.proc)
        blocks = proc_to_blocks(proc)
        self.assertEqual(len(blocks), 5)
        for block in blocks:
            self.assertEqual(block[0]["opcode"], "label")

    def test_no_fallthrough(self):
        proc = add_labels(self.proc)
        blocks = proc_to_blocks(proc)
        old_blocks = blocks.copy()
        blocks = add_jumps(blocks)

        self.assertEqual(old_blocks, blocks)

    def tearDown(self):
        del self.proc

class testLoading(unittest.TestCase):
    def setUp(self):
        fname = "./examples/cond.tac.json"

        with open(fname, 'r') as f:
            js_obj = json.load(f)

        self.proc = js_obj[0]

    def test_additional_labels(self):
        proc = add_labels(self.proc)

        label_count = 0
        labels = set()
        for instr in proc["body"]:
            if instr["opcode"] == "label":
                label = instr["args"][0]
                if label not in labels:
                    label_count += 1
                    labels.add(label)

        self.assertEqual(label_count, 5)

    def test_blocks(self):
        proc = add_labels(self.proc)
        blocks = proc_to_blocks(proc)
        self.assertEqual(len(blocks), 5)
        for block in blocks:
            self.assertEqual(block[0]["opcode"], "label")

    def test_fallthrough(self):
        proc = add_labels(self.proc)
        blocks = proc_to_blocks(proc)
        old_blocks = [block.copy() for block in blocks]
        blocks = add_jumps(blocks)

        self.assertNotEqual(old_blocks, blocks)

    def tearDown(self):
        del self.proc

if __name__ == "__main__":
    unittest.main()
