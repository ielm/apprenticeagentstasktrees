import unittest
from instructions import Instructions


class InstructionsTestCase(unittest.TestCase):

    tmr1 = {"results": None, "sentence": "tmr1"}
    tmr2 = {"results": None, "sentence": "tmr2"}
    tmr3 = {"results": None, "sentence": "tmr3"}

    action1 = {"action": 1}
    action2 = {"action": 2}
    action3 = {"action": 3}

    def test_tmr_sequence(self):
        ins = Instructions([
            self.tmr1, self.tmr2, self.tmr3
        ])

        results = list(ins)

        self.assertEqual(results, [[self.tmr1], [self.tmr2], [self.tmr3]])

    def test_action_sequence(self):
        ins = Instructions([
            self.action1, self.action2, self.action3
        ])

        results = list(ins)

        self.assertEqual(results, [[self.action1, self.action2, self.action3]])

    def test_mixed_sequence(self):
        ins = Instructions([
            self.tmr1, self.action1, self.tmr2, self.action2, self.action3, self.tmr3
        ])

        results = list(ins)

        self.assertEqual(results, [[self.tmr1], [self.action1], [self.tmr2], [self.action2, self.action3], [self.tmr3]])