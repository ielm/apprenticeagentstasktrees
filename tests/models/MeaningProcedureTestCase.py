# from backend.models.graph import Frame, Graph, Literal
from backend.models.mps import AgentMethod, Executable, MeaningProcedure, MPRegistry, Registry
from io import StringIO
from ontograph import graph
from ontograph.Frame import Frame

import contextlib
import sys
import unittest


class RegistryTestCase(unittest.TestCase):

    def test_register(self):
        def test_mp(*args, **kwargs): pass

        registry = Registry()

        self.assertFalse(registry.has_mp(test_mp.__name__))

        registry.register(test_mp)

        self.assertTrue(registry.has_mp(test_mp.__name__))

        registry.register(test_mp, name="another-mp")

        self.assertTrue(registry.has_mp("another-mp"))

    def test_register_prints_warning(self):
        def test_mp(*args, **kwargs): pass

        registry = Registry()

        registry.register(test_mp)

        temp_stdout = StringIO()
        with contextlib.redirect_stdout(temp_stdout):
            registry.register(test_mp)

        output = temp_stdout.getvalue().strip()
        self.assertEqual(output, "Warning, overwriting meaning procedure '" + test_mp.__name__ + "'.")

    def test_run(self):
        proof_a = None
        proof_b = None

        class TestMP(AgentMethod):
            def run(self, *args, **kwargs):
                nonlocal proof_a
                proof_a = args[0]

                nonlocal proof_b
                if "test" in kwargs:
                    proof_b = kwargs["test"]

        registry = Registry()

        registry.register(TestMP)

        registry.run(TestMP.__name__, None, True)

        self.assertEqual(proof_a, True)
        self.assertIsNone(proof_b)

        registry.run(TestMP.__name__, None, False, test=123)

        self.assertEqual(proof_a, False)
        self.assertEqual(proof_b, 123)

    def test_run_throws_unknown_exception(self):
        registry = Registry()
        with self.assertRaises(Exception):
            registry.run("no-such-mp")


class MeaningProcedureTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_calls(self):
        def test_mp(*args, **kwargs): pass

        registry = Registry()
        registry.register(test_mp)

        frame = Frame("@TEST.MEANING-PROCEDURE.1")
        frame["CALLS"] = test_mp.__name__

        mp = MeaningProcedure(frame)
        self.assertEqual(mp.calls(), test_mp.__name__)

    def test_calls_raises_exception_if_not_one_property(self):
        frame = Frame("@TEST.MEANING-PROCEDURE.1")

        with self.assertRaises(Exception):
            MeaningProcedure(frame).calls()

        frame["CALLS"] += "test1"
        frame["CALLS"] += "test2"

        with self.assertRaises(Exception):
            MeaningProcedure(frame).calls()

    def test_run(self):
        proof_a = None
        proof_b = None

        class TestMP(AgentMethod):
            def run(self, *args, **kwargs):
                nonlocal proof_a
                proof_a = args[0]

                nonlocal proof_b
                if "test" in kwargs:
                    proof_b = kwargs["test"]

        MPRegistry.register(TestMP)

        frame = Frame("@TEST.MEANING-PROCEDURE.1")
        frame["CALLS"] = TestMP.__name__

        mp = MeaningProcedure(frame)
        mp.run(None, False, test=123)

        self.assertEqual(proof_a, False)
        self.assertEqual(proof_b, 123)

    def test_order(self):
        frame = Frame("@TEST.MEANING-PROCEDURE.1")

        mp = MeaningProcedure(frame)
        self.assertEqual(mp.order(), sys.maxsize)

        frame["ORDER"] = 1
        self.assertEqual(mp.order(), 1)

        frame["ORDER"] = [1, 2]
        self.assertEqual(mp.order(), 2)


class ExecutableTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_mps(self):
        e = Frame("@TEST.EXECUTABLE.1")
        mp1 = Frame("@TEST.MEANING-PROCEDURE.1")
        mp2 = Frame("@TEST.MEANING-PROCEDURE.2")

        e["RUN"] = [mp1, mp2]
        executable = Executable(e)

        self.assertTrue(mp1 in executable.mps())
        self.assertTrue(mp2 in executable.mps())
        self.assertTrue(MeaningProcedure(mp1) in executable.mps())
        self.assertTrue(MeaningProcedure(mp2) in executable.mps())

    def test_run_single(self):
        proof_a = None
        proof_b = None

        class TestMP(AgentMethod):
            def run(self, *args, **kwargs):
                nonlocal proof_a
                proof_a = args[0]

                nonlocal proof_b
                if "test" in kwargs:
                    proof_b = kwargs["test"]

        MPRegistry.register(TestMP)

        e = Frame("@TEST.EXECUTABLE.1")
        mp = Frame("@TEST.MEANING-PROCEDURE.1")

        e["RUN"] = mp
        mp["CALLS"] = TestMP.__name__

        executable = Executable(e)
        executable.run(None, False, test=123)

        self.assertEqual(proof_a, False)
        self.assertEqual(proof_b, 123)

    def test_run_multiple_respects_order(self):
        proof = None

        class TestMP1(AgentMethod):
            def run(self, *args, **kwargs):
                nonlocal proof
                proof = args[0]

        class TestMP2(AgentMethod):
            def run(self, *args, **kwargs):
                nonlocal proof
                proof = args[1]

        MPRegistry.register(TestMP1)
        MPRegistry.register(TestMP2)

        e = Frame("@TEST.EXECUTABLE.1")
        mp1 = Frame("@TEST.MEANING-PROCEDURE.1")
        mp2 = Frame("@TEST.MEANING-PROCEDURE.2")

        e["RUN"] = [mp1, mp2]
        mp1["CALLS"] = TestMP1.__name__
        mp2["CALLS"] = TestMP2.__name__
        mp1["ORDER"] = 2
        mp2["ORDER"] = 1

        executable = Executable(e)
        executable.run(None, 1, 2)

        self.assertEqual(proof, 1)

    def test_run_raises_exception_if_no_mps_found(self):
        executable = Executable(Frame("@TEST.FRAME.1"))
        with self.assertRaises(Exception):
            executable.run()