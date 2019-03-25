from backend.models.mps import MPRegistry
from ontograph.Frame import Frame
from ontograph.Graph import Graph
from ontograph.Index import Identifier
from ontograph.Query import Query
from ontograph.Space import Space
from typing import Any, Callable, List, Type, Union


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.models.output import OutputXMR, OutputXMRTemplate


class Variable(object):

    @classmethod
    def instance(cls, space: Space, name: str, value: Any, varmap: 'VariableMap', assign: bool=True):
        if value == []:
            value = [[]]

        frame = Frame("@" + space.name + ".VARIABLE.?")
        frame["NAME"] = name
        frame["VALUE"] = value
        frame["FROM"] = varmap.frame

        if assign:
            varmap.assign(name, frame)

        return Variable(frame)

    def __init__(self, frame: Frame):
        self.frame = frame

    def name(self) -> str:
        if "NAME" in self.frame:
            return self.frame["NAME"][0]
        raise Exception("Unnamed variable '" + self.frame.id + "'.")

    def value(self) -> Any:
        if "VALUE" in self.frame:
            return self.frame["VALUE"][0]
        raise Exception("Variable '" + self.name() + "' has no value.")

    def set_value(self, value: Any):
        self.frame["VALUE"] = value

    def varmap(self) -> 'VariableMap':
        if "FROM" in self.frame:
            return VariableMap(self.frame["FROM"][0])
        raise Exception("Variable '" + self.name() + "' has no varmap.")

    def __eq__(self, other):
        if isinstance(other, Variable):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other

        return super().__eq__(other)


class VariableMap(object):

    @classmethod
    def instance_of(cls, space: Space, definition: Frame, params: List[Any], existing: Union[str, Identifier, Frame]=None) -> 'VariableMap':
        if existing is not None:
            if isinstance(existing, str):
                existing = Frame(existing)
            if isinstance(existing, Identifier):
                existing = Frame(existing.id)

        frame = existing
        if frame is None:
            frame = Frame("@" + space.name + ".VARMAP.?").add_parent(definition)

        for i, var in enumerate(definition["WITH"]):
            frame["WITH"] += var
            variable_instance = Frame("@" + space.name + ".VARIABLE.?")
            variable_instance["NAME"] = var
            variable_instance["FROM"] = frame
            variable_instance["VALUE"] = params[i]

            frame["_WITH"] += variable_instance

        return VariableMap(frame)

    def __init__(self, frame: Frame):
        self.frame = frame

    def assign(self, name: str, variable: Union[str, Identifier, Frame, Variable]):
        if isinstance(variable, str):
            variable = Frame(variable)
        if isinstance(variable, Identifier):
            variable = Frame(variable.id)
        if isinstance(variable, Variable):
            variable = variable.frame

        self.frame["_WITH"] += variable

    def resolve(self, name: str) -> Any:
        return self.find(name).value()

    def find(self, name: str) -> Variable:
        for var in self.frame["_WITH"]:
            var = Variable(var)
            if var.name() == name:
                return var
        raise Exception("Variable '" + name + "' is not defined in this mapping.")

    def variables(self) -> List[str]:
        return list(self.frame["WITH"])

    def __eq__(self, other):
        if isinstance(other, VariableMap):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)


class TransientFrame(object):

    def __init__(self, frame: Frame):
        self.frame = frame

    def is_in_scope(self) -> bool:
        if "__IN_SCOPE__" in self.frame:
            return self.frame["__IN_SCOPE__"].singleton()()
        return True

    def update_scope(self, condition: Callable):
        self.frame["__IN_SCOPE__"] = condition

    def __eq__(self, other):
        if isinstance(other, TransientFrame):
            return self.frame == other.frame
        elif isinstance(other, Frame):
            return self.frame == other

        return super().__eq__(other)


class TransientTriple(object):

    def __init__(self, slot: str, filler: Union[Identifier, Any], facet: str=None):
        self.slot = slot
        self.facet = facet
        self.filler = filler

    def __eq__(self, other):
        if isinstance(other, TransientTriple):
            return self.slot == other.slot and self.facet == other.facet and self.filler == other.filler
        return super().__eq__(other)


class StatementScope(object):

    def __init__(self):
        from backend.models.agenda import Expectation
        from backend.models.output import XMR

        self.outputs: List[XMR] = []
        self.expectations: List[Expectation] = []
        self.transients: List[TransientFrame] = []
        self.variables = {}


class Registry(object):

    def __init__(self):
        self.statements = dict()
        self.load_defaults()

    def load_defaults(self):
        for sub in Statement.__subclasses__():
            self.register(sub)

    def register(self, clazz: Type['Statement'], name: str=None):
        if name is None:
            name = clazz.__qualname__

        self.statements[name] = clazz

    def lookup(self, name: str) -> Type['Statement']:
        return self.statements[name]

    def reset(self):
        self.statements = dict()
        self.load_defaults()


class Statement(object):

    @classmethod
    def from_instance(cls, frame: Frame) -> 'Statement':
        definition = frame.parents()[0]
        clazz = definition["CLASSMAP"][0]
        return StatementRegistry.lookup(clazz)(frame)

    def __init__(self, frame: Frame):
        self.frame = frame

    def run(self, scope: StatementScope, varmap: VariableMap) -> Any:
        raise Exception("Statement.run(scope, varmap) must be implemented.")

    def _resolve_param(self, param: Any, varmap: VariableMap):
        if isinstance(param, Frame):
            return param
        if isinstance(param, Identifier):
            try:
                return Frame(param.id)
            except: param = param.id
        if isinstance(param, str):
            try:
                return varmap.resolve(param)
            except: pass

            try:
                return Frame(Identifier.parse(param).id)
            except: pass

        return param

    def __eq__(self, other):
        if isinstance(other, Statement):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)


class AddFillerStatement(Statement):

    @classmethod
    def instance(cls, space: Space, to: Union[str, Identifier, Frame, Query], slot: str, value: Any):
        if isinstance(value, Statement):
            value = value.frame

        frame = Frame("@" + space.name + ".ADDFILLER-STATEMENT.?").add_parent("@EXE.ADDFILLER-STATEMENT")
        frame["TO"] = to
        frame["SLOT"] = slot
        frame["ADD"] = value

        return AddFillerStatement(frame)

    def run(self, scope: StatementScope, varmap: VariableMap):
        to: Any = self.frame["TO"][0]
        slot: str = self.frame["SLOT"][0]
        value: Any = self.frame["ADD"][0]

        if isinstance(to, Identifier):
            to = Frame(self.frame.id)
        if isinstance(to, Query):
            to = to.start()
        if isinstance(to, str):
            try:
                to = varmap.resolve(to)
            except: pass
        if isinstance(to, str):
            try:
                Identifier.parse(to)
                to = Frame(to)
            except: pass
        if isinstance(to, Frame):
            to = [to]

        if isinstance(value, str):
            try:
                value = varmap.resolve(value)
            except: pass
        if isinstance(value, Frame):
            if value ^ "@EXE.RETURNING-STATEMENT":
                value = Statement.from_instance(value).run(StatementScope(), varmap)

        for frame in to:
            frame[slot] += value

    def __eq__(self, other):
        if isinstance(other, AddFillerStatement):
            return other.frame["TO"] == list(self.frame["TO"]) and \
                   other.frame["SLOT"] == list(self.frame["SLOT"]) and \
                   self.__eqADD(other)
        return super().__eq__(other)

    def __eqADD(self, other: 'AddFillerStatement') -> bool:
        if other.frame["ADD"] == list(self.frame["ADD"]):
            return True

        try:
            s1 = list(map(lambda frame: Statement.from_instance(frame.resolve()), self.frame["ADD"]))
            s2 = list(map(lambda frame: Statement.from_instance(frame.resolve()), other.frame["ADD"]))
            return s1 == s2
        except: pass

        return False


class AssertStatement(Statement):

    class ImpasseException(Exception):

        def __init__(self, resolutions: List['MakeInstanceStatement']):
            self.resolutions = resolutions

    @classmethod
    def instance(cls, space: Space, assertion: Union[str, Identifier, Frame, Statement], resolutions: List[Union[str, Identifier, Frame, 'MakeInstanceStatement']]):
        if isinstance(assertion, Statement):
            assertion = assertion.frame
        resolutions = list(map(lambda r: r.frame if isinstance(r, MakeInstanceStatement) else r, resolutions))

        stmt = Frame("@" + space.name + ".ASSERT-STATEMENT.?").add_parent("@EXE.ASSERT-STATEMENT")
        stmt["ASSERTION"] = assertion
        stmt["RESOLUTION"] = resolutions

        return AssertStatement(stmt)

    def assertion(self) -> Statement:
        return Statement.from_instance(self.frame["ASSERTION"].singleton())

    def resolutions(self) -> List['MakeInstanceStatement']:
        return list(map(lambda s: MakeInstanceStatement(s), self.frame["RESOLUTION"]))

    def run(self, scope: StatementScope, varmap: VariableMap):
        if not self.assertion().run(scope, varmap):
            raise AssertStatement.ImpasseException(self.resolutions())

    def __eq__(self, other):
        if isinstance(other, AssertStatement):
            return self.assertion() == other.assertion() and \
                   self.resolutions() == other.resolutions()
        return super().__eq__(other)


class AssignFillerStatement(Statement):

    @classmethod
    def instance(cls, space: Space, to: Union[str, Identifier, Frame, Query], slot: str, value: Any):
        frame = Frame("@" + space.name + ".ASSIGNFILLER-STATEMENT.?").add_parent("@EXE.ASSIGNFILLER-STATEMENT")
        frame["TO"] = to
        frame["SLOT"] = slot
        frame["ASSIGN"] = value

        return AssignFillerStatement(frame)

    def run(self, scope: StatementScope, varmap: VariableMap):
        to: Any = self.frame["TO"][0]
        slot: str = self.frame["SLOT"][0]
        value: Any = self.frame["ASSIGN"][0]

        if isinstance(to, Identifier):
            to = Frame(to.id)
        if isinstance(to, Query):
            to = list(to.start())
        if isinstance(to, str):
            try:
                to = varmap.resolve(to)
            except: pass
        if isinstance(to, Frame):
            to = [to]

        if isinstance(value, str):
            try:
                value = varmap.resolve(value)
            except: pass
        if isinstance(value, Frame):
            if value ^ "@EXE.RETURNING-STATEMENT":
                value = Statement.from_instance(value).run(StatementScope(), varmap)

        for frame in to:
            frame[slot] = value

    def __eq__(self, other):
        if isinstance(other, AssignFillerStatement):
            return other.frame["TO"] == list(self.frame["TO"]) and \
                   other.frame["SLOT"] == list(self.frame["SLOT"]) and \
                   other.frame["ASSIGN"] == list(self.frame["ASSIGN"])
        return super().__eq__(other)


class AssignVariableStatement(Statement):

    @classmethod
    def instance(cls, space: Space, variable: str, value: Any):
        frame = Frame("@" + space.name + ".ASSIGNVARIABLE-STATEMENT.?").add_parent("@EXE.ASSIGNVARIABLE-STATEMENT")
        frame["TO"] = variable
        frame["ASSIGN"] = value

        return AssignVariableStatement(frame)

    def run(self, scope: StatementScope, varmap: VariableMap):
        variable = self.frame["TO"].singleton()
        value = self.frame["ASSIGN"].singleton()
        value = self._resolve(value, scope, varmap)

        Variable.instance(self.frame.space(), variable, value, varmap)

    def _resolve(self, value, scope: StatementScope, varmap: VariableMap):
        if isinstance(value, list):
            return list(map(lambda v: self._resolve(v, scope, varmap), value))
        if isinstance(value, str):
            try:
                return varmap.resolve(value)
            except:
                pass
        if isinstance(value, Statement) and value.frame ^ "@EXE.RETURNING-STATEMENT":
            return value.run(StatementScope(), varmap)
        if isinstance(value, Frame) and value ^ "@EXE.RETURNING-STATEMENT":
            return Statement.from_instance(value).run(StatementScope(), varmap)

        return value

    def __eq__(self, other):
        if isinstance(other, AssignVariableStatement):
            return list(self.frame["TO"]) == list(other.frame["TO"]) and list(self.frame["ASSIGN"]) == list(other.frame["ASSIGN"])
        return super().__eq__(other)


class ExistsStatement(Statement):

    @classmethod
    def instance(cls, space: Space, query: Query):
        frame = Frame("@" + space.name + ".EXISTS-STATEMENT.?").add_parent("@EXE.EXISTS-STATEMENT")
        frame["FIND"] = query

        return ExistsStatement(frame)

    def run(self, scope: StatementScope, varmap: VariableMap) -> bool:
        query = self.frame["FIND"][0]
        results = query.start()
        return len(results) > 0

    def __eq__(self, other):
        if isinstance(other, ExistsStatement):
            return other.frame["FIND"].singleton() == self.frame["FIND"].singleton()

        return super().__eq__(other)


class ExpectationStatement(Statement):

    @classmethod
    def instance(cls, space: Space, condition: Union[str, Identifier, Frame, Statement]):
        if isinstance(condition, Statement):
            condition = condition.frame

        frame = Frame("@" + space.name + ".EXPECTATION-STATEMENT.?").add_parent("@EXE.EXPECTATION-STATEMENT")
        frame["CONDITION"] = condition

        return ExpectationStatement(frame)

    def condition(self) -> Statement:
        return Statement.from_instance(self.frame["CONDITION"].singleton())

    def run(self, scope: StatementScope, varmap: VariableMap):
        scope.expectations.append(self.condition())

    def __eq__(self, other):
        if isinstance(other, ExpectationStatement):
            return self.condition() == other.condition()

        return super().__eq__(other)


class ForEachStatement(Statement):

    @classmethod
    def instance(cls, space: Space, query: Query, assign: str, do: Union[Statement, List[Statement]]):
        if isinstance(do, Statement):
            do = [do]
        do = list(map(lambda do: do.frame, do))

        frame = Frame("@" + space.name + ".FOREACH-STATEMENT.?").add_parent("@EXE.FOREACH-STATEMENT")
        frame["FROM"] = query
        frame["ASSIGN"] = assign
        frame["DO"] = do

        return ForEachStatement(frame)

    def run(self, scope: StatementScope, varmap: VariableMap):
        query: Query = self.frame["FROM"].singleton()
        variable: str = self.frame["ASSIGN"].singleton()
        do: List[Statement] = list(map(lambda stmt: Statement.from_instance(stmt), self.frame["DO"]))

        var: Variable = None
        try:
            var = varmap.find(variable)
        except:
            var = Variable.instance(self.frame.space(), variable, None, varmap)

        for frame in query.start():
            var.set_value(frame)
            for stmt in do:
                stmt.run(scope, varmap)

    def __eq__(self, other):
        if isinstance(other, ForEachStatement):
            return list(other.frame["FROM"]) == list(self.frame["FROM"]) and \
                   other.frame["ASSIGN"] == list(self.frame["ASSIGN"]) and \
                   list(map(lambda frame: Statement.from_instance(frame), other.frame["DO"])) == list(map(lambda frame: Statement.from_instance(frame), self.frame["DO"]))

        return super().__eq__(other)


class IsStatement(Statement):

    @classmethod
    def instance(clsg, space: Space, domain: Union[str, Identifier, Frame], slot: str, filler: Any):
        frame = Frame("@" + space.name + ".IS-STATEMENT.?").add_parent("@EXE.IS-STATEMENT")
        frame["DOMAIN"] = domain
        frame["SLOT"] = slot
        frame["FILLER"] = filler

        return IsStatement(frame)

    def run(self, scope: StatementScope, varmap: VariableMap):
        domain = self.frame["DOMAIN"][0]
        slot: str = self.frame["SLOT"][0]
        filler = self.frame["FILLER"][0]

        if isinstance(domain, str):
            try:
                domain = varmap.resolve(domain)
            except: pass
        if not isinstance(domain, Frame):
            return False  # Typically this means a variable could not be resolved, so it cannot possibly match yet

        if isinstance(filler, str):
            try:
                filler = varmap.resolve(filler)
            except: pass

        return domain[slot] == filler

    def __eq__(self, other):
        if isinstance(other, IsStatement):
            return other.frame["DOMAIN"] == list(self.frame["DOMAIN"]) and \
                   other.frame["SLOT"] == list(self.frame["SLOT"]) and \
                   other.frame["FILLER"] == list(self.frame["FILLER"])
        return super().__eq__(other)


class MakeInstanceStatement(Statement):

    @classmethod
    def instance(cls, space: Space, in_graph: str, of: Union[str, Identifier, Frame], params: List[Any]):
        frame = Frame("@" + space.name + ".MAKEINSTANCE-STATEMENT.?").add_parent("@EXE.MAKEINSTANCE-STATEMENT")
        frame["IN"] = in_graph
        frame["OF"] = of
        frame["PARAMS"] = params

        return MakeInstanceStatement(frame)

    def run(self, scope: StatementScope, varmap: VariableMap):
        space: str = self.frame["IN"][0]
        of: Frame = self.frame["OF"][0]
        params: List[Any] = self.frame["PARAMS"]

        if isinstance(of, str):
            of = Frame(of)
        if isinstance(of, Identifier):
            of = Frame(of.id)

        instance = Frame("@" + space + "." + Identifier.parse(of.id)[1] + ".?").add_parent(of)

        if len(params) != len(instance["WITH"]):
            raise Exception("Mismatched parameter count when making instance of '" + of.id + "' with parameters '" + str(params) + "'.")

        params = list(map(lambda param: self._resolve_param(param, varmap), params))

        if of ^ "@EXE.GOAL":
            from backend.models.agenda import Goal
            Goal.instance_of(self.frame.space(), of, params, existing=instance)
        else:
            VariableMap.instance_of(self.frame.space(), of, params, existing=instance)

        return instance

    def __eq__(self, other):
        if isinstance(other, MakeInstanceStatement):
            return other.frame["IN"] == list(self.frame["IN"]) and \
                   other.frame["OF"] == list(self.frame["OF"]) and \
                   other.frame["PARAMS"] == list(self.frame["PARAMS"])
        return super().__eq__(other)


class MeaningProcedureStatement(Statement):

    @classmethod
    def instance(cls, space: Space, calls: str, params: List[Any]):
        frame = Frame("@" + space.name + ".MP-STATEMENT.?").add_parent("@EXE.MP-STATEMENT")
        frame["CALLS"] = calls
        frame["PARAMS"] = params

        return MeaningProcedureStatement(frame)

    def run(self, scope: StatementScope, varmap: VariableMap):
        mp: str = self.frame["CALLS"][0]

        params = list(map(lambda param: self._resolve_param(param, varmap), self.frame["PARAMS"]))

        from backend import agent
        result = MPRegistry.run(mp, agent, *params, statement=self, varmap=varmap)
        return result

    def __eq__(self, other):
        if isinstance(other, MeaningProcedureStatement):
            return other.frame["CALLS"] == list(self.frame["CALLS"]) and \
                   other.frame["PARAMS"] == list(self.frame["PARAMS"])
        return super().__eq__(other)


class OutputXMRStatement(Statement):

    @classmethod
    def instance(cls, space: Space, template: Union[str, Graph, 'OutputXMRTemplate'], params: List[Any], agent: Union[str, Identifier, Frame]):
        from backend.models.output import OutputXMRTemplate

        frame = Frame("@" + space.name + ".OUTPUTXMR-STATEMENT.?").add_parent("@EXE.OUTPUTXMR-STATEMENT")

        if isinstance(template, Space):
            template = OutputXMRTemplate(template)
        if isinstance(template, OutputXMRTemplate):
            template = template.name()

        frame["TEMPLATE"] = template
        frame["PARAMS"] = params
        frame["AGENT"] = agent

        return OutputXMRStatement(frame)

    def template(self) -> 'OutputXMRTemplate':
        from backend.models.output import OutputXMRTemplate

        return OutputXMRTemplate.lookup(self.frame["TEMPLATE"].singleton())

    def params(self) -> List[Any]:
        return list(self.frame["PARAMS"])

    def agent(self) -> Frame:
        return self.frame["AGENT"].singleton()

    def run(self, scope: StatementScope, varmap: VariableMap) -> 'OutputXMR':
        agent = self.agent()

        params = self.params()
        params = list(map(lambda param: self._resolve_param(param, varmap), params))

        output = self.template().create(Space("OUTPUTS"), params)
        scope.outputs.append(output)

        return output

    def __eq__(self, other):
        if isinstance(other, OutputXMRStatement):
            return self.template() == other.template() and \
                self.params() == other.params() and \
                self.agent() == other.agent()
        elif isinstance(other, Frame):
            return self.frame == other

        return super().__eq__(other)


class TransientFrameStatement(Statement):

    @classmethod
    def instance(cls, space: Space, properties: List['TransientTriple']):
        frame = Frame("@" + space.name + ".TRANSIENTFRAME-STATEMENT.?").add_parent("@EXE.TRANSIENTFRAME-STATEMENT")

        for property in properties:
            frame["HAS-PROPERTY"] += property

        return TransientFrameStatement(frame)

    def properties(self) -> List['TransientTriple']:
        return list(self.frame["HAS-PROPERTY"])

    def run(self, scope: StatementScope, varmap: VariableMap):
        frame = Frame("@EXE.TRANSIENT-FRAME.?").add_parent("@EXE.TRANSIENT-FRAME")

        for property in self.properties():
            filler = property.filler
            if isinstance(filler, str):
                try:
                    filler = varmap.resolve(filler)
                except: pass

            frame[property.slot] += filler

        scope.transients.append(TransientFrame(frame))

        return frame

    def __eq__(self, other):
        if isinstance(other, TransientFrameStatement):
            return self.properties() == other.properties()
        elif isinstance(other, Frame):
            return self.frame == other

        return super().__eq__(other)


StatementRegistry = Registry()