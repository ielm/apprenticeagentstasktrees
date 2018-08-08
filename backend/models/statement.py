from backend.models.graph import Frame, Graph, Identifier, Literal
from backend.models.query import Query
from typing import Any, List, Union


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
        hierarchy.register("NONRETURNING-STATEMENT", isa="EXE.STATEMENT")
        hierarchy.register("FOREACH-STATEMENT", isa="EXE.NONRETURNING-STATEMENT")
        hierarchy.register("ADDFILLER-STATEMENT", isa="EXE.NONRETURNING-STATEMENT")
        hierarchy.register("ASSIGNFILLER-STATEMENT", isa="EXE.NONRETURNING-STATEMENT")

        hierarchy["STATEMENT"]["CLASSMAP"] = Literal(Statement)
        hierarchy["ADDFILLER-STATEMENT"]["CLASSMAP"] = Literal(AddFillerStatement)
        hierarchy["EXISTS-STATEMENT"]["CLASSMAP"] = Literal(ExistsStatement)
        hierarchy["FOREACH-STATEMENT"]["CLASSMAP"] = Literal(ForEachStatement)
        hierarchy["MAKEINSTANCE-STATEMENT"]["CLASSMAP"] = Literal(MakeInstanceStatement)

        return hierarchy


class Statement(object):

    hierarchy = StatementHierarchy()

    @classmethod
    def from_instance(cls, frame: Frame) -> 'Statement':
        definition = frame.parents()[0].resolve(frame._graph, network=frame._network)
        return definition["CLASSMAP"][0].resolve().value(frame)

    def __init__(self, frame: Frame):
        self.frame = frame

    def run(self, varmap: VariableMap) -> Any:
        raise Exception("Statement.run(varmap) must be implemented.")


class AddFillerStatement(Statement):

    @classmethod
    def instance(cls, graph: Graph, to: Union[Identifier, Frame, Query], slot: str, value: Any):
        frame = graph.register("ADDFILLER-STATEMENT", isa="EXE.ADDFILLER-STATEMENT", generate_index=True)
        frame["TO"] = to
        frame["SLOT"] = slot
        frame["ADD"] = value

        return AddFillerStatement(frame)

    def run(self, varmap: VariableMap):
        to: Any = self.frame["TO"][0].resolve()
        slot: str = self.frame["SLOT"][0].resolve().value
        value: Any = self.frame["ADD"][0].resolve()

        if isinstance(to, Identifier):
            to = to.resolve(self.frame._graph)
        if isinstance(to, Frame):
            to = [to]
        if isinstance(to, Literal):
            to = to.value
        if isinstance(to, Query):
            to = self.frame._graph.search(to)

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


class ExistsStatement(Statement):

    @classmethod
    def instance(cls, graph: Graph, query: Query):
        frame = graph.register("EXISTS-STATEMENT", isa="EXE.EXISTS-STATEMENT", generate_index=True)
        frame["FIND"] = query

        return ExistsStatement(frame)

    def run(self, varmap: VariableMap) -> bool:
        query = self.frame["FIND"][0].resolve().value
        results = self.frame._graph.search(query)
        return len(results) > 0


class ForEachStatement(Statement):

    @classmethod
    def instance(cls, graph: Graph, query: Query, assign: str, do: List[Statement]):
        frame = graph.register("FOREACH-STATEMENT", isa="EXE.FOREACH-STATEMENT", generate_index=True)
        frame["FROM"] = query
        frame["ASSIGN"] = Literal(assign)
        frame["DO"] = list(map(lambda stmt: stmt.frame, do))

        return ForEachStatement(frame)

    def run(self, varmap: VariableMap):
        query: Query = self.frame["FROM"][0].resolve().value
        variable: str = self.frame["ASSIGN"][0].resolve().value
        do: List[Statement] = list(map(lambda stmt: Statement.from_instance(stmt.resolve()), self.frame["DO"]))

        var: Variable = None
        try:
            varmap.find(variable)
        except:
            var = Variable.instance(self.frame._graph, variable, None, varmap)

        for frame in self.frame._graph.search(query):
            var.set_value(frame)
            for stmt in do:
                stmt.run(varmap)


class MakeInstanceStatement(Statement):

    @classmethod
    def instance(cls, graph: Graph, of: Union[str, Identifier, Frame], params: List[Any]):
        frame = graph.register("MAKEINSTANCE-STATEMENT", isa="EXE.MAKEINSTANCE-STATEMENT", generate_index=True)
        frame["OF"] = of
        frame["PARAMS"] = params

        return MakeInstanceStatement(frame)

    def run(self, varmap: VariableMap):
        of: Frame = self.frame["OF"][0].resolve()
        params: List[Any] = list(map(lambda param: param.resolve().value, self.frame["PARAMS"]))

        instance = self.frame._graph.register(of.name(), isa=of, generate_index=True)
        for slot in of:
            slot = of[slot]
            instance[slot._name] = slot

        if len(params) != len(instance["WITH"]):
            raise Exception("Mismatched parameter count when making instance of '" + of.name() + "' with parameters '" + str(params) + "'.")

        VariableMap.instance_of(self.frame._graph, of, params, existing=instance)

        return instance