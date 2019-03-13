from backend.models.bootstrap import Bootstrap
# from backend.models.graph import Frame, Graph, Identifier, Literal, Network
from backend.models.mps import AgentMethod, MPRegistry
from backend.models.query import Query
from backend.models.statement import TransientFrame, Statement, StatementScope, Variable, VariableMap
from backend.models.xmr import XMR
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Index import Identifier
from ontograph.Query import ExistsComparator, IdComparator, IsAComparator, Query
from ontograph.Space import Space

import unittest


class VariableTestCase(unittest.TestCase):

    def test_name(self):
        f = Frame("TEST.1")
        f["NAME"] = "VAR_X"

        var = Variable(f)
        self.assertEqual(var.name(), "VAR_X")

    def test_varmap(self):
        vm = Frame("@TEST.VARMAP.1")
        v = Frame("@TEST.FRAME.1")
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

    def setUp(self):
        graph.reset()

    def test_instance_of(self):
        f = Frame("@TEST.VARMAPDEF.1")
        f["WITH"] = ["VAR_X", "VAR_Y"]

        params = [1, 2]

        vm = VariableMap.instance_of(Space("TEST"), f, params)
        self.assertTrue(vm.frame["WITH"] == "VAR_X")
        self.assertTrue(vm.frame["WITH"] == "VAR_Y")
        self.assertTrue(vm.frame["_WITH"] == Identifier("@TEST.VARIABLE.1"))
        self.assertTrue(vm.frame["_WITH"] == Identifier("@TEST.VARIABLE.2"))

        self.assertIn("@TEST.VARIABLE.1", graph)
        self.assertIn("@TEST.VARIABLE.2", graph)

        self.assertEqual(Variable(Frame("@TEST.VARIABLE.1")).name(), "VAR_X")
        self.assertEqual(Variable(Frame("@TEST.VARIABLE.2")).name(), "VAR_Y")

        self.assertEqual(Variable(Frame("@TEST.VARIABLE.1")).varmap(), vm)
        self.assertEqual(Variable(Frame("@TEST.VARIABLE.2")).varmap(), vm)

        self.assertEqual(Variable(Frame("@TEST.VARIABLE.1")).value(), 1)
        self.assertEqual(Variable(Frame("@TEST.VARIABLE.2")).value(), 2)

    def test_instance_of_with_existing_frame(self):
        existing = Frame("@TEST.EXISTING.1")
        f = Frame("@TEST.VARMAPDEF.1")
        f["WITH"] = ["VAR_X", "VAR_Y"]

        params = [1, 2]

        vm = VariableMap.instance_of(Space("TEST"), f, params, existing=existing)
        self.assertEqual(vm.frame, existing)

        self.assertTrue(existing["WITH"] == "VAR_X")
        self.assertTrue(existing["WITH"] == "VAR_Y")
        self.assertTrue(existing["_WITH"] == Identifier("@TEST.VARIABLE.1"))
        self.assertTrue(existing["_WITH"] == Identifier("@TEST.VARIABLE.2"))

        self.assertIn("@TEST.VARIABLE.1", graph)
        self.assertIn("@TEST.VARIABLE.2", graph)

        self.assertEqual(Variable(Frame("@TEST.VARIABLE.1")).name(), "VAR_X")
        self.assertEqual(Variable(Frame("@TEST.VARIABLE.2")).name(), "VAR_Y")

        self.assertEqual(Variable(Frame("@TEST.VARIABLE.1")).varmap(), vm)
        self.assertEqual(Variable(Frame("@TEST.VARIABLE.2")).varmap(), vm)

        self.assertEqual(Variable(Frame("@TEST.VARIABLE.1")).value(), 1)
        self.assertEqual(Variable(Frame("@TEST.VARIABLE.2")).value(), 2)

    def test_assign(self):
        f = Frame("@TEST.VARMAP.1")
        v1 = Frame("@TEST.VARIABLE.1")
        v2 = Frame("@TEST.VARIABLE.2")
        v3 = Frame("@TEST.VARIABLE.3")
        v4 = Frame("@TEST.VARIABLE.4")

        v1["NAME"] = "V1"
        v2["NAME"] = "V2"
        v3["NAME"] = "V3"
        v4["NAME"] = "V4"

        vm = VariableMap(f)
        vm.assign("VAR1", Variable(v1))
        vm.assign("VAR2", v2)
        vm.assign("VAR3", Identifier(v3.id))
        vm.assign("VAR3", "@TEST.VARIABLE.4")

        self.assertEqual(f["_WITH"], v1)
        self.assertEqual(f["_WITH"], v2)
        self.assertEqual(f["_WITH"], v3)
        self.assertEqual(f["_WITH"], v4)

    def test_resolve(self):
        f = Frame("@TEST.VARMAP.1")
        v1 = Frame("@TEST.VARIABLE.1")
        v2 = Frame("@TEST.VARIABLE.2")

        v1["NAME"] = "X"
        v1["VALUE"] = 1

        v2["NAME"] = "Y"
        v2["VALUE"] = 2

        f["_WITH"] = [v1, v2]

        vm = VariableMap(f)
        self.assertEqual(vm.resolve("X"), 1)
        self.assertEqual(vm.resolve("Y"), 2)

    def test_find(self):
        f = Frame("@TEST.VARMAP.1")
        v1 = Frame("@TEST.VARIABLE.1")
        v2 = Frame("@TEST.VARIABLE.2")

        v1["NAME"] = "X"
        v2["NAME"] = "Y"

        v1["VALUE"] = 1
        v2["VALUE"] = 1

        f["_WITH"] = [v1, v2]
        vm = VariableMap(f)
        self.assertEqual(vm.find("X"), v1)
        self.assertEqual(vm.find("Y"), v2)

    def test_variables(self):
        f = Frame("@TEST.VARMAP")
        f["WITH"] += "$var1"
        f["WITH"] += "$var2"

        self.assertEqual(["$var1", "$var2"], VariableMap(f).variables())


class TransientFrameTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

    def test_is_in_scope(self):
        f = TransientFrame(Frame("@TEST.FRAME"))

        self.assertTrue(f.is_in_scope())

        f.update_scope(lambda: False)

        self.assertFalse(f.is_in_scope())


class StatementTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()

        Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")

    def test_run(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope, varmap: VariableMap):
                return varmap.resolve("X")

        stmt = Frame("@TEST.STATEMENT")
        varmap = Frame("@TEST.VARMAP")
        varmap["WITH"] = "X"

        vm = VariableMap.instance_of(Space("TEST"), varmap, [123])
        statement = TestStatement(stmt)

        self.assertEqual(123, statement.run(StatementScope(), vm))

    def test_from_instance(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope, varmap: VariableMap):
                return 1

        Frame("@TEST.TEST-STATEMENT").add_parent("@EXE.STATEMENT")
        Frame("@TEST.TEST-STATEMENT")["CLASSMAP"] = TestStatement

        frame = Frame("@TEST.TEST.1").add_parent("@TEST-STATEMENT")
        stmt = Statement.from_instance(frame)

        self.assertIsInstance(stmt, TestStatement)


class AddFillerStatementTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")

    def test_run(self):
        addfiller = Frame("@TEST.FRAME").add_parent("@EXE.ADDFILLER-STATEMENT")
        target = Frame("@TEST.TARGET")

        addfiller["TO"] = target
        addfiller["SLOT"] = "X"
        addfiller["ADD"] = 123

        Statement.from_instance(addfiller).run(StatementScope(), None)
        self.assertTrue(target["X"] == 123)

        Statement.from_instance(addfiller).run(StatementScope(), None)
        self.assertTrue(target["X"] == [123, 123])

    def test_run_variable_to(self):
        addfiller = Frame("@TEST.FRAME").add_parent("@EXE.ADDFILLER-STATEMENT")
        target = Frame("@TEST.TARGET")
        varmap = Frame("@TEST.VARMAP")

        addfiller["TO"] = "$VAR"
        addfiller["SLOT"] = "X"
        addfiller["ADD"] = 123

        varmap = VariableMap(varmap)
        Variable.instance(Space("TEST"), "$VAR", target, varmap)

        Statement.from_instance(addfiller).run(StatementScope(), varmap)
        self.assertTrue(target["X"] == 123)

    def test_run_variable_value(self):
        addfiller = Frame("@TEST.FRAME").add_parent("@EXE.ADDFILLER-STATEMENT")
        target = Frame("@TEST.TARGET")
        varmap = Frame("@TEST.VARMAP")
        Variable.instance(Space("TEST"), "MYVAR", 123, VariableMap(varmap))

        addfiller["TO"] = target
        addfiller["SLOT"] = "X"
        addfiller["ADD"] = "MYVAR"

        Statement.from_instance(addfiller).run(StatementScope(), VariableMap(varmap))
        self.assertTrue(target["X"] == 123)

    def test_run_returning_statement_results(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope(), varmap: VariableMap):
                return 123

        addfiller = Frame("@TEST.FRAME").add_parent("@EXE.ADDFILLER-STATEMENT")
        target = Frame("@TEST.TARGET")
        stmt = Frame("@TEST.TEST-STMT").add_parent("@EXE.RETURNING-STATEMENT")

        Frame("@RETURNING-STATEMENT")["CLASSMAP"] = TestStatement

        addfiller["TO"] = target
        addfiller["SLOT"] = "X"
        addfiller["ADD"] = stmt

        Statement.from_instance(addfiller).run(StatementScope(), None)
        self.assertTrue(target["X"] == 123)


class AssertStatementTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")

    def test_assertion(self):
        from backend.models.statement import AssertStatement, ExistsStatement

        assertion = ExistsStatement.instance(Space("TEST"), Query().search(ExistsComparator(slot="TEST")))

        stmt = Frame("@TEST.ASSERT-STATEMENT.?")
        stmt["ASSERTION"] = assertion.frame

        self.assertEqual(assertion, AssertStatement(stmt).assertion())

    def test_resolutions(self):
        from backend.models.statement import AssertStatement, MakeInstanceStatement

        mi1 = MakeInstanceStatement.instance(Space("TEST"), "TEST", "@EXE.TEST-GOAL-A", [])
        mi2 = MakeInstanceStatement.instance(Space("TEST"), "TEST", "@EXE.TEST-GOAL-B", [])

        stmt = Frame("@TEST.ASSERT-STATEMENT.?")
        stmt["RESOLUTION"] = [mi1.frame, mi2.frame]

        self.assertEqual([mi1, mi2], AssertStatement(stmt).resolutions())

    def test_instance(self):
        from backend.models.statement import AssertStatement, ExistsStatement, MakeInstanceStatement

        assertion = ExistsStatement.instance(Space("TEST"), Query().search(ExistsComparator(slot="TEST")))
        mi1 = MakeInstanceStatement.instance(Space("TEST"), "TEST", "EXE.TEST-GOAL-A", [])
        mi2 = MakeInstanceStatement.instance(Space("TEST"), "TEST", "EXE.TEST-GOAL-B", [])

        stmt = AssertStatement.instance(Space("TEST"), assertion, [mi1, mi2])
        self.assertEqual(assertion, stmt.assertion())
        self.assertEqual([mi1, mi2], stmt.resolutions())

    def test_from_instance(self):
        from backend.models.statement import AssertStatement

        stmt = Frame("@TEST.STMT").add_parent("@EXE.ASSERT-STATEMENT")
        stmt = Statement.from_instance(stmt)
        self.assertIsInstance(stmt, AssertStatement)

    def test_run_query_passes(self):
        from backend.models.statement import AssertStatement, ExistsStatement

        target = Frame("@TEST.TARGET")
        target["TEST"] = 123

        assertion = ExistsStatement.instance(Space("TEST"), Query().search(ExistsComparator(slot="TEST")))
        stmt = AssertStatement.instance(Space("TEST"), assertion, [])

        stmt.run(StatementScope(), VariableMap(Frame("@TEST.VARMAP")))

    def test_run_query_fails(self):
        from backend.models.statement import AssertStatement, ExistsStatement, MakeInstanceStatement

        Frame("@TEST.TARGET")

        assertion = ExistsStatement.instance(Space("TEST"), Query().search(ExistsComparator(slot="TEST")))
        mi = MakeInstanceStatement.instance(Space("TEST"), "TEST", "@EXE.TEST-GOAL", [])
        stmt = AssertStatement.instance(Space("TEST"), assertion, [mi])

        try:
            stmt.run(StatementScope(), VariableMap(Frame("@TEST.VARMAP")))
            self.fail()
        except AssertStatement.ImpasseException as e:
            self.assertEqual([mi], e.resolutions)


class AssignFillerStatementTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")

    def test_run(self):
        assignfiller = Frame("@TEST.FRAME").add_parent("@EXE.ASSIGNFILLER-STATEMENT")
        target = Frame("@TEST.TARGET")

        assignfiller["TO"] = target
        assignfiller["SLOT"] = "X"
        assignfiller["ASSIGN"] = 123

        Statement.from_instance(assignfiller).run(StatementScope(), None)
        self.assertTrue(target["X"] == 123)

        assignfiller["ASSIGN"] = 345
        Statement.from_instance(assignfiller).run(StatementScope(), None)
        self.assertTrue(target["X"] == 345)
        self.assertTrue(target["X"] != 123)

    def test_run_variable_to(self):
        assignfiller = Frame("@TEST.FRAME").add_parent("@EXE.ASSIGNFILLER-STATEMENT")
        target = Frame("@TEST.TARGET")
        varmap = Frame("@TEST.VARMAP")

        assignfiller["TO"] = "$VAR"
        assignfiller["SLOT"] = "X"
        assignfiller["ASSIGN"] = 123

        varmap = VariableMap(varmap)
        Variable.instance(Space("TEST"), "$VAR", target, varmap)

        Statement.from_instance(assignfiller).run(StatementScope(), varmap)
        self.assertTrue(target["X"] == 123)

    def test_run_variable_value(self):
        assignfiller = Frame("@TEST.TARGET").add_parent("@EXE.ASSIGNFILLER-STATEMENT")
        target = Frame("@TEST.TARGET")
        varmap = Frame("@TEST.VARMAP")
        Variable.instance(Space("TEST"), "MYVAR", 123, VariableMap(varmap))

        assignfiller["TO"] = target
        assignfiller["SLOT"] = "X"
        assignfiller["ASSIGN"] = "MYVAR"

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
        graph.reset()
        Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")

    def test_run_assign_literal(self):
        assignvariable = Frame("@TEST.TARGET").add_parent("@EXE.ASSIGNVARIABLE-STATEMENT")
        assignvariable["TO"] = "$var1"
        assignvariable["ASSIGN"] = 123

        varmap = VariableMap(Frame("@TEST.VARMAP"))
        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(123, varmap.resolve("$var1"))

    def test_run_assign_frame(self):
        target = Frame("@TEST.TARGET")

        assignvariable = Frame("@TEST.FRAME").add_parent("@EXE.ASSIGNVARIABLE-STATEMENT")
        assignvariable["TO"] = "$var1"
        assignvariable["ASSIGN"] = target

        varmap = VariableMap(Frame("@TEST.VARMAP"))
        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(target, varmap.resolve("$var1"))

    def test_run_assign_variable(self):
        assignvariable = Frame("@TEST.FRAME").add_parent("@EXE.ASSIGNVARIABLE-STATEMENT")
        assignvariable["TO"] = "$var1"
        assignvariable["ASSIGN"] = "$existing"

        varmap = VariableMap(Frame("@TEST.VARMAP"))
        Variable.instance(Space("TEST"), "$existing", 123, varmap)

        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(123, varmap.resolve("$var1"))

    def test_run_assign_statement_results(self):
        from backend.models.statement import ExistsStatement, MakeInstanceStatement, MeaningProcedureStatement

        class TestMP(AgentMethod):
            def run(self, *args, **kwargs):
                return 123
        MPRegistry.register(TestMP)

        assignvariable = Frame("@TEST.FRAME").add_parent("@EXE.ASSIGNVARIABLE-STATEMENT")
        varmap = VariableMap(Frame("@TEST.VARMAP"))

        assignvariable["TO"] = "$var1"
        assignvariable["ASSIGN"] = MeaningProcedureStatement.instance(Space("TEST"), "TestMP", [])
        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(123, varmap.resolve("$var1"))

        assignvariable["TO"] = "$var2"
        assignvariable["ASSIGN"] = ExistsStatement.instance(Space("TEST"), Query().search(IdComparator("@TEST.FRAME")))
        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(True, varmap.resolve("$var2"))

        assignvariable["TO"] = "$var3"
        assignvariable["ASSIGN"] = MakeInstanceStatement.instance(Space("TEST"), "TEST", "@EXE.TEST", [])
        Statement.from_instance(assignvariable).run(StatementScope(), varmap)
        self.assertEqual(Frame("@TEST.TEST.1"), varmap.resolve("$var3"))


class ExistsStatementTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")

    def test_run(self):
        stmt = Frame("@TEST.FRAME").add_parent("@EXE.EXISTS-STATEMENT")

        stmt["FIND"] = Query().search(IsAComparator("@EXE.EXISTS-STATEMENT"))
        self.assertTrue(Statement.from_instance(stmt).run(StatementScope(), None))

        stmt["FIND"] = Query().search(ExistsComparator(slot="abc", filler=123))
        self.assertFalse(Statement.from_instance(stmt).run(StatementScope(), None))


class ExpectationStatementTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")

    def test_condition(self):
        from backend.models.statement import ExistsStatement, ExpectationStatement

        stmt = Frame("@TEST.STATEMENT")
        stmt["CONDITION"] = ExistsStatement.instance(Space("TEST"), Query().search(IdComparator("@TEST.FRAME.1"))).frame

        self.assertEqual(ExistsStatement.instance(Space("TEST"), Query().search(IdComparator("@TEST.FRAME.1"))), ExpectationStatement(stmt).condition())

    def test_instance(self):
        from backend.models.statement import ExistsStatement, ExpectationStatement

        stmt = ExpectationStatement.instance(Space("TEST"), ExistsStatement.instance(Space("TEST"), Query().search(IdComparator("@TEST.FRAME.1"))))

        self.assertEqual(ExistsStatement.instance(Space("TEST"), Query().search(IdComparator("@TEST.FRAME.1"))), stmt.condition())

    def test_from_instance(self):
        from backend.models.statement import ExpectationStatement

        stmt = Frame("@TEST.FRAME").add_parent("@EXE.EXPECTATION-STATEMENT")
        stmt = Statement.from_instance(stmt)

        self.assertIsInstance(stmt, ExpectationStatement)

    def test_run(self):
        from backend.models.statement import ExistsStatement, ExpectationStatement

        condition = ExistsStatement.instance(Space("TEST"), Query().search(IdComparator("@TEST.FRAME.1")))
        stmt = ExpectationStatement.instance(Space("TEST"), condition)

        scope = StatementScope()
        self.assertEqual([], scope.expectations)

        stmt.run(scope, None)
        self.assertEqual([condition], scope.expectations)

        stmt.run(scope, None)
        self.assertEqual([condition, condition], scope.expectations)


class ForEachStatementTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")

    def test_run(self):

        class TestStatement(Statement):
            def run(self, scope: StatementScope(), varmap: VariableMap):
                frame = varmap.resolve("$FOR")
                frame["c"] = frame["a"][0].resolve().value + frame["b"][0].resolve().value

        foreach = Frame("@TEST.FRAME").add_parent("@EXE.FOREACH-STATEMENT")
        stmt = Frame("@TEST.STMT").add_parent("@EXE.STATEMENT")
        varmap = Frame("@TEST.VARMAP")

        target1 = Frame("@TEST.TARGET.?")
        target2 = Frame("@TEST.TARGET.?")

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
        graph.reset()
        Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")

    def test_run(self):
        stmt = Frame("@TEST.FRAME").add_parent("@EXE.IS-STATEMENT")
        target = Frame("@TEST.TARGET")

        stmt["DOMAIN"] = target
        stmt["SLOT"] = "X"
        stmt["FILLER"] = 123

        stmt = Statement.from_instance(stmt)

        self.assertFalse(stmt.run(StatementScope(), None))

        target["X"] = 123
        self.assertTrue(stmt.run(StatementScope(), None))

    def test_variable_domain(self):
        stmt = Frame("@TEST.FRAME").add_parent("@EXE.IS-STATEMENT")
        target = Frame("@TEST.TARGET")
        varmap = Frame("@TEST.VARMAP")

        stmt["DOMAIN"] = "$VAR"
        stmt["SLOT"] = "X"
        stmt["FILLER"] = 123

        varmap = VariableMap(varmap)
        Variable.instance(Space("TEST"), "$VAR", target, varmap)

        stmt = Statement.from_instance(stmt)

        self.assertFalse(stmt.run(StatementScope(), varmap))

        target["X"] = 123
        self.assertTrue(stmt.run(StatementScope(), varmap))

    def test_variable_filler(self):
        stmt = Frame("@TEST.FRAME").add_parent("@EXE.IS-STATEMENT")
        target = Frame("@TEST.TARGET")
        varmap = Frame("@TEST.VARMAP")

        stmt["DOMAIN"] = target
        stmt["SLOT"] = "X"
        stmt["FILLER"] = "$VAR"

        varmap = VariableMap(varmap)
        Variable.instance(Space("TEST"), "$VAR", 123, varmap)

        stmt = Statement.from_instance(stmt)

        self.assertFalse(stmt.run(StatementScope(), varmap))

        target["X"] = 123
        self.assertTrue(stmt.run(StatementScope(), varmap))


class MakeInstanceStatementTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")

    def test_run(self):
        makeinstance = Frame("@TEST.FRAME").add_parent("@EXE.MAKEINSTANCE-STATEMENT")
        target = Frame("@TEST.TARGET")

        makeinstance["IN"] = "EXE"
        makeinstance["OF"] = target
        makeinstance["PARAMS"] = [1, 2, 3]

        target["WITH"] = ["$A", "$B", "$C"]

        instance = Statement.from_instance(makeinstance).run(StatementScope(), None)
        self.assertTrue(instance in graph)
        self.assertEqual(VariableMap(instance).resolve("$A"), 1)
        self.assertEqual(VariableMap(instance).resolve("$B"), 2)
        self.assertEqual(VariableMap(instance).resolve("$C"), 3)

        makeinstance["IN"] = "OTHER"
        instance = Statement.from_instance(makeinstance).run(StatementScope(), None)
        self.assertTrue(instance in Space("OTHER"))

    def test_raises_exception_on_mismatched_params(self):
        makeinstance = Frame("@TEST.FRAME").add_parent("@EXE.MAKEINSTANCE-STATEMENT")
        target = Frame("@TEST.TARGET")

        makeinstance["OF"] = target
        makeinstance["PARAMS"] = [1, 2, 3]

        with self.assertRaises(Exception):
            Statement.from_instance(makeinstance).run(StatementScope(), None)


class MeaningProcedureStatementTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")

    def test_run(self):
        result = 0

        class TestMP(AgentMethod):
            def run(self, a, b, c):
                nonlocal result
                result += a
                result += b
                result += c
                result += self.statement.frame["X"][0]

        from backend.models.mps import MPRegistry
        MPRegistry.register(TestMP)

        mp = Frame("@TEST.FRAME").add_parent("@EXE.MP-STATEMENT")

        mp["CALLS"] = TestMP.__name__
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
                result += self.statement.frame["X"][0]

        from backend.models.mps import MPRegistry
        MPRegistry.register(TestMP)

        mp = Frame("@TEST.FRAME").add_parent("@EXE.MP-STATEMENT")
        varmap = Frame("@TEST.VARMAP")

        mp["CALLS"] = TestMP.__name__
        mp["PARAMS"] = [1, 2, "$var"]
        mp["X"] = 4

        varmap = VariableMap(varmap)
        Variable.instance(Space("TEST"), "$var", 3, varmap)

        Statement.from_instance(mp).run(StatementScope(), varmap)

        self.assertEqual(result, 10)


class OutputXMRStatementTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")

    def test_template(self):
        from backend.models.output import OutputXMRTemplate
        from backend.models.statement import OutputXMRStatement

        template = OutputXMRTemplate.build("test-template", XMR.Type.ACTION, "EXE.CAPABILITY", [])

        frame = Frame("@TEST.FRAME").add_parent("@EXE.OUTPUTXMR-STATEMENT")
        frame["TEMPLATE"] = "test-template"

        stmt: OutputXMRStatement = Statement.from_instance(frame)
        self.assertEqual(template, stmt.template())

    def test_params(self):
        from backend.models.statement import OutputXMRStatement

        frame = Frame("@TEST.FRAME").add_parent("@EXE.OUTPUTXMR-STATEMENT")
        frame["PARAMS"] = [1, 2, "$var1", "$var2"]

        stmt: OutputXMRStatement = Statement.from_instance(frame)
        self.assertEqual([1, 2, "$var1", "$var2"], stmt.params())

    def test_agent(self):
        from backend.models.statement import OutputXMRStatement

        agent = Frame("@TEST.AGENT")

        frame = Frame("@TEST.FRAME").add_parent("@EXE.OUTPUTXMR-STATEMENT")
        frame["AGENT"] = agent

        stmt: OutputXMRStatement = Statement.from_instance(frame)
        self.assertEqual(agent, stmt.agent())

    def test_instance(self):
        from backend.models.output import OutputXMRTemplate
        from backend.models.statement import OutputXMRStatement

        template = OutputXMRTemplate.build("test-template", XMR.Type.ACTION, "@EXE.CAPABILITY", [])
        params = [1, 2, "$var1", "$var2"]
        agent = Frame("@TEST.AGENT")

        stmt = OutputXMRStatement.instance(Space("TEST"), template, params, agent)

        self.assertEqual(template, stmt.template())
        self.assertEqual(params, stmt.params())
        self.assertEqual(agent, stmt.agent())

    def test_run(self):
        from backend.models.output import OutputXMRTemplate
        from backend.models.statement import OutputXMRStatement

        Frame("@TEST.CAPABILITY")

        template = OutputXMRTemplate.build("test-template", XMR.Type.ACTION, "@EXE.CAPABILITY", [])
        agent = Frame("@TEST.AGENT")

        stmt = OutputXMRStatement.instance(Space("TEST"), template, [], agent)

        self.assertNotIn("XMR#1", graph)

        varmap = Frame("@TEST.MY-VARMAP-TEST")
        varmap = VariableMap(varmap)
        output = stmt.run(StatementScope(), varmap)

        self.assertIsInstance(output, XMR)
        self.assertIn(output.frame, Space("OUTPUTS"))
        self.assertEqual(Space("XMR#1"), output.graph())

    def test_run_affects_scope(self):
        from backend.models.output import OutputXMRTemplate
        from backend.models.statement import OutputXMRStatement

        Frame("@TEST.CAPABILITY")

        template = OutputXMRTemplate.build("test-template", XMR.Type.ACTION, "@EXE.CAPABILITY", [])
        agent = Frame("@TEST.AGENT")
        test1 = Frame("@TEST.TEST1")
        test2 = Frame("@TEST.TEST2")

        stmt = OutputXMRStatement.instance(Space("TEST"), template, [], agent)

        self.assertNotIn("XMR#1", Space("TEST"))

        varmap = Frame("@TEST.MY-VARMAP-TEST")
        varmap = VariableMap(varmap)
        scope = StatementScope()
        output = stmt.run(scope, varmap)

        self.assertIn(output.frame, scope.outputs)

    def test_run_with_variables(self):
        from backend.models.output import OutputXMRTemplate
        from backend.models.statement import OutputXMRStatement

        Frame("@TEST.CAPABILITY")

        template = OutputXMRTemplate.build("test-template", XMR.Type.ACTION, "@EXE.CAPABILITY", ["$var1", "$var2"])
        f = Frame("@" + template.space.name + ".FRAME.?")
        f["PROP1"] = "$var1"
        f["PROP2"] = "$var1"
        f["PROP3"] = "$var2"

        agent = Frame("@TEST.AGENT")
        stmt = OutputXMRStatement.instance(Space("TEST"), template, [123, "$myvar"], agent)

        varmap = Frame("@TEST.MY-VARMAP-TEST")
        varmap = VariableMap(varmap)
        Variable.instance(Space("TEST"), "$myvar", "abc", varmap)

        output = stmt.run(StatementScope(), varmap)

        fi = Frame("@" + output.graph().name + ".FRAME.1")
        self.assertEqual(123, fi["PROP1"])
        self.assertEqual(123, fi["PROP2"])
        self.assertEqual("abc", fi["PROP3"])


class TransientFrameStatementTestCase(unittest.TestCase):

    def setUp(self):
        graph.reset()
        Bootstrap.bootstrap_resource(None, "backend.resources", "exe.knowledge")

    def test_properties(self):
        from backend.models.bootstrap import BootstrapTriple
        from backend.models.statement import TransientFrameStatement

        triple1 = BootstrapTriple("TEST", 123)
        triple2 = BootstrapTriple("TEST", 456)
        triple3 = BootstrapTriple("XYZ", Identifier("@TEST.FRAME.1"))

        statement = Frame("@TEST.STATEMENT")
        statement["HAS-PROPERTY"] += triple1
        statement["HAS-PROPERTY"] += triple2
        statement["HAS-PROPERTY"] += triple3

        self.assertEqual([triple1, triple2, triple3], TransientFrameStatement(statement).properties())

    def test_instance(self):
        from backend.models.bootstrap import BootstrapTriple
        from backend.models.statement import TransientFrameStatement

        triple1 = BootstrapTriple("TEST", 123)
        triple2 = BootstrapTriple("TEST", 456)
        triple3 = BootstrapTriple("XYZ", Identifier("@TEST.FRAME.1"))

        statement = TransientFrameStatement.instance(Space("TEST"), [triple1, triple2, triple3])

        self.assertEqual([triple1, triple2, triple3], statement.properties())

    def test_from_instance(self):
        from backend.models.statement import TransientFrameStatement

        frame = Frame("@TEST.STATEMENT").add_parent("@EXE.TRANSIENTFRAME-STATEMENT")
        statement = Statement.from_instance(frame)

        self.assertIsInstance(statement, TransientFrameStatement)

    def test_run(self):
        from backend.models.bootstrap import BootstrapTriple
        from backend.models.statement import TransientFrameStatement

        triple1 = BootstrapTriple("TEST", 123)
        triple2 = BootstrapTriple("TEST", 456)
        triple3 = BootstrapTriple("XYZ", Identifier("@TEST.FRAME.1"))
        triple4 = BootstrapTriple("ABC", "$var1")
        triple5 = BootstrapTriple("DEF", "test")

        statement = TransientFrameStatement.instance(Space("TEST"), [triple1, triple2, triple3, triple4, triple5])

        varmap = VariableMap(Frame("@TEST.VARMAP"))
        Variable.instance(Space("TEST"), "$var1", 789, varmap)

        scope = StatementScope()
        frame = statement.run(scope, varmap)

        self.assertEqual("@EXE.TRANSIENT-FRAME.1", frame.id)
        self.assertEqual(Space("EXE"), frame.space())
        self.assertIn(frame, graph)
        self.assertEqual([123, 456], frame["TEST"])
        self.assertEqual("@TEST.FRAME.1", frame["XYZ"])
        self.assertEqual(789, frame["ABC"])
        self.assertEqual("test", frame["DEF"])
        self.assertIn(frame, scope.transients)