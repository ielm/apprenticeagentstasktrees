from backend.models.graph import Frame, Graph, Identifier, Literal, Network
from backend.models.query import Query
from backend.models.statement import Statement, Variable, VariableMap

import unittest


class VariableTestCase(unittest.TestCase):

    def test_name(self):
        f = Frame("TEST.1")
        f["NAME"] = Literal("VAR_X")

        var = Variable(f)
        self.assertEqual(var.name(), "VAR_X")

    def test_varmap(self):
        g = Graph("TEST")
        vm = g.register("VARMAP.1")
        v = g.register("TEST.1")
        v["FROM"] = vm

        var = Variable(v)
        self.assertEqual(var.varmap(), vm)
        self.assertIsInstance(var.varmap(), VariableMap)

    def test_value(self):
        f = Frame("TEST.1")
        f["VALUE"] = 123

        var = Variable(f)
        self.assertEqual(var.value(), 123)


class VariableMapTestCase(unittest.TestCase):

    def test_instance_of(self):
        g = Graph("DEF")
        f = g.register("VARMAPDEF.1")
        f["WITH"] = [Literal("VAR_X"), Literal("VAR_Y")]

        params = [1, 2]

        vm = VariableMap.instance_of(g, f, params)
        self.assertTrue(vm.frame["WITH"] == Literal("VAR_X"))
        self.assertTrue(vm.frame["WITH"] == Literal("VAR_Y"))
        self.assertTrue(vm.frame["_WITH"] == Identifier.parse("DEF.VARIABLE.1"))
        self.assertTrue(vm.frame["_WITH"] == Identifier.parse("DEF.VARIABLE.2"))

        self.assertIn("DEF.VARIABLE.1", g)
        self.assertIn("DEF.VARIABLE.2", g)

        self.assertEqual(Variable(g["VARIABLE.1"]).name(), "VAR_X")
        self.assertEqual(Variable(g["VARIABLE.2"]).name(), "VAR_Y")

        self.assertEqual(Variable(g["VARIABLE.1"]).varmap(), vm)
        self.assertEqual(Variable(g["VARIABLE.2"]).varmap(), vm)

        self.assertEqual(Variable(g["VARIABLE.1"]).value(), 1)
        self.assertEqual(Variable(g["VARIABLE.2"]).value(), 2)

    def test_instance_of_with_existing_frame(self):
        g = Graph("DEF")
        existing = g.register("EXISTING.1")
        f = g.register("VARMAPDEF.1")
        f["WITH"] = [Literal("VAR_X"), Literal("VAR_Y")]

        params = [1, 2]

        vm = VariableMap.instance_of(g, f, params, existing=existing)
        self.assertEqual(vm.frame, existing)

        self.assertTrue(existing["WITH"] == Literal("VAR_X"))
        self.assertTrue(existing["WITH"] == Literal("VAR_Y"))
        self.assertTrue(existing["_WITH"] == Identifier.parse("DEF.VARIABLE.1"))
        self.assertTrue(existing["_WITH"] == Identifier.parse("DEF.VARIABLE.2"))

        self.assertIn("DEF.VARIABLE.1", g)
        self.assertIn("DEF.VARIABLE.2", g)

        self.assertEqual(Variable(g["VARIABLE.1"]).name(), "VAR_X")
        self.assertEqual(Variable(g["VARIABLE.2"]).name(), "VAR_Y")

        self.assertEqual(Variable(g["VARIABLE.1"]).varmap(), vm)
        self.assertEqual(Variable(g["VARIABLE.2"]).varmap(), vm)

        self.assertEqual(Variable(g["VARIABLE.1"]).value(), 1)
        self.assertEqual(Variable(g["VARIABLE.2"]).value(), 2)

    def test_assign(self):
        g = Graph("TEST")
        f = g.register("VARMAP.1")
        v1 = g.register("VARIABLE.1")
        v2 = g.register("VARIABLE.2")
        v3 = g.register("VARIABLE.3")
        v4 = g.register("VARIABLE.4")

        v1["NAME"] = Literal("V1")
        v2["NAME"] = Literal("V2")
        v3["NAME"] = Literal("V3")
        v4["NAME"] = Literal("V4")

        vm = VariableMap(f)
        vm.assign("VAR1", Variable(v1))
        vm.assign("VAR2", v2)
        vm.assign("VAR3", v3._identifier)
        vm.assign("VAR3", "TEST.VARIABLE.4")

        self.assertEqual(f["_WITH"], v1)
        self.assertEqual(f["_WITH"], v2)
        self.assertEqual(f["_WITH"], v3)
        self.assertEqual(f["_WITH"], v4)

    def test_assign_requires_unique_names(self):
        g = Graph("TEST")
        f = g.register("VARMAP.1")
        v = g.register("VARIABLE")

        vm = VariableMap(f)
        vm.assign("VAR1", v)

        with self.assertRaises(Exception):
            vm.assign("VAR1", v)

    def test_resolve(self):
        g = Graph("TEST")
        f = g.register("VARMAP.1")
        v1 = g.register("VARIABLE.1")
        v2 = g.register("VARIABLE.2")

        v1["NAME"] = Literal("X")
        v1["VALUE"] = 1

        v2["NAME"] = Literal("Y")
        v2["VALUE"] = 2

        f["_WITH"] = [v1, v2]

        vm = VariableMap(f)
        self.assertEqual(vm.resolve("X"), 1)
        self.assertEqual(vm.resolve("Y"), 2)


class StatementTestCase(unittest.TestCase):

    def test_run(self):

        class TestStatement(Statement):
            def run(self, varmap: VariableMap):
                return varmap.resolve("X")

        graph = Graph("TEST")

        stmt = graph.register("STATEMENT")
        varmap = graph.register("VARMAP")
        varmap["WITH"] = Literal("X")

        vm = VariableMap.instance_of(graph, varmap, [123])
        statement = TestStatement(stmt)

        self.assertEqual(123, statement.run(vm))

    def test_from_instance(self):

        class TestStatement(Statement):
            def run(self, varmap: VariableMap):
                return 1

        graph = Statement.hierarchy()
        graph.register("TEST-STATEMENT", isa="EXE.STATEMENT")
        graph["TEST-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)

        frame = graph.register("TEST.1", isa="TEST-STATEMENT")
        stmt = Statement.from_instance(frame)

        self.assertIsInstance(stmt, TestStatement)


class ExistsStatementTestCase(unittest.TestCase):

    def test_run(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        stmt = graph.register("TEST", isa="EXE.EXISTS-STATEMENT")

        stmt["FIND"] = Query.parse(graph._network, "WHERE @ ^ EXE.EXISTS-STATEMENT")
        self.assertTrue(Statement.from_instance(stmt).run(None))

        stmt["FIND"] = Query.parse(graph._network, "WHERE abc=123")
        self.assertFalse(Statement.from_instance(stmt).run(None))