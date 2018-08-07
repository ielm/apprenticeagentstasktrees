from backend.models.graph import Frame, Graph, Identifier, Literal
from typing import Any, List, Union


class Variable(object):

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

    def varmap(self) -> 'VariableMap':
        if "FROM" in self.frame:
            return VariableMap(self.frame["FROM"][0].resolve())
        raise Exception("Variable '" + self.name() + "' has no varmap.")


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
        for var in self.frame["_WITH"]:
            var = Variable(var.resolve())
            if var.name() == name:
                return var.value()
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

        return hierarchy


class Statement(object):

    hierarchy = StatementHierarchy()

    @classmethod
    def from_instance(cls, frame: Frame) -> 'Statement':
        definition = frame.parents()[0].resolve(frame._graph)
        return definition["CLASSMAP"][0].resolve().value(frame)

    def __init__(self, frame: Frame):
        self.frame = frame

    def run(self, varmap: VariableMap) -> Any:
        raise Exception("Statement.run(varmap) must be implemented.")


