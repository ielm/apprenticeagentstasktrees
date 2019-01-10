from backend.models.graph import Filler, Frame, Graph, Identifier, Literal
from backend.models.mps import MPRegistry
from backend.models.query import Query
from pydoc import locate
from typing import Any, List, Union

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.models.output import OutputXMR, OutputXMRTemplate


class Variable(object):

    @classmethod
    def instance(cls, graph: Graph, name: str, value: Any, varmap: 'VariableMap', assign: bool=True):
        if value == []:
            value = [[]]

        frame = graph.register("VARIABLE", generate_index=True)
        frame["NAME"] = Literal(name)
        frame["VALUE"] = value
        frame["FROM"] = varmap.frame

        if assign:
            varmap.assign(name, frame)

        return Variable(frame)

    def __init__(self, frame: Frame):
        self.frame = frame

    def name(self) -> str:
        if "NAME" in self.frame:
            return self.frame["NAME"][0].resolve().value
        raise Exception("Unnamed variable '" + self.frame.name() + "'.")

    def value(self) -> Any:
        if "VALUE" in self.frame:
            value = self.frame["VALUE"][0].resolve()
            if isinstance(value, Literal):
                return value.value
            return value
        raise Exception("Variable '" + self.name() + "' has no value.")

    def set_value(self, value: Any):
        self.frame["VALUE"] = value

    def varmap(self) -> 'VariableMap':
        if "FROM" in self.frame:
            return VariableMap(self.frame["FROM"][0].resolve())
        raise Exception("Variable '" + self.name() + "' has no varmap.")

    def __eq__(self, other):
        if isinstance(other, Variable):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other

        return super().__eq__(other)


class VariableMap(object):

    @classmethod
    def instance_of(cls, graph: Graph, definition: Frame, params: List[Any], existing: Union[str, Identifier, Frame]=None) -> 'VariableMap':
        if existing is not None:
            if isinstance(existing, str):
                existing = Identifier.parse(existing)
            if isinstance(existing, Identifier):
                existing = existing.resolve(graph)

        frame = existing if existing is not None else graph.register("VARMAP", isa=definition._identifier, generate_index=True)
        for i, var in enumerate(definition["WITH"]):
            frame["WITH"] += var
            variable_instance = graph.register("VARIABLE", generate_index=True)
            variable_instance["NAME"] = var
            variable_instance["FROM"] = frame
            variable_instance["VALUE"] = params[i]

            frame["_WITH"] += variable_instance

        return VariableMap(frame)

    def __init__(self, frame: Frame):
        self.frame = frame

    def assign(self, name: str, variable: Union[str, Identifier, Frame, Variable]):
        if isinstance(variable, str):
            variable = Identifier.parse(variable)
        if isinstance(variable, Frame):
            variable = variable._identifier
        if isinstance(variable, Variable):
            variable = variable.frame._identifier

        self.frame["_WITH"] += variable

    def resolve(self, name: str) -> Any:
        return self.find(name).value()

    def find(self, name: str) -> Variable:
        for var in self.frame["_WITH"]:
            var = Variable(var.resolve())
            if var.name() == name:
                return var
        raise Exception("Variable '" + name + "' is not defined in this mapping.")

    def variables(self) -> List[str]:
        return list(map(lambda v: v.resolve().value, self.frame["WITH"]))

    def __eq__(self, other):
        if isinstance(other, VariableMap):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)


class StatementScope(object):

    def __init__(self):
        from backend.models.output import OutputXMR
        self.outputs: List[OutputXMR] = []


class Statement(object):

    @classmethod
    def from_instance(cls, frame: Frame) -> 'Statement':
        definition = frame.parents()[0].resolve(frame._graph, network=frame._network)
        clazz = definition["CLASSMAP"][0].resolve().value
        if isinstance(clazz, str):
            clazz = locate(definition["CLASSMAP"][0].resolve().value)
        return clazz(frame)

    def __init__(self, frame: Frame):
        self.frame = frame

    def run(self, scope: StatementScope, varmap: VariableMap) -> Any:
        raise Exception("Statement.run(scope, varmap) must be implemented.")

    def _resolve_param(self, param: Any, varmap: VariableMap):
        if isinstance(param, Filler):
            param = param._value
        if isinstance(param, Frame):
            return param
        if isinstance(param, Identifier):
            try:
                return param.resolve(self.frame._graph)
            except: param = param.render()
        if isinstance(param, Literal):
            param = param.value
        if isinstance(param, str):
            try:
                return varmap.resolve(param)
            except: pass

            try:
                return Identifier.parse(param).resolve(self.frame._graph)
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
    def instance(cls, graph: Graph, to: Union[str, Identifier, Frame, Query], slot: str, value: Any):
        if isinstance(value, Statement):
            value = value.frame

        frame = graph.register("ADDFILLER-STATEMENT", isa="EXE.ADDFILLER-STATEMENT", generate_index=True)
        frame["TO"] = to
        frame["SLOT"] = Literal(slot)
        frame["ADD"] = value

        return AddFillerStatement(frame)

    def run(self, scope: StatementScope, varmap: VariableMap):
        to: Any = self.frame["TO"][0].resolve()
        slot: str = self.frame["SLOT"][0].resolve().value
        value: Any = self.frame["ADD"][0].resolve()

        if isinstance(to, Identifier):
            to = to.resolve(self.frame._graph)
        if isinstance(to, Literal):
            to = to.value
        if isinstance(to, Query):
            to = self.frame._graph.search(to)
        if isinstance(to, str):
            try:
                to = varmap.resolve(to)
            except: pass
        if isinstance(to, Frame):
            to = [to]

        if isinstance(value, Literal):
            value = value.value
        if isinstance(value, str):
            try:
                value = varmap.resolve(value)
            except: pass
        if isinstance(value, Frame):
            if value ^ "EXE.RETURNING-STATEMENT":
                value = Statement.from_instance(value).run(StatementScope(), varmap)

        for frame in to:
            frame[slot] += value

    def __eq__(self, other):
        if isinstance(other, AddFillerStatement):
            return other.frame["TO"] == self.frame["TO"] and \
                   other.frame["SLOT"] == self.frame["SLOT"] and \
                   self.__eqADD(other)
        return super().__eq__(other)

    def __eqADD(self, other: 'AddFillerStatement') -> bool:
        if other.frame["ADD"] == self.frame["ADD"]:
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
    def instance(cls, graph: Graph, assertion: Union[str, Identifier, Frame, Statement], resolutions: List[Union[str, Identifier, Frame, 'MakeInstanceStatement']]):
        if isinstance(assertion, Statement):
            assertion = assertion.frame
        resolutions = list(map(lambda r: r.frame if isinstance(r, MakeInstanceStatement) else r, resolutions))

        stmt = graph.register("ASSERT-STATEMENT", isa="EXE.ASSERT-STATEMENT", generate_index=True)
        stmt["ASSERTION"] = assertion
        stmt["RESOLUTION"] = resolutions

        return AssertStatement(stmt)

    def assertion(self) -> Statement:
        return Statement.from_instance(self.frame["ASSERTION"].singleton())

    def resolutions(self) -> List['MakeInstanceStatement']:
        return list(map(lambda s: MakeInstanceStatement(s.resolve()), self.frame["RESOLUTION"]))

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
    def instance(cls, graph: Graph, to: Union[str, Identifier, Frame, Query], slot: str, value: Any):
        frame = graph.register("ASSIGNFILLER-STATEMENT", isa="EXE.ASSIGNFILLER-STATEMENT", generate_index=True)
        frame["TO"] = to if not isinstance(to, str) else Literal(to)
        frame["SLOT"] = Literal(slot)
        frame["ASSIGN"] = value

        return AssignFillerStatement(frame)

    def run(self, scope: StatementScope, varmap: VariableMap):
        to: Any = self.frame["TO"][0].resolve()
        slot: str = self.frame["SLOT"][0].resolve().value
        value: Any = self.frame["ASSIGN"][0].resolve()

        if isinstance(to, Identifier):
            to = to.resolve(self.frame._graph)
        if isinstance(to, Literal):
            to = to.value
        if isinstance(to, Query):
            to = self.frame._graph.search(to)
        if isinstance(to, str):
            try:
                to = varmap.resolve(to)
            except: pass
        if isinstance(to, Frame):
            to = [to]

        if isinstance(value, Literal) and isinstance(value.value, str):
            try:
                value = varmap.resolve(value.value)
            except: pass
        if isinstance(value, Frame):
            if value ^ "EXE.RETURNING-STATEMENT":
                value = Statement.from_instance(value).run(StatementScope(), varmap)

        for frame in to:
            frame[slot] = value

    def __eq__(self, other):
        if isinstance(other, AssignFillerStatement):
            return other.frame["TO"] == self.frame["TO"] and \
                   other.frame["SLOT"] == self.frame["SLOT"] and \
                   other.frame["ASSIGN"] == self.frame["ASSIGN"]
        return super().__eq__(other)


class AssignVariableStatement(Statement):

    @classmethod
    def instance(cls, graph: Graph, variable: str, value: Any):
        frame = graph.register("ASSIGNVARIABLE-STATEMENT", isa="EXE.ASSIGNVARIABLE-STATEMENT", generate_index=True)
        frame["TO"] = Literal(variable)
        frame["ASSIGN"] = value

        return AssignVariableStatement(frame)

    def run(self, scope: StatementScope, varmap: VariableMap):
        variable = self.frame["TO"].singleton()
        value = self.frame["ASSIGN"].singleton()
        value = self._resolve(value, scope, varmap)

        Variable.instance(self.frame._graph, variable, value, varmap)

    def _resolve(self, value, scope: StatementScope, varmap: VariableMap):
        if isinstance(value, list):
            return list(map(lambda v: self._resolve(v, scope, varmap), value))
        if isinstance(value, str):
            try:
                return varmap.resolve(value)
            except:
                pass
        if isinstance(value, Statement) and value.frame ^ "EXE.RETURNING-STATEMENT":
            return value.run(StatementScope(), varmap)
        if isinstance(value, Frame) and value ^ "EXE.RETURNING-STATEMENT":
            return Statement.from_instance(value).run(StatementScope(), varmap)

        return value

    def __eq__(self, other):
        if isinstance(other, AssignVariableStatement):
            return self.frame["TO"] == other.frame["TO"] and self.frame["ASSIGN"] == other.frame["ASSIGN"]
        return super().__eq__(other)


class ExistsStatement(Statement):

    @classmethod
    def instance(cls, graph: Graph, query: Query):
        frame = graph.register("EXISTS-STATEMENT", isa="EXE.EXISTS-STATEMENT", generate_index=True)
        frame["FIND"] = query

        return ExistsStatement(frame)

    def run(self, scope: StatementScope, varmap: VariableMap) -> bool:
        query = self.frame["FIND"][0].resolve().value
        results = self.frame._graph._network.search(query)
        return len(results) > 0

    def __eq__(self, other):
        if isinstance(other, ExistsStatement):
            return other.frame["FIND"] == self.frame["FIND"]

        return super().__eq__(other)


class ForEachStatement(Statement):

    @classmethod
    def instance(cls, graph: Graph, query: Query, assign: str, do: Union[Statement, List[Statement]]):
        if isinstance(do, Statement):
            do = [do]
        do = list(map(lambda do: do.frame, do))

        frame = graph.register("FOREACH-STATEMENT", isa="EXE.FOREACH-STATEMENT", generate_index=True)
        frame["FROM"] = query
        frame["ASSIGN"] = Literal(assign)
        frame["DO"] = do

        return ForEachStatement(frame)

    def run(self, scope: StatementScope, varmap: VariableMap):
        query: Query = self.frame["FROM"].singleton()
        variable: str = self.frame["ASSIGN"].singleton()
        do: List[Statement] = list(map(lambda stmt: Statement.from_instance(stmt.resolve()), self.frame["DO"]))

        var: Variable = None
        try:
            var = varmap.find(variable)
        except:
            var = Variable.instance(self.frame._graph, variable, None, varmap)

        for frame in self.frame._graph._network.search(query):
            var.set_value(frame)
            for stmt in do:
                stmt.run(scope, varmap)

    def __eq__(self, other):
        if isinstance(other, ForEachStatement):
            return other.frame["FROM"] == self.frame["FROM"] and \
                   other.frame["ASSIGN"] == self.frame["ASSIGN"] and \
                   list(map(lambda frame: Statement.from_instance(frame.resolve()), other.frame["DO"])) == list(map(lambda frame: Statement.from_instance(frame.resolve()), self.frame["DO"]))

        return super().__eq__(other)


class IsStatement(Statement):

    @classmethod
    def instance(clsg, graph: Graph, domain: Union[str, Identifier, Frame], slot: str, filler: Any):
        frame = graph.register("IS-STATEMENT", isa="EXE.IS-STATEMENT", generate_index=True)
        frame["DOMAIN"] = domain if not isinstance(domain, str) else Literal(domain)
        frame["SLOT"] = Literal(slot)
        frame["FILLER"] = filler

        return IsStatement(frame)

    def run(self, scope: StatementScope, varmap: VariableMap):
        domain = self.frame["DOMAIN"][0].resolve()
        slot: str = self.frame["SLOT"][0].resolve().value
        filler = self.frame["FILLER"][0].resolve()

        if isinstance(domain, Literal):
            domain = domain.value
        if isinstance(domain, str):
            try:
                domain = varmap.resolve(domain)
            except: pass
        if not isinstance(domain, Frame):
            return False  # Typically this means a variable could not be resolved, so it cannot possibly match yet

        if isinstance(filler, Literal):
            filler = filler.value
        if isinstance(filler, str):
            try:
                filler = varmap.resolve(filler)
            except: pass

        return domain[slot] == filler

    def __eq__(self, other):
        if isinstance(other, IsStatement):
            return other.frame["DOMAIN"] == self.frame["DOMAIN"] and \
                   other.frame["SLOT"] == self.frame["SLOT"] and \
                   other.frame["FILLER"] == self.frame["FILLER"]
        return super().__eq__(other)


class MakeInstanceStatement(Statement):

    @classmethod
    def instance(cls, graph: Graph, in_graph: str, of: Union[str, Identifier, Frame], params: List[Any]):
        frame = graph.register("MAKEINSTANCE-STATEMENT", isa="EXE.MAKEINSTANCE-STATEMENT", generate_index=True)
        frame["IN"] = Literal(in_graph)
        frame["OF"] = of
        frame["PARAMS"] = list(map(lambda param: Literal(param) if isinstance(param, str) else param, params))

        return MakeInstanceStatement(frame)

    def run(self, scope: StatementScope, varmap: VariableMap):
        graph: str = self.frame["IN"][0].resolve().value
        of: Frame = self.frame["OF"][0].resolve()
        params: List[Any] = list(map(lambda param: param.resolve().value, self.frame["PARAMS"]))

        instance = self.frame._network[graph].register(of._identifier.name, isa=of, generate_index=True)
        for slot in of:
            slot = of[slot]
            instance[slot._name] = slot

        if len(params) != len(instance["WITH"]):
            raise Exception("Mismatched parameter count when making instance of '" + of.name() + "' with parameters '" + str(params) + "'.")

        params = list(map(lambda param: self._resolve_param(param, varmap), params))

        VariableMap.instance_of(self.frame._graph, of, params, existing=instance)

        return instance

    def __eq__(self, other):
        if isinstance(other, MakeInstanceStatement):
            return other.frame["IN"] == self.frame["IN"] and \
                   other.frame["OF"] == self.frame["OF"] and \
                   other.frame["PARAMS"] == self.frame["PARAMS"]
        return super().__eq__(other)


class MeaningProcedureStatement(Statement):

    @classmethod
    def instance(cls, graph: Graph, calls: str, params: List[Any]):
        frame = graph.register("MP-STATEMENT", isa="EXE.MP-STATEMENT", generate_index=True)
        frame["CALLS"] = Literal(calls)
        frame["PARAMS"] = params

        return MeaningProcedureStatement(frame)

    def run(self, scope: StatementScope, varmap: VariableMap):
        mp: str = self.frame["CALLS"][0].resolve().value

        params = list(map(lambda param: self._resolve_param(param, varmap), self.frame["PARAMS"]))

        result = MPRegistry.run(mp, self.frame._graph._network, *params, statement=self, varmap=varmap)
        return result

    def __eq__(self, other):
        if isinstance(other, MeaningProcedureStatement):
            return other.frame["CALLS"] == self.frame["CALLS"] and \
                   other.frame["PARAMS"] == self.frame["PARAMS"]
        return super().__eq__(other)


class OutputXMRStatement(Statement):

    @classmethod
    def instance(cls, graph: Graph, template: Union[str, Graph, 'OutputXMRTemplate'], params: List[Any], agent: Union[str, Identifier, Frame]):
        from backend.models.output import OutputXMRTemplate

        frame = graph.register("OUTPUTXMR-STATEMENT", isa="EXE.OUTPUTXMR-STATEMENT", generate_index=True)

        if isinstance(template, Graph):
            template = OutputXMRTemplate(template)
        if isinstance(template, OutputXMRTemplate):
            template = template.name()

        frame["TEMPLATE"] = Literal(template)
        frame["PARAMS"] = params
        frame["AGENT"] = agent

        return OutputXMRStatement(frame)

    def template(self) -> 'OutputXMRTemplate':
        from backend.models.output import OutputXMRTemplate

        return OutputXMRTemplate.lookup(self.frame._graph._network, self.frame["TEMPLATE"].singleton())

    def params(self) -> List[Any]:
        return list(map(lambda param: param._value, self.frame["PARAMS"]))

    def agent(self) -> Frame:
        return self.frame["AGENT"].singleton()

    def run(self, scope: StatementScope, varmap: VariableMap) -> 'OutputXMR':
        agent = self.agent()
        network = self.frame._graph._network
        graph = network["OUTPUTS"]

        params = self.params()
        params = list(map(lambda param: self._resolve_param(param, varmap), params))

        output = self.template().create(network, graph, params)
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