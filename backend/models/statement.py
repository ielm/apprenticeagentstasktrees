# from backend.models.effectors import Callback, Capability
from backend.models.graph import Filler, Frame, Graph, Identifier, Literal
from backend.models.mps import MPRegistry
from backend.models.query import Query
from typing import Any, List, Union

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from backend.models.effectors import Capability


class Variable(object):

    @classmethod
    def instance(cls, graph: Graph, name: str, value: Any, varmap: 'VariableMap', assign: bool=True):
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

        for var in self.frame["_WITH"]:
            var = var.resolve()
            if Variable(var).name() == name:
                raise Exception("Variable '" + name + "' is already mapped.")

        self.frame["_WITH"] += variable

    def resolve(self, name: str) -> Any:
        return self.find(name).value()

    def find(self, name: str) -> Variable:
        for var in self.frame["_WITH"]:
            var = Variable(var.resolve())
            if var.name() == name:
                return var
        raise Exception("Variable '" + name + "' is not defined in this mapping.")

    def __eq__(self, other):
        if isinstance(other, VariableMap):
            return self.frame == other.frame
        if isinstance(other, Frame):
            return self.frame == other
        return super().__eq__(other)


class StatementHierarchy(object):

    def __init__(self):
        self._cache = None

    def __call__(self, *args, **kwargs) -> Graph:
        if self._cache is None:
            self._cache = self.build()
        return self._cache

    def build(self) -> Graph:
        '''
        STATEMENT (hierarchy)
            RETURNING-STATEMENT
                BOOLEAN-STATEMENT
                    EXISTS-STATEMENT
                    IS-STATEMENT
                MAKEINSTANCE-STATEMENT
                QUERY-STATEMENT
                SLOT-STATEMENT
                MP-STATEMENT
            NONRETURNING-STATEMENT
                FOREACH-STATEMENT
                ADDFILLER-STATEMENT
                ASSIGNFILLER-STATEMENT
        '''

        hierarchy = Graph("EXE")
        hierarchy.register("STATEMENT")
        hierarchy.register("RETURNING-STATEMENT", isa="EXE.STATEMENT")
        hierarchy.register("BOOLEAN-STATEMENT", isa="EXE.RETURNING-STATEMENT")
        hierarchy.register("EXISTS-STATEMENT", isa="EXE.BOOLEAN-STATEMENT")
        hierarchy.register("IS-STATEMENT", isa="EXE.BOOLEAN-STATEMENT")
        hierarchy.register("MAKEINSTANCE-STATEMENT", isa="EXE.RETURNING-STATEMENT")
        hierarchy.register("QUERY-STATEMENT", isa="EXE.RETURNING-STATEMENT")
        hierarchy.register("SLOT-STATEMENT", isa="EXE.RETURNING-STATEMENT")
        hierarchy.register("MP-STATEMENT", isa="EXE.RETURNING-STATEMENT")
        hierarchy.register("CAPABILITY-STATEMENT", isa="EXE.RETURNING-STATEMENT")
        hierarchy.register("NONRETURNING-STATEMENT", isa="EXE.STATEMENT")
        hierarchy.register("FOREACH-STATEMENT", isa="EXE.NONRETURNING-STATEMENT")
        hierarchy.register("ADDFILLER-STATEMENT", isa="EXE.NONRETURNING-STATEMENT")
        hierarchy.register("ASSIGNFILLER-STATEMENT", isa="EXE.NONRETURNING-STATEMENT")

        hierarchy["STATEMENT"]["CLASSMAP"] = Literal(Statement)
        hierarchy["ADDFILLER-STATEMENT"]["CLASSMAP"] = Literal(AddFillerStatement)
        hierarchy["ASSIGNFILLER-STATEMENT"]["CLASSMAP"] = Literal(AssignFillerStatement)
        hierarchy["EXISTS-STATEMENT"]["CLASSMAP"] = Literal(ExistsStatement)
        hierarchy["FOREACH-STATEMENT"]["CLASSMAP"] = Literal(ForEachStatement)
        hierarchy["IS-STATEMENT"]["CLASSMAP"] = Literal(IsStatement)
        hierarchy["MAKEINSTANCE-STATEMENT"]["CLASSMAP"] = Literal(MakeInstanceStatement)
        hierarchy["MP-STATEMENT"]["CLASSMAP"] = Literal(MeaningProcedureStatement)
        hierarchy["CAPABILITY-STATEMENT"]["CLASSMAP"] = Literal(CapabilityStatement)

        return hierarchy

    def concept_for_statement(self, statement: 'Statement'):
        root: Frame = self()["STATEMENT"]
        for frame in self():
            if frame ^ root and frame["CLASSMAP"] == statement.__class__:
                return frame
        raise Exception("Unknown statement type: '" + str(statement.__class__) + "'.")


class Statement(object):

    @classmethod
    def hierarchy(cls):
        return StatementHierarchy().build()

    @classmethod
    def from_instance(cls, frame: Frame) -> 'Statement':
        definition = frame.parents()[0].resolve(frame._graph, network=frame._network)
        return definition["CLASSMAP"][0].resolve().value(frame)

    def __init__(self, frame: Frame):
        self.frame = frame

    def run(self, varmap: VariableMap) -> Any:
        raise Exception("Statement.run(varmap) must be implemented.")

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

    def capabilities(self) -> List['Capability']:
        return []

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

    def run(self, varmap: VariableMap):
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
                value = Statement.from_instance(value).run(varmap)

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


class AssignFillerStatement(Statement):

    @classmethod
    def instance(cls, graph: Graph, to: Union[str, Identifier, Frame, Query], slot: str, value: Any):
        frame = graph.register("ASSIGNFILLER-STATEMENT", isa="EXE.ASSIGNFILLER-STATEMENT", generate_index=True)
        frame["TO"] = to if not isinstance(to, str) else Literal(to)
        frame["SLOT"] = Literal(slot)
        frame["ASSIGN"] = value

        return AssignFillerStatement(frame)

    def run(self, varmap: VariableMap):
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

        if isinstance(value, Literal):
            value = value.value
        if isinstance(value, str):
            try:
                value = varmap.resolve(value)
            except: pass
        if isinstance(value, Frame):
            if value ^ "EXE.RETURNING-STATEMENT":
                value = Statement.from_instance(value).run(varmap)

        for frame in to:
            frame[slot] = value

    def __eq__(self, other):
        if isinstance(other, AssignFillerStatement):
            return other.frame["TO"] == self.frame["TO"] and \
                   other.frame["SLOT"] == self.frame["SLOT"] and \
                   other.frame["ASSIGN"] == self.frame["ASSIGN"]
        return super().__eq__(other)


class ExistsStatement(Statement):

    @classmethod
    def instance(cls, graph: Graph, query: Query):
        frame = graph.register("EXISTS-STATEMENT", isa="EXE.EXISTS-STATEMENT", generate_index=True)
        frame["FIND"] = query

        return ExistsStatement(frame)

    def run(self, varmap: VariableMap) -> bool:
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

    def run(self, varmap: VariableMap):
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
                stmt.run(varmap)

    def capabilities(self) -> List['Capability']:
        do: List[Statement] = list(map(lambda stmt: Statement.from_instance(stmt.resolve()), self.frame["DO"]))
        capabilities = []
        for stmt in do:
            capabilities.extend(stmt.capabilities())
        return capabilities

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

    def run(self, varmap: VariableMap):
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

    def run(self, varmap: VariableMap):
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

    def run(self, varmap: VariableMap):
        mp: str = self.frame["CALLS"][0].resolve().value

        params = list(map(lambda param: self._resolve_param(param, varmap), self.frame["PARAMS"]))
        params.insert(0, self)

        result = MPRegistry.run(mp, *params)
        return result

    def __eq__(self, other):
        if isinstance(other, MeaningProcedureStatement):
            return other.frame["CALLS"] == self.frame["CALLS"] and \
                   other.frame["PARAMS"] == self.frame["PARAMS"]
        return super().__eq__(other)


class CapabilityStatement(Statement):

    @classmethod
    def instance(cls, graph: Graph, capability: Union[str, Identifier, Frame, 'Capability'], callback: List[Union[str, Identifier, Frame, Statement]], params: List[Any]) -> 'CapabilityStatement':
        from backend.models.effectors import Capability

        frame = graph.register("CAPABILITY-STATEMENT", isa="EXE.CAPABILITY-STATEMENT", generate_index=True)

        if isinstance(capability, str):
            capability = Identifier.parse(capability)
        if isinstance(capability, Capability):
            capability = capability.frame
        if isinstance(capability, Frame):
            capability = capability._identifier
        frame["CAPABILITY"] = capability

        for cb in callback:
            if isinstance(cb, str):
                cb = Identifier.parse(cb)
            if isinstance(cb, Statement):
                cb = cb.frame
            if isinstance(cb, Frame):
                cb = cb._identifier
            frame["CALLBACK"] += cb

        frame["PARAMS"] = params

        return CapabilityStatement(frame)

    def run(self, varmap: VariableMap):
        from backend.models.effectors import Capability

        capability: Capability = Capability(self.frame["CAPABILITY"].singleton())

        params = list(map(lambda param: self._resolve_param(param, varmap), self.frame["PARAMS"]))
        params.insert(0, self)

        result = capability.run(*params, graph=self.frame._graph, callbacks=self.callbacks(), varmap=varmap)
        return result

    def callbacks(self) -> List[Statement]:
        return list(map(lambda cb: Statement.from_instance(cb.resolve()), self.frame["CALLBACK"]))

    def capabilities(self) -> List['Capability']:
        from backend.models.effectors import Capability

        return [Capability(self.frame["CAPABILITY"].singleton())]

    def __eq__(self, other):
        if isinstance(other, CapabilityStatement):
            other = other.frame

        if isinstance(other, Frame):
            return self.frame["CAPABILITY"] == other["CAPABILITY"] and \
                    list(map(lambda frame: Statement.from_instance(frame.resolve()), other["CALLBACK"])) == list(map(lambda frame: Statement.from_instance(frame.resolve()), self.frame["CALLBACK"])) and \
                    self.frame["PARAMS"] == other["PARAMS"]
        else:
            return super().__eq__(other)