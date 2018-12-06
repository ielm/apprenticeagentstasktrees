from backend.models.effectors import Capability
from backend.models.graph import Frame, Graph, Identifier, Literal, Network
from backend.models.mps import AgentMethod, MPRegistry
from backend.models.query import Query
from backend.models.statement import Statement, StatementScope, Variable, VariableMap

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

    def test_variables(self):
        g = Graph("TEST")
        f = g.register("VARMAP")
        f["WITH"] += Literal("$var1")
        f["WITH"] += Literal("$var2")

        self.assertEqual(["$var1", "$var2"], VariableMap(f).variables())


class StatementTestCase(unittest.TestCase):

    def test_run(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope, varmap: VariableMap):
                return varmap.resolve("X")

        graph = Graph("TEST")

        stmt = graph.register("STATEMENT")
        varmap = graph.register("VARMAP")
        varmap["WITH"] = Literal("X")

        vm = VariableMap.instance_of(graph, varmap, [123])
        statement = TestStatement(stmt)

        self.assertEqual(123, statement.run(StatementScope(), vm))

    def test_from_instance(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope, varmap: VariableMap):
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

        Statement.from_instance(addfiller).run(StatementScope(), None)
        self.assertTrue(target["X"] == 123)

        Statement.from_instance(addfiller).run(StatementScope(), None)
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

        Statement.from_instance(addfiller).run(StatementScope(), varmap)
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

        Statement.from_instance(addfiller).run(StatementScope(), VariableMap(varmap))
        self.assertTrue(target["X"] == 123)

    def test_run_returning_statement_results(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope(), varmap: VariableMap):
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

        Statement.from_instance(addfiller).run(StatementScope(), None)
        self.assertTrue(target["X"] == 123)


class AssignFillerStatementTestCase(unittest.TestCase):

    def test_run(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        assignfiller = graph.register("TEST", isa="EXE.ASSIGNFILLER-STATEMENT")
        target = graph.register("TARGET")

        assignfiller["TO"] = target
        assignfiller["SLOT"] = Literal("X")
        assignfiller["ASSIGN"] = 123

        Statement.from_instance(assignfiller).run(StatementScope(), None)
        self.assertTrue(target["X"] == 123)

        assignfiller["ASSIGN"] = 345
        Statement.from_instance(assignfiller).run(StatementScope(), None)
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
        assignfiller["ASSIGN"] = 123

        varmap = VariableMap(varmap)
        Variable.instance(graph, "$VAR", target, varmap)

        Statement.from_instance(assignfiller).run(StatementScope(), varmap)
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
        assignfiller["ASSIGN"] = Literal("MYVAR")

        Statement.from_instance(assignfiller).run(StatementScope(), VariableMap(varmap))
        self.assertTrue(target["X"] == 123)

    def test_run_returning_statement_results(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope(), varmap: VariableMap):
                return 123

        network = Network()
        graph = network.register(Statement.hierarchy())
        assignfiller = graph.register("TEST", isa="EXE.ASSIGNFILLER-STATEMENT")
        target = graph.register("TARGET")
        stmt = graph.register("TEST-STMT", isa="EXE.RETURNING-STATEMENT")

        graph["RETURNING-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)

        assignfiller["TO"] = target
        assignfiller["SLOT"] = Literal("X")
        assignfiller["ASSIGN"] = stmt

        Statement.from_instance(assignfiller).run(StatementScope(), None)
        self.assertTrue(target["X"] == 123)


class AssignVariableStatementTestCase(unittest.TestCase):

    def test_run_assign_literal(self):
        network = Network()
        graph = network.register(Statement.hierarchy())

        assignvariable = graph.register("TEST", isa="EXE.ASSIGNVARIABLE-STATEMENT")
        assignvariable["TO"] = Literal("$var1")
        assignvariable["ASSIGN"] = 123

        varmap = VariableMap(graph.register("VARMAP"))
        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(123, varmap.resolve("$var1"))

    def test_run_assign_frame(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        target = graph.register("TARGET")

        assignvariable = graph.register("TEST", isa="EXE.ASSIGNVARIABLE-STATEMENT")
        assignvariable["TO"] = Literal("$var1")
        assignvariable["ASSIGN"] = target

        varmap = VariableMap(graph.register("VARMAP"))
        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(target, varmap.resolve("$var1"))

    def test_run_assign_variable(self):
        network = Network()
        graph = network.register(Statement.hierarchy())

        assignvariable = graph.register("TEST", isa="EXE.ASSIGNVARIABLE-STATEMENT")
        assignvariable["TO"] = Literal("$var1")
        assignvariable["ASSIGN"] = Literal("$existing")

        varmap = VariableMap(graph.register("VARMAP"))
        Variable.instance(graph, "$existing", 123, varmap)

        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(123, varmap.resolve("$var1"))

    def test_run_assign_statement_results(self):
        from backend.models.statement import ExistsStatement, MakeInstanceStatement, MeaningProcedureStatement

        class TestMP(AgentMethod):
            def run(self, *args, **kwargs):
                return 123
        MPRegistry.register(TestMP)

        network = Network()
        graph = network.register(Statement.hierarchy())

        assignvariable = graph.register("TEST", isa="EXE.ASSIGNVARIABLE-STATEMENT")
        varmap = VariableMap(graph.register("VARMAP"))

        assignvariable["TO"] = Literal("$var1")
        assignvariable["ASSIGN"] = MeaningProcedureStatement.instance(graph, "TestMP", [])
        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(123, varmap.resolve("$var1"))

        assignvariable["TO"] = Literal("$var2")
        assignvariable["ASSIGN"] = ExistsStatement.instance(graph, Frame.q(network).id("EXE.TEST"))
        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(True, varmap.resolve("$var2"))

        assignvariable["TO"] = Literal("$var3")
        assignvariable["ASSIGN"] = MakeInstanceStatement.instance(graph, graph._namespace, "EXE.TEST", [])
        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(graph["TEST.1"], varmap.resolve("$var3"))


class ExistsStatementTestCase(unittest.TestCase):

    def test_run(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        stmt = graph.register("TEST", isa="EXE.EXISTS-STATEMENT")

        stmt["FIND"] = Query.parse(graph._network, "WHERE @ ^ EXE.EXISTS-STATEMENT")
        self.assertTrue(Statement.from_instance(stmt).run(StatementScope(), None))

        stmt["FIND"] = Query.parse(graph._network, "WHERE abc=123")
        self.assertFalse(Statement.from_instance(stmt).run(StatementScope(), None))


class ForEachStatementTestCase(unittest.TestCase):

    def test_run(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope(), varmap: VariableMap):
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

        Statement.from_instance(foreach).run(StatementScope(), VariableMap(varmap))

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

        self.assertFalse(stmt.run(StatementScope(), None))

        target["X"] = 123
        self.assertTrue(stmt.run(StatementScope(), None))

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

        self.assertFalse(stmt.run(StatementScope(), varmap))

        target["X"] = 123
        self.assertTrue(stmt.run(StatementScope(), varmap))

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

        self.assertFalse(stmt.run(StatementScope(), varmap))

        target["X"] = 123
        self.assertTrue(stmt.run(StatementScope(), varmap))


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

        instance = Statement.from_instance(makeinstance).run(StatementScope(), None)
        self.assertTrue(instance.name() in graph)
        self.assertEqual(VariableMap(instance).resolve("$A"), 1)
        self.assertEqual(VariableMap(instance).resolve("$B"), 2)
        self.assertEqual(VariableMap(instance).resolve("$C"), 3)

        other = network.register("OTHER")
        makeinstance["IN"] = Literal("OTHER")
        instance = Statement.from_instance(makeinstance).run(StatementScope(), None)
        self.assertTrue(instance.name() in other)

    def test_raises_exception_on_mismatched_params(self):
        network = Network()
        graph = network.register(Statement.hierarchy())
        makeinstance = graph.register("TEST", isa="EXE.MAKEINSTANCE-STATEMENT")
        target = graph.register("TARGET")

        makeinstance["OF"] = target
        makeinstance["PARAMS"] = [1, 2, 3]

        with self.assertRaises(Exception):
            Statement.from_instance(makeinstance).run(StatementScope(), None)


class MeaningProcedureStatementTestCase(unittest.TestCase):

    def test_run(self):
        result = 0

        class TestMP(AgentMethod):
            def run(self, a, b, c):
                nonlocal result
                result += a
                result += b
                result += c
                result += self.statement.frame["X"][0].resolve().value

        from backend.models.mps import MPRegistry
        MPRegistry.register(TestMP)

        network = Network()
        graph = network.register(Statement.hierarchy())
        mp = graph.register("TEST", isa="EXE.MP-STATEMENT")

        mp["CALLS"] = Literal(TestMP.__name__)
        mp["PARAMS"] = [1, 2, 3]
        mp["X"] = 4

        Statement.from_instance(mp).run(StatementScope(), None)

        self.assertEqual(result, 10)

    def test_run_with_variables(self):
        result = 0

        class TestMP(AgentMethod):
            def run(self, a, b, c):
                nonlocal result
                result += a
                result += b
                result += c
                result += self.statement.frame["X"][0].resolve().value

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

        Statement.from_instance(mp).run(StatementScope(), varmap)

        self.assertEqual(result, 10)

    def test_capabilities(self):

        class TestMP(AgentMethod):
            def capabilities(self, a, b, c):
                return a + b + c

        from backend.models.mps import MPRegistry
        MPRegistry.register(TestMP)

        network = Network()
        graph = network.register(Statement.hierarchy())

        mp = graph.register("TEST", isa="EXE.MP-STATEMENT")
        mp["PARAMS"] = [1, 2, Literal("$var")]
        mp["CALLS"] = Literal(TestMP.__name__)

        varmap = graph.register("VARMAP")
        varmap = VariableMap(varmap)
        Variable.instance(graph, "$var", 3, varmap)

        self.assertEqual(6, Statement.from_instance(mp).capabilities(varmap))


class CapabilityStatementTestCase(unittest.TestCase):

    def test_run(self):
        result = 0

        class TestMP(AgentMethod):
            def run(self, a, b, c):
                nonlocal result
                result += a
                result += b
                result += c
                result += self.statement.frame["X"][0].resolve().value

        from backend.models.mps import MPRegistry
        MPRegistry.register(TestMP)

        network = Network()
        graph = network.register(Statement.hierarchy())

        Capability.instance(graph, "TEST-CAPABILITY", TestMP)

        cap = graph.register("TEST", isa="EXE.CAPABILITY-STATEMENT")
        cap["CAPABILITY"] = "EXE.TEST-CAPABILITY"
        cap["PARAMS"] = [1, 2, 3]
        cap["X"] = 4

        Statement.from_instance(cap).run(StatementScope(), None)

        self.assertEqual(result, 10)

    def test_run_with_variables(self):
        result = 0

        class TestMP(AgentMethod):
            def run(self, a, b, c):
                nonlocal result
                result += a
                result += b
                result += c
                result += self.statement.frame["X"][0].resolve().value

        from backend.models.mps import MPRegistry
        MPRegistry.register(TestMP)

        network = Network()
        graph = network.register(Statement.hierarchy())

        Capability.instance(graph, "TEST-CAPABILITY", TestMP)

        cap = graph.register("TEST", isa="EXE.CAPABILITY-STATEMENT")
        varmap = graph.register("VARMAP")

        cap["CAPABILITY"] = "EXE.TEST-CAPABILITY"
        cap["PARAMS"] = [1, 2, Literal("$var")]
        cap["X"] = 4

        varmap = VariableMap(varmap)
        Variable.instance(graph, "$var", 3, varmap)

        Statement.from_instance(cap).run(StatementScope(), varmap)

        self.assertEqual(result, 10)

    def test_run_with_callbacks(self):

        class TestMP(AgentMethod):
            def run(self):
                pass

        from backend.models.mps import MPRegistry
        MPRegistry.register(TestMP)

        network = Network()
        graph = network.register(Statement.hierarchy())
        graph.register("CAPABILITY")
        graph.register("CALLBACK")

        c = Capability.instance(graph, "TEST-CAPABILITY", TestMP)

        cap = graph.register("TEST-W-CALLBACKS", isa="EXE.CAPABILITY-STATEMENT")
        cap["CAPABILITY"] = "EXE.TEST-CAPABILITY"

        stmt1 = graph.register("STMT1", isa="EXE.MP-STATEMENT")
        stmt2 = graph.register("STMT1", isa="EXE.MP-STATEMENT")
        cap["CALLBACK"] = [stmt1, stmt2]

        varmap = graph.register("MY-VARMAP-TEST")
        varmap = VariableMap(varmap)
        Statement.from_instance(cap).run(StatementScope(), varmap)

        callback = graph.search(Frame.q(network).f("VARMAP", varmap.frame))[0]
        self.assertTrue(callback["CAPABILITY"] == c.frame)
        self.assertTrue(callback["STATEMENT"] == [stmt1, stmt2])


class OutputXMRStatementTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register(Statement.hierarchy())

    def test_template(self):
        from backend.models.output import OutputXMRTemplate
        from backend.models.statement import OutputXMRStatement

        template = OutputXMRTemplate.build(self.n, "test-template", OutputXMRTemplate.Type.PHYSICAL, "EXE.CAPABILITY", [])

        frame = self.g.register("TEST", isa="EXE.OUTPUTXMR-STATEMENT")
        frame["TEMPLATE"] = Literal("test-template")

        stmt: OutputXMRStatement = Statement.from_instance(frame)
        self.assertEqual(template, stmt.template())

    def test_params(self):
        from backend.models.statement import OutputXMRStatement

        frame = self.g.register("TEST", isa="EXE.OUTPUTXMR-STATEMENT")
        frame["PARAMS"] = [1, 2, Literal("$var1"), Literal("$var2")]

        stmt: OutputXMRStatement = Statement.from_instance(frame)
        self.assertEqual([1, 2, "$var1", "$var2"], stmt.params())

    def test_agent(self):
        from backend.models.statement import OutputXMRStatement

        agent = self.g.register("AGENT")

        frame = self.g.register("TEST", isa="EXE.OUTPUTXMR-STATEMENT")
        frame["AGENT"] = agent

        stmt: OutputXMRStatement = Statement.from_instance(frame)
        self.assertEqual(agent, stmt.agent())

    def test_instance(self):
        from backend.models.output import OutputXMRTemplate
        from backend.models.statement import OutputXMRStatement

        template = OutputXMRTemplate.build(self.n, "test-template", OutputXMRTemplate.Type.PHYSICAL, "EXE.CAPABILITY", [])
        params = [1, 2, Literal("$var1"), Literal("$var2")]
        agent = self.g.register("AGENT")

        stmt = OutputXMRStatement.instance(self.g, template, params, agent)

        self.assertEqual(template, stmt.template())
        self.assertEqual(params, stmt.params())
        self.assertEqual(agent, stmt.agent())

    def test_run(self):
        from backend.models.output import OutputXMR, OutputXMRTemplate
        from backend.models.statement import OutputXMRStatement

        self.g.register("CAPABILITY")

        template = OutputXMRTemplate.build(self.n, "test-template", OutputXMRTemplate.Type.PHYSICAL, "EXE.CAPABILITY", [])
        agent = self.g.register("AGENT")

        stmt = OutputXMRStatement.instance(self.g, template, [], agent)

        self.assertNotIn("XMR#1", self.n)

        varmap = self.g.register("MY-VARMAP-TEST")
        varmap = VariableMap(varmap)
        output = stmt.run(StatementScope(), varmap)

        self.assertIn("XMR#1", self.n)
        self.assertIsInstance(output, OutputXMR)
        self.assertIn(output.frame.name(), agent._graph)

    def test_run_affects_scope(self):
        from backend.models.output import OutputXMR, OutputXMRTemplate
        from backend.models.statement import OutputXMRStatement

        self.g.register("CAPABILITY")

        template = OutputXMRTemplate.build(self.n, "test-template", OutputXMRTemplate.Type.PHYSICAL, "EXE.CAPABILITY",
                                           [])
        agent = self.g.register("AGENT")
        test1 = self.g.register("TEST1")
        test2 = self.g.register("TEST2")

        stmt = OutputXMRStatement.instance(self.g, template, [], agent)

        self.assertNotIn("XMR#1", self.n)

        varmap = self.g.register("MY-VARMAP-TEST")
        varmap = VariableMap(varmap)
        scope = StatementScope()
        output = stmt.run(scope, varmap)

        self.assertIn(output.frame, scope.outputs)

    def test_run_with_variables(self):
        from backend.models.output import OutputXMR, OutputXMRTemplate
        from backend.models.statement import OutputXMRStatement

        self.g.register("CAPABILITY")

        template = OutputXMRTemplate.build(self.n, "test-template", OutputXMRTemplate.Type.PHYSICAL, "EXE.CAPABILITY", ["$var1", "$var2"])
        f = template.graph.register("FRAME", generate_index=True)
        f["PROP1"] = Literal("$var1")
        f["PROP2"] = Literal("$var1")
        f["PROP3"] = Literal("$var2")

        agent = self.g.register("AGENT")
        stmt = OutputXMRStatement.instance(self.g, template, [123, "$myvar"], agent)

        varmap = self.g.register("MY-VARMAP-TEST")
        varmap = VariableMap(varmap)
        Variable.instance(self.g, "$myvar", Literal("abc"), varmap)

        output = stmt.run(StatementScope(), varmap)

        fi = output.graph(self.n)["FRAME.1"]
        self.assertEqual(123, fi["PROP1"])
        self.assertEqual(123, fi["PROP2"])
        self.assertEqual("abc", fi["PROP3"])