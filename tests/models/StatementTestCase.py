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

    def test_find(self):
        g = Graph("TEST")
        f = g.register("VARMAP.1")
        v1 = g.register("VARIABLE.1")
        v2 = g.register("VARIABLE.2")

        v1["NAME"] = Literal("X")
        v2["NAME"] = Literal("Y")

        v1["VALUE"] = 1
        v2["VALUE"] = 1

        f["_WITH"] = [v1, v2]
        vm = VariableMap(f)
        self.assertEqual(vm.find("X"), v1)
        self.assertEqual(vm.find("Y"), v2)


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


class AddFillerStatementTestCase(unittest.TestCase):

    def test_run(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        addfiller = graph.register("TEST", isa="EXE.ADDFILLER-STATEMENT")
        target = graph.register("TARGET")

        addfiller["TO"] = target
        addfiller["SLOT"] = Literal("X")
        addfiller["ADD"] = 123

        Statement.from_instance(addfiller).run(None)
        self.assertTrue(target["X"] == 123)

        Statement.from_instance(addfiller).run(None)
        self.assertTrue(target["X"] == [123, 123])

    def test_run_variable_to(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        addfiller = graph.register("TEST", isa="EXE.ADDFILLER-STATEMENT")
        target = graph.register("TARGET")
        varmap = graph.register("VARMAP")

        addfiller["TO"] = Literal("$VAR")
        addfiller["SLOT"] = Literal("X")
        addfiller["ADD"] = 123

        varmap = VariableMap(varmap)
        Variable.instance(graph, "$VAR", target, varmap)

        Statement.from_instance(addfiller).run(varmap)
        self.assertTrue(target["X"] == 123)

    def test_run_variable_value(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        addfiller = graph.register("TEST", isa="EXE.ADDFILLER-STATEMENT")
        target = graph.register("TARGET")
        varmap = graph.register("VARMAP")
        Variable.instance(graph, "MYVAR", 123, VariableMap(varmap))

        addfiller["TO"] = target
        addfiller["SLOT"] = Literal("X")
        addfiller["ADD"] = Literal("MYVAR")

        Statement.from_instance(addfiller).run(VariableMap(varmap))
        self.assertTrue(target["X"] == 123)

    def test_run_returning_statement_results(self):

        class TestStatement(Statement):
            def run(self, varmap: VariableMap):
                return 123

        network = Network()
        graph = network.register(Statement.hierarchy())
        addfiller = graph.register("TEST", isa="EXE.ADDFILLER-STATEMENT")
        target = graph.register("TARGET")
        stmt = graph.register("TEST-STMT", isa="EXE.RETURNING-STATEMENT")

        graph["RETURNING-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)

        addfiller["TO"] = target
        addfiller["SLOT"] = Literal("X")
        addfiller["ADD"] = stmt

        Statement.from_instance(addfiller).run(None)
        self.assertTrue(target["X"] == 123)


class AssignFillerStatementTestCase(unittest.TestCase):

    def test_run(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        assignfiller = graph.register("TEST", isa="EXE.ASSIGNFILLER-STATEMENT")
        target = graph.register("TARGET")

        assignfiller["TO"] = target
        assignfiller["SLOT"] = Literal("X")
        assignfiller["ADD"] = 123

        Statement.from_instance(assignfiller).run(None)
        self.assertTrue(target["X"] == 123)

        assignfiller["ADD"] = 345
        Statement.from_instance(assignfiller).run(None)
        self.assertTrue(target["X"] == 345)
        self.assertTrue(target["X"] != 123)

    def test_run_variable_to(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        assignfiller = graph.register("TEST", isa="EXE.ASSIGNFILLER-STATEMENT")
        target = graph.register("TARGET")
        varmap = graph.register("VARMAP")

        assignfiller["TO"] = Literal("$VAR")
        assignfiller["SLOT"] = Literal("X")
        assignfiller["ADD"] = 123

        varmap = VariableMap(varmap)
        Variable.instance(graph, "$VAR", target, varmap)

        Statement.from_instance(assignfiller).run(varmap)
        self.assertTrue(target["X"] == 123)

    def test_run_variable_value(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        assignfiller = graph.register("TEST", isa="EXE.ASSIGNFILLER-STATEMENT")
        target = graph.register("TARGET")
        varmap = graph.register("VARMAP")
        Variable.instance(graph, "MYVAR", 123, VariableMap(varmap))

        assignfiller["TO"] = target
        assignfiller["SLOT"] = Literal("X")
        assignfiller["ADD"] = Literal("MYVAR")

        Statement.from_instance(assignfiller).run(VariableMap(varmap))
        self.assertTrue(target["X"] == 123)

    def test_run_returning_statement_results(self):

        class TestStatement(Statement):
            def run(self, varmap: VariableMap):
                return 123

        network = Network()
        graph = network.register(Statement.hierarchy())
        assignfiller = graph.register("TEST", isa="EXE.ASSIGNFILLER-STATEMENT")
        target = graph.register("TARGET")
        stmt = graph.register("TEST-STMT", isa="EXE.RETURNING-STATEMENT")

        graph["RETURNING-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)

        assignfiller["TO"] = target
        assignfiller["SLOT"] = Literal("X")
        assignfiller["ADD"] = stmt

        Statement.from_instance(assignfiller).run(None)
        self.assertTrue(target["X"] == 123)


class ExistsStatementTestCase(unittest.TestCase):

    def test_run(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        stmt = graph.register("TEST", isa="EXE.EXISTS-STATEMENT")

        stmt["FIND"] = Query.parse(graph._network, "WHERE @ ^ EXE.EXISTS-STATEMENT")
        self.assertTrue(Statement.from_instance(stmt).run(None))

        stmt["FIND"] = Query.parse(graph._network, "WHERE abc=123")
        self.assertFalse(Statement.from_instance(stmt).run(None))


class ForEachStatementTestCase(unittest.TestCase):

    def test_run(self):

        class TestStatement(Statement):
            def run(self, varmap: VariableMap):
                frame = varmap.resolve("$FOR")
                frame["c"] = frame["a"][0].resolve().value + frame["b"][0].resolve().value

        network = Network()
        graph = network.register(Statement.hierarchy())
        foreach = graph.register("TEST", isa="EXE.FOREACH-STATEMENT")
        stmt = graph.register("TEST", isa="EXE.STATEMENT")
        varmap = graph.register("VARMAP")

        target1 = graph.register("TARGET", generate_index=True)
        target2 = graph.register("TARGET", generate_index=True)

        target1["a"] = 1
        target2["a"] = 1
        target1["b"] = 2
        target2["b"] = 3

        graph["STATEMENT"]["CLASSMAP"] = Literal(TestStatement)

        foreach["FROM"] = Query.parse(graph._network, "WHERE a = 1")
        foreach["ASSIGN"] = Literal("$FOR")
        foreach["DO"] = stmt

        Statement.from_instance(foreach).run(VariableMap(varmap))

        self.assertTrue(target1["c"] == 3)
        self.assertTrue(target2["c"] == 4)


class IsStatementTestCase(unittest.TestCase):

    def test_run(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        stmt = graph.register("TEST", isa="EXE.IS-STATEMENT")
        target = graph.register("TARGET")

        stmt["DOMAIN"] = target
        stmt["SLOT"] = Literal("X")
        stmt["FILLER"] = 123

        stmt = Statement.from_instance(stmt)

        self.assertFalse(stmt.run(None))

        target["X"] = 123
        self.assertTrue(stmt.run(None))

    def test_variable_domain(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        stmt = graph.register("TEST", isa="EXE.IS-STATEMENT")
        target = graph.register("TARGET")
        varmap = graph.register("VARMAP")

        stmt["DOMAIN"] = Literal("$VAR")
        stmt["SLOT"] = Literal("X")
        stmt["FILLER"] = 123

        varmap = VariableMap(varmap)
        Variable.instance(graph, "$VAR", target, varmap)

        stmt = Statement.from_instance(stmt)

        self.assertFalse(stmt.run(varmap))

        target["X"] = 123
        self.assertTrue(stmt.run(varmap))

    def test_variable_filler(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        stmt = graph.register("TEST", isa="EXE.IS-STATEMENT")
        target = graph.register("TARGET")
        varmap = graph.register("VARMAP")

        stmt["DOMAIN"] = target
        stmt["SLOT"] = Literal("X")
        stmt["FILLER"] = Literal("$VAR")

        varmap = VariableMap(varmap)
        Variable.instance(graph, "$VAR", 123, varmap)

        stmt = Statement.from_instance(stmt)

        self.assertFalse(stmt.run(varmap))

        target["X"] = 123
        self.assertTrue(stmt.run(varmap))


class MakeInstanceStatementTestCase(unittest.TestCase):

    def test_run(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        makeinstance = graph.register("TEST", isa="EXE.MAKEINSTANCE-STATEMENT")
        target = graph.register("TARGET")

        makeinstance["IN"] = Literal("EXE")
        makeinstance["OF"] = target
        makeinstance["PARAMS"] = [1, 2, 3]

        target["WITH"] = [Literal("$A"), Literal("$B"), Literal("$C")]

        instance = Statement.from_instance(makeinstance).run(None)
        self.assertTrue(instance.name() in graph)
        self.assertEqual(VariableMap(instance).resolve("$A"), 1)
        self.assertEqual(VariableMap(instance).resolve("$B"), 2)
        self.assertEqual(VariableMap(instance).resolve("$C"), 3)

        other = network.register("OTHER")
        makeinstance["IN"] = Literal("OTHER")
        instance = Statement.from_instance(makeinstance).run(None)
        self.assertTrue(instance.name() in other)

    def test_raises_exception_on_mismatched_params(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        makeinstance = graph.register("TEST", isa="EXE.MAKEINSTANCE-STATEMENT")
        target = graph.register("TARGET")

        makeinstance["OF"] = target
        makeinstance["PARAMS"] = [1, 2, 3]

        with self.assertRaises(Exception):
            Statement.from_instance(makeinstance).run(None)


class MeaningProcedureStatementTestCase(unittest.TestCase):

    def test_run(self):
        result = 0

        def TestMP(statement, a, b, c):
            nonlocal result
            result += a
            result += b
            result += c
            result += statement.frame["X"][0].resolve().value

        from backend.models.mps import MPRegistry
        MPRegistry.register(TestMP)

        network = Network()
        graph = network.register(Statement.hierarchy())
        mp = graph.register("TEST", isa="EXE.MP-STATEMENT")

        mp["CALLS"] = Literal(TestMP.__name__)
        mp["PARAMS"] = [1, 2, 3]
        mp["X"] = 4

        Statement.from_instance(mp).run(None)

        self.assertEqual(result, 10)

    def test_run_with_variables(self):
        result = 0

        def TestMP(statement, a, b, c):
            nonlocal result
            result += a
            result += b
            result += c
            result += statement.frame["X"][0].resolve().value

        from backend.models.mps import MPRegistry
        MPRegistry.register(TestMP)

        network = Network()
        graph = network.register(Statement.hierarchy())
        mp = graph.register("TEST", isa="EXE.MP-STATEMENT")
        varmap = graph.register("VARMAP")

        mp["CALLS"] = Literal(TestMP.__name__)
        mp["PARAMS"] = [1, 2, Literal("$var")]
        mp["X"] = 4

        varmap = VariableMap(varmap)
        Variable.instance(graph, "$var", 3, varmap)

        Statement.from_instance(mp).run(varmap)

        self.assertEqual(result, 10)