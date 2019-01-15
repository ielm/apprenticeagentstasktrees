from backend.models.bootstrap import Bootstrap
from backend.models.graph import Frame, Graph, Identifier, Literal, Network
from backend.models.mps import AgentMethod, MPRegistry
from backend.models.query import Query
from backend.models.statement import TransientFrame, Statement, StatementScope, Variable, VariableMap

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


class TransientFrameTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")

    def test_is_in_scope(self):
        f = TransientFrame(self.g.register("FRAME"))

        self.assertTrue(f.is_in_scope())

        f.update_scope(lambda: False)

        self.assertFalse(f.is_in_scope())


class StatementTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

    def test_run(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope, varmap: VariableMap):
                return varmap.resolve("X")

        stmt = self.g.register("STATEMENT")
        varmap = self.g.register("VARMAP")
        varmap["WITH"] = Literal("X")

        vm = VariableMap.instance_of(self.g, varmap, [123])
        statement = TestStatement(stmt)

        self.assertEqual(123, statement.run(StatementScope(), vm))

    def test_from_instance(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope, varmap: VariableMap):
                return 1

        self.g.register("TEST-STATEMENT", isa="EXE.STATEMENT")
        self.g["TEST-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)

        frame = self.g.register("TEST.1", isa="TEST-STATEMENT")
        stmt = Statement.from_instance(frame)

        self.assertIsInstance(stmt, TestStatement)


class AddFillerStatementTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

    def test_run(self):
        addfiller = self.g.register("TEST", isa="EXE.ADDFILLER-STATEMENT")
        target = self.g.register("TARGET")

        addfiller["TO"] = target
        addfiller["SLOT"] = Literal("X")
        addfiller["ADD"] = 123

        Statement.from_instance(addfiller).run(StatementScope(), None)
        self.assertTrue(target["X"] == 123)

        Statement.from_instance(addfiller).run(StatementScope(), None)
        self.assertTrue(target["X"] == [123, 123])

    def test_run_variable_to(self):
        addfiller = self.g.register("TEST", isa="EXE.ADDFILLER-STATEMENT")
        target = self.g.register("TARGET")
        varmap = self.g.register("VARMAP")

        addfiller["TO"] = Literal("$VAR")
        addfiller["SLOT"] = Literal("X")
        addfiller["ADD"] = 123

        varmap = VariableMap(varmap)
        Variable.instance(self.g, "$VAR", target, varmap)

        Statement.from_instance(addfiller).run(StatementScope(), varmap)
        self.assertTrue(target["X"] == 123)

    def test_run_variable_value(self):
        addfiller = self.g.register("TEST", isa="EXE.ADDFILLER-STATEMENT")
        target = self.g.register("TARGET")
        varmap = self.g.register("VARMAP")
        Variable.instance(self.g, "MYVAR", 123, VariableMap(varmap))

        addfiller["TO"] = target
        addfiller["SLOT"] = Literal("X")
        addfiller["ADD"] = Literal("MYVAR")

        Statement.from_instance(addfiller).run(StatementScope(), VariableMap(varmap))
        self.assertTrue(target["X"] == 123)

    def test_run_returning_statement_results(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope(), varmap: VariableMap):
                return 123

        addfiller = self.g.register("TEST", isa="EXE.ADDFILLER-STATEMENT")
        target = self.g.register("TARGET")
        stmt = self.g.register("TEST-STMT", isa="EXE.RETURNING-STATEMENT")

        self.g["RETURNING-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)

        addfiller["TO"] = target
        addfiller["SLOT"] = Literal("X")
        addfiller["ADD"] = stmt

        Statement.from_instance(addfiller).run(StatementScope(), None)
        self.assertTrue(target["X"] == 123)


class AssertStatementTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

    def test_assertion(self):
        from backend.models.statement import AssertStatement, ExistsStatement

        assertion = ExistsStatement.instance(self.g, Frame.q(self.n).has("TEST"))

        stmt = self.g.register("ASSERT-STATEMENT", generate_index=True)
        stmt["ASSERTION"] = assertion.frame

        self.assertEqual(assertion, AssertStatement(stmt).assertion())

    def test_resolutions(self):
        from backend.models.statement import AssertStatement, MakeInstanceStatement

        mi1 = MakeInstanceStatement.instance(self.g, self.g._namespace, "EXE.TEST-GOAL-A", [])
        mi2 = MakeInstanceStatement.instance(self.g, self.g._namespace, "EXE.TEST-GOAL-B", [])

        stmt = self.g.register("ASSERT-STATEMENT", generate_index=True)
        stmt["RESOLUTION"] = [mi1.frame, mi2.frame]

        self.assertEqual([mi1, mi2], AssertStatement(stmt).resolutions())

    def test_instance(self):
        from backend.models.statement import AssertStatement, ExistsStatement, MakeInstanceStatement

        assertion = ExistsStatement.instance(self.g, Frame.q(self.n).has("TEST"))
        mi1 = MakeInstanceStatement.instance(self.g, self.g._namespace, "EXE.TEST-GOAL-A", [])
        mi2 = MakeInstanceStatement.instance(self.g, self.g._namespace, "EXE.TEST-GOAL-B", [])

        stmt = AssertStatement.instance(self.g, assertion, [mi1, mi2])
        self.assertEqual(assertion, stmt.assertion())
        self.assertEqual([mi1, mi2], stmt.resolutions())

    def test_from_instance(self):
        from backend.models.statement import AssertStatement

        stmt = self.g.register("TEST", isa="EXE.ASSERT-STATEMENT")
        stmt = Statement.from_instance(stmt)
        self.assertIsInstance(stmt, AssertStatement)

    def test_run_query_passes(self):
        from backend.models.statement import AssertStatement, ExistsStatement

        target = self.g.register("TARGET")
        target["TEST"] = 123

        assertion = ExistsStatement.instance(self.g, Frame.q(self.n).has("TEST"))
        stmt = AssertStatement.instance(self.g, assertion, [])

        stmt.run(StatementScope(), VariableMap(self.g.register("VARMAP")))

    def test_run_query_fails(self):
        from backend.models.statement import AssertStatement, ExistsStatement, MakeInstanceStatement

        self.g.register("TARGET")

        assertion = ExistsStatement.instance(self.g, Frame.q(self.n).has("TEST"))
        mi = MakeInstanceStatement.instance(self.g, self.g._namespace, "EXE.TEST-GOAL", [])
        stmt = AssertStatement.instance(self.g, assertion, [mi])

        try:
            stmt.run(StatementScope(), VariableMap(self.g.register("VARMAP")))
            self.fail()
        except AssertStatement.ImpasseException as e:
            self.assertEqual([mi], e.resolutions)


class AssignFillerStatementTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

    def test_run(self):
        assignfiller = self.g.register("TEST", isa="EXE.ASSIGNFILLER-STATEMENT")
        target = self.g.register("TARGET")

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
        assignfiller = self.g.register("TEST", isa="EXE.ASSIGNFILLER-STATEMENT")
        target = self.g.register("TARGET")
        varmap = self.g.register("VARMAP")

        assignfiller["TO"] = Literal("$VAR")
        assignfiller["SLOT"] = Literal("X")
        assignfiller["ASSIGN"] = 123

        varmap = VariableMap(varmap)
        Variable.instance(self.g, "$VAR", target, varmap)

        Statement.from_instance(assignfiller).run(StatementScope(), varmap)
        self.assertTrue(target["X"] == 123)

    def test_run_variable_value(self):
        assignfiller = self.g.register("TEST", isa="EXE.ASSIGNFILLER-STATEMENT")
        target = self.g.register("TARGET")
        varmap = self.g.register("VARMAP")
        Variable.instance(self.g, "MYVAR", 123, VariableMap(varmap))

        assignfiller["TO"] = target
        assignfiller["SLOT"] = Literal("X")
        assignfiller["ASSIGN"] = Literal("MYVAR")

        Statement.from_instance(assignfiller).run(StatementScope(), VariableMap(varmap))
        self.assertTrue(target["X"] == 123)

    def test_run_returning_statement_results(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope(), varmap: VariableMap):
                return 123

        assignfiller = self.g.register("TEST", isa="EXE.ASSIGNFILLER-STATEMENT")
        target = self.g.register("TARGET")
        stmt = self.g.register("TEST-STMT", isa="EXE.RETURNING-STATEMENT")

        self.g["RETURNING-STATEMENT"]["CLASSMAP"] = Literal(TestStatement)

        assignfiller["TO"] = target
        assignfiller["SLOT"] = Literal("X")
        assignfiller["ASSIGN"] = stmt

        Statement.from_instance(assignfiller).run(StatementScope(), None)
        self.assertTrue(target["X"] == 123)


class AssignVariableStatementTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

    def test_run_assign_literal(self):
        assignvariable = self.g.register("TEST", isa="EXE.ASSIGNVARIABLE-STATEMENT")
        assignvariable["TO"] = Literal("$var1")
        assignvariable["ASSIGN"] = 123

        varmap = VariableMap(self.g.register("VARMAP"))
        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(123, varmap.resolve("$var1"))

    def test_run_assign_frame(self):
        target = self.g.register("TARGET")

        assignvariable = self.g.register("TEST", isa="EXE.ASSIGNVARIABLE-STATEMENT")
        assignvariable["TO"] = Literal("$var1")
        assignvariable["ASSIGN"] = target

        varmap = VariableMap(self.g.register("VARMAP"))
        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(target, varmap.resolve("$var1"))

    def test_run_assign_variable(self):
        assignvariable = self.g.register("TEST", isa="EXE.ASSIGNVARIABLE-STATEMENT")
        assignvariable["TO"] = Literal("$var1")
        assignvariable["ASSIGN"] = Literal("$existing")

        varmap = VariableMap(self.g.register("VARMAP"))
        Variable.instance(self.g, "$existing", 123, varmap)

        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(123, varmap.resolve("$var1"))

    def test_run_assign_statement_results(self):
        from backend.models.statement import ExistsStatement, MakeInstanceStatement, MeaningProcedureStatement

        class TestMP(AgentMethod):
            def run(self, *args, **kwargs):
                return 123
        MPRegistry.register(TestMP)

        assignvariable = self.g.register("TEST", isa="EXE.ASSIGNVARIABLE-STATEMENT")
        varmap = VariableMap(self.g.register("VARMAP"))

        assignvariable["TO"] = Literal("$var1")
        assignvariable["ASSIGN"] = MeaningProcedureStatement.instance(self.g, "TestMP", [])
        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(123, varmap.resolve("$var1"))

        assignvariable["TO"] = Literal("$var2")
        assignvariable["ASSIGN"] = ExistsStatement.instance(self.g, Frame.q(self.n).id("EXE.TEST"))
        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(True, varmap.resolve("$var2"))

        assignvariable["TO"] = Literal("$var3")
        assignvariable["ASSIGN"] = MakeInstanceStatement.instance(self.g, self.g._namespace, "EXE.TEST", [])
        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(self.g["TEST.1"], varmap.resolve("$var3"))


class ExistsStatementTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

    def test_run(self):
        stmt = self.g.register("TEST", isa="EXE.EXISTS-STATEMENT")

        stmt["FIND"] = Query.parse(self.g._network, "WHERE @ ^ @EXE.EXISTS-STATEMENT")
        self.assertTrue(Statement.from_instance(stmt).run(StatementScope(), None))

        stmt["FIND"] = Query.parse(self.g._network, "WHERE abc=123")
        self.assertFalse(Statement.from_instance(stmt).run(StatementScope(), None))


class ExpectationStatementTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

    def test_condition(self):
        from backend.models.statement import ExistsStatement, ExpectationStatement

        stmt = self.g.register("STATEMENT")
        stmt["CONDITION"] = ExistsStatement.instance(self.g, Frame.q(self.n).id("TEST.FRAME.1")).frame

        self.assertEqual(ExistsStatement.instance(self.g, Frame.q(self.n).id("TEST.FRAME.1")), ExpectationStatement(stmt).condition())

    def test_instance(self):
        from backend.models.statement import ExistsStatement, ExpectationStatement

        stmt = ExpectationStatement.instance(self.g, ExistsStatement.instance(self.g, Frame.q(self.n).id("TEST.FRAME.1")))

        self.assertEqual(ExistsStatement.instance(self.g, Frame.q(self.n).id("TEST.FRAME.1")), stmt.condition())

    def test_from_instance(self):
        from backend.models.statement import ExpectationStatement

        stmt = self.g.register("TEST", isa="EXE.EXPECTATION-STATEMENT")
        stmt = Statement.from_instance(stmt)

        self.assertIsInstance(stmt, ExpectationStatement)

    def test_run(self):
        from backend.models.statement import ExistsStatement, ExpectationStatement

        condition = ExistsStatement.instance(self.g, Frame.q(self.n).id("TEST.FRAME.1"))
        stmt = ExpectationStatement.instance(self.g, condition)

        scope = StatementScope()
        self.assertEqual([], scope.expectations)

        stmt.run(scope, None)
        self.assertEqual([condition], scope.expectations)

        stmt.run(scope, None)
        self.assertEqual([condition, condition], scope.expectations)


class ForEachStatementTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

    def test_run(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope(), varmap: VariableMap):
                frame = varmap.resolve("$FOR")
                frame["c"] = frame["a"][0].resolve().value + frame["b"][0].resolve().value

        foreach = self.g.register("TEST", isa="EXE.FOREACH-STATEMENT")
        stmt = self.g.register("TEST", isa="EXE.STATEMENT")
        varmap = self.g.register("VARMAP")

        target1 = self.g.register("TARGET", generate_index=True)
        target2 = self.g.register("TARGET", generate_index=True)

        target1["a"] = 1
        target2["a"] = 1
        target1["b"] = 2
        target2["b"] = 3

        self.g["STATEMENT"]["CLASSMAP"] = Literal(TestStatement)

        foreach["FROM"] = Query.parse(self.g._network, "WHERE a = 1")
        foreach["ASSIGN"] = Literal("$FOR")
        foreach["DO"] = stmt

        Statement.from_instance(foreach).run(StatementScope(), VariableMap(varmap))

        self.assertTrue(target1["c"] == 3)
        self.assertTrue(target2["c"] == 4)


class IsStatementTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

    def test_run(self):
        stmt = self.g.register("TEST", isa="EXE.IS-STATEMENT")
        target = self.g.register("TARGET")

        stmt["DOMAIN"] = target
        stmt["SLOT"] = Literal("X")
        stmt["FILLER"] = 123

        stmt = Statement.from_instance(stmt)

        self.assertFalse(stmt.run(StatementScope(), None))

        target["X"] = 123
        self.assertTrue(stmt.run(StatementScope(), None))

    def test_variable_domain(self):
        stmt = self.g.register("TEST", isa="EXE.IS-STATEMENT")
        target = self.g.register("TARGET")
        varmap = self.g.register("VARMAP")

        stmt["DOMAIN"] = Literal("$VAR")
        stmt["SLOT"] = Literal("X")
        stmt["FILLER"] = 123

        varmap = VariableMap(varmap)
        Variable.instance(self.g, "$VAR", target, varmap)

        stmt = Statement.from_instance(stmt)

        self.assertFalse(stmt.run(StatementScope(), varmap))

        target["X"] = 123
        self.assertTrue(stmt.run(StatementScope(), varmap))

    def test_variable_filler(self):
        stmt = self.g.register("TEST", isa="EXE.IS-STATEMENT")
        target = self.g.register("TARGET")
        varmap = self.g.register("VARMAP")

        stmt["DOMAIN"] = target
        stmt["SLOT"] = Literal("X")
        stmt["FILLER"] = Literal("$VAR")

        varmap = VariableMap(varmap)
        Variable.instance(self.g, "$VAR", 123, varmap)

        stmt = Statement.from_instance(stmt)

        self.assertFalse(stmt.run(StatementScope(), varmap))

        target["X"] = 123
        self.assertTrue(stmt.run(StatementScope(), varmap))


class MakeInstanceStatementTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

    def test_run(self):
        makeinstance = self.g.register("TEST", isa="EXE.MAKEINSTANCE-STATEMENT")
        target = self.g.register("TARGET")

        makeinstance["IN"] = Literal("EXE")
        makeinstance["OF"] = target
        makeinstance["PARAMS"] = [1, 2, 3]

        target["WITH"] = [Literal("$A"), Literal("$B"), Literal("$C")]

        instance = Statement.from_instance(makeinstance).run(StatementScope(), None)
        self.assertTrue(instance.name() in self.g)
        self.assertEqual(VariableMap(instance).resolve("$A"), 1)
        self.assertEqual(VariableMap(instance).resolve("$B"), 2)
        self.assertEqual(VariableMap(instance).resolve("$C"), 3)

        other = self.n.register("OTHER")
        makeinstance["IN"] = Literal("OTHER")
        instance = Statement.from_instance(makeinstance).run(StatementScope(), None)
        self.assertTrue(instance.name() in other)

    def test_raises_exception_on_mismatched_params(self):
        makeinstance = self.g.register("TEST", isa="EXE.MAKEINSTANCE-STATEMENT")
        target = self.g.register("TARGET")

        makeinstance["OF"] = target
        makeinstance["PARAMS"] = [1, 2, 3]

        with self.assertRaises(Exception):
            Statement.from_instance(makeinstance).run(StatementScope(), None)


class MeaningProcedureStatementTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

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

        mp = self.g.register("TEST", isa="EXE.MP-STATEMENT")

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

        mp = self.g.register("TEST", isa="EXE.MP-STATEMENT")
        varmap = self.g.register("VARMAP")

        mp["CALLS"] = Literal(TestMP.__name__)
        mp["PARAMS"] = [1, 2, Literal("$var")]
        mp["X"] = 4

        varmap = VariableMap(varmap)
        Variable.instance(self.g, "$var", 3, varmap)

        Statement.from_instance(mp).run(StatementScope(), varmap)

        self.assertEqual(result, 10)


class OutputXMRStatementTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")
        self.n.register("OUTPUTS")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

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
        self.assertIn(output.frame.name(), self.n["OUTPUTS"])

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


class TransientFrameStatementTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()
        self.g = self.n.register("EXE")
        Bootstrap.bootstrap_resource(self.n, "backend.resources", "exe.knowledge")

    def test_properties(self):
        from backend.models.bootstrap import BootstrapTriple
        from backend.models.statement import TransientFrameStatement

        triple1 = BootstrapTriple("TEST", Literal(123))
        triple2 = BootstrapTriple("TEST", Literal(456))
        triple3 = BootstrapTriple("XYZ", Identifier.parse("TEST.FRAME.1"))

        statement = self.g.register("STATEMENT")
        statement["HAS-PROPERTY"] += triple1
        statement["HAS-PROPERTY"] += triple2
        statement["HAS-PROPERTY"] += triple3

        self.assertEqual([triple1, triple2, triple3], TransientFrameStatement(statement).properties())

    def test_instance(self):
        from backend.models.bootstrap import BootstrapTriple
        from backend.models.statement import TransientFrameStatement

        triple1 = BootstrapTriple("TEST", Literal(123))
        triple2 = BootstrapTriple("TEST", Literal(456))
        triple3 = BootstrapTriple("XYZ", Identifier.parse("TEST.FRAME.1"))

        statement = TransientFrameStatement.instance(self.g, [triple1, triple2, triple3])

        self.assertEqual([triple1, triple2, triple3], statement.properties())

    def test_from_instance(self):
        from backend.models.statement import TransientFrameStatement

        frame = self.g.register("STATEMENT", isa="EXE.TRANSIENTFRAME-STATEMENT")
        statement = Statement.from_instance(frame)

        self.assertIsInstance(statement, TransientFrameStatement)

    def test_run(self):
        from backend.models.bootstrap import BootstrapTriple
        from backend.models.statement import TransientFrameStatement

        triple1 = BootstrapTriple("TEST", Literal(123))
        triple2 = BootstrapTriple("TEST", Literal(456))
        triple3 = BootstrapTriple("XYZ", Identifier.parse("TEST.FRAME.1"))
        triple4 = BootstrapTriple("ABC", Literal("$var1"))
        triple5 = BootstrapTriple("DEF", Literal("test"))

        statement = TransientFrameStatement.instance(self.g, [triple1, triple2, triple3, triple4, triple5])

        varmap = VariableMap(self.g.register("VARMAP"))
        Variable.instance(self.g, "$var1", 789, varmap)

        scope = StatementScope()
        frame = statement.run(scope, varmap)

        self.assertEqual("EXE.TRANSIENT-FRAME.1", frame.name())
        self.assertEqual(self.g, frame._graph)
        self.assertIn(frame.name(), self.g)
        self.assertEqual([123, 456], frame["TEST"])
        self.assertEqual("TEST.FRAME.1", frame["XYZ"])
        self.assertEqual(789, frame["ABC"])
        self.assertEqual("test", frame["DEF"])
        self.assertIn(frame, scope.transients)