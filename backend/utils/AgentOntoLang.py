from backend.models.agenda import Agenda, Goal, Plan, Step, Trigger
from backend.models.bootstrap import BootstrapTriple
from backend.models.effectors import Capability
from backend.models.mps import AgentMethod, MPRegistry, OutputMethod
from backend.models.output import OutputXMRTemplate
from backend.models.statement import AddFillerStatement, AssertStatement, AssignFillerStatement, AssignVariableStatement, ExistsStatement, ExpectationStatement, ForEachStatement, IsStatement, MakeInstanceStatement, MeaningProcedureStatement, OutputXMRStatement, Statement, TransientFrameStatement
from backend.models.xmr import XMR
from lark import Tree
from ontograph.Frame import Frame
from ontograph.Index import Identifier
from ontograph.Query import Query, SearchComparator
from ontograph.OntoLang import AppendOntoLangProcessor, AssignOntoLangProcessor, OntoLang, OntoLangProcessor, OntoLangTransformer
from ontograph.Space import Space
from typing import Any, List, Tuple, Type, Union


class AgentOntoLang(OntoLang):

    def __init__(self):
        super().__init__()
        self.resources.insert(0, ("backend.resources", "ontoagent.lark"))

    def get_starting_rule(self):
        return "ontoagent"

    def get_transformer_type(self):
        return AgentOntoLangTransformer


class AgentOntoLangTransformer(OntoLangTransformer):

    def ontoagent(self, matches: Union[OntoLangProcessor, List[OntoLangProcessor]]) -> List[OntoLangProcessor]:
        processors = []
        for match in matches:
            if isinstance(match, list):
                processors.extend(match)
            else:
                processors.append(match)
        return processors

    def ontoagent_process(self, matches: List[OntoLangProcessor]) -> OntoLangProcessor:
        return matches[0]

    def ontoagent_process_add_trigger(self, matches: List[Tree]) -> 'OntoAgentProcessorAddTrigger':
        agenda: Identifier = matches[3]
        definition: Identifier = matches[5]
        query: SearchComparator = matches[7]

        return OntoAgentProcessorAddTrigger(agenda, definition, Query().search(query))

    def ontoagent_process_define_goal(self, matches: List['OntoAgentProcessorDefineGoal']) -> 'OntoAgentProcessorDefineGoal':
        return matches[1]

    def ontoagent_process_define_output_xmr_template(self, matches):
        #from backend.models.bootstrap import BootstrapDeclareKnowledge, BootstrapDefineOutputXMRTemplate

        name = str(matches[1])
        params = matches[2]
        type = matches[5]
        capability = matches[6]
        root = None
        include = []

        if isinstance(matches[7], Identifier):
            root = matches[7]
            include = matches[8]
        else:
            include = matches[7]

        return OntoAgentProcessorDefineOutputXMRTemplate(name, type, capability, params, root, include)

    def ontoagent_process_register_mp(self, matches: List[Tree]) -> 'OntoAgentProcessorRegisterMP':
        mp: Type[Union[AgentMethod, OutputMethod]] = matches[2]
        name: str = None if len(matches) == 3 else str(matches[4])

        return OntoAgentProcessorRegisterMP(mp, name=name)

    def add_filler_statement(self, matches):
        domain = matches[0]
        slot = str(matches[1])
        filler = matches[2]

        return AddFillerStatement.instance(Space("EXE"), domain, slot, filler)

    def agent_method(self, matches) -> Type[Union[AgentMethod, OutputMethod]]:
        index = matches[0].rfind(".")
        module = matches[0][0:index]
        clazz = matches[0][index + 1:]

        import sys
        __import__(module)
        return getattr(sys.modules[module], clazz)

    def argument(self, matches):
        return str(matches[0])

    def arguments(self, matches):
        return matches

    def assert_statement(self, matches):
        assertion = matches[1]
        resolutions = matches[5]

        return AssertStatement.instance(Space("EXE"), assertion, resolutions)

    def assertion(self, matches):
        return matches[0]

    def assign_filler_statement(self, matches):
        domain = matches[0]
        slot = str(matches[1])
        filler = matches[2]

        return AssignFillerStatement.instance(Space("EXE"), domain, slot, filler)

    def assign_variable_statement(self, matches):
        variable = str(matches[0])
        value = matches[1]

        return AssignVariableStatement.instance(Space("EXE"), variable, value)

    def boolean_statement(self, matches: List[Statement]) -> Statement:
        return matches[0]

    def condition(self, matches):
        from backend.models.agenda import Condition

        if isinstance(matches[1], Condition.On):
            on = matches[1]
            statements = []
            logic = Condition.Logic.AND.value
        else:
            on = None
            statements = matches[1][1]
            logic = matches[1][0]

        status = matches[3]

        return Condition.build(Space("EXE"), statements, status, logic=logic, on=on)

    def condition_and(self, matches):
        from backend.models.agenda import Condition
        from backend.models.agenda import Statement

        return Condition.Logic.AND, list(filter(lambda match: isinstance(match, Statement), matches))

    def condition_or(self, matches):
        from backend.models.agenda import Condition
        from backend.models.agenda import Statement

        return Condition.Logic.OR, list(filter(lambda match: isinstance(match, Statement), matches))

    def condition_nand(self, matches):
        from backend.models.agenda import Condition
        from backend.models.agenda import Statement

        return Condition.Logic.NAND, list(filter(lambda match: isinstance(match, Statement), matches))

    def condition_nor(self, matches):
        from backend.models.agenda import Condition
        from backend.models.agenda import Statement

        return Condition.Logic.NOR, list(filter(lambda match: isinstance(match, Statement), matches))

    def condition_not(self, matches):
        from backend.models.agenda import Condition
        from backend.models.agenda import Statement

        return Condition.Logic.NOT, list(filter(lambda match: isinstance(match, Statement), matches))

    def condition_on(self, matches):
        from backend.models.agenda import Condition

        return Condition.On[str(matches[0])]

    def exists_statement(self, matches):
        return ExistsStatement.instance(Space("EXE"), Query().search(matches[1]))

    def expectation_statement(self, matches):
        return ExpectationStatement.instance(Space("EXE"), matches[1])

    def foreach_statement(self, matches):
        return ForEachStatement.instance(Space("EXE"), Query().search(matches[4]), str(matches[2]), matches[5:])

    def goal(self, matches: List[Tree]) -> 'OntoAgentProcessorDefineGoal':
        from backend.models.agenda import Condition, Effect, Goal, Plan
        from ontograph.Space import Space

        name = str(matches[0])
        variables = matches[1]
        space: str = matches[5]

        priority = list(map(lambda m: m[1], filter(lambda m: isinstance(m, tuple) and m[0] == "priority", matches)))
        resources = list(map(lambda m: m[1], filter(lambda m: isinstance(m, tuple) and m[0] == "resources", matches)))

        priority = 0.5 if len(priority) != 1 else priority[0]
        resources = 0.5 if len(resources) != 1 else resources[0]

        if isinstance(priority, MeaningProcedureStatement):
            priority = priority.frame
        if isinstance(resources, MeaningProcedureStatement):
            resources = resources.frame

        plan = list(filter(lambda match: isinstance(match, Plan), matches))
        conditions = list(filter(lambda match: isinstance(match, Condition), matches))
        effects = list(filter(lambda match: isinstance(match, Effect), matches))

        condition_order = 1
        for c in conditions:
            c.frame["ORDER"] = condition_order
            condition_order += 1

        return OntoAgentProcessorDefineGoal(Goal.define(Space(space), name, priority, resources, plan, conditions, variables, effects))

    def goal_status(self, matches):
        from backend.models.agenda import Goal
        if str(matches[0]).upper() == "PENDING":
            return Goal.Status.PENDING
        if str(matches[0]).upper() == "ACTIVE":
            return Goal.Status.ACTIVE
        if str(matches[0]).upper() == "ABANDONED":
            return Goal.Status.ABANDONED
        if str(matches[0]).upper() == "SATISFIED":
            return Goal.Status.SATISFIED

    def impasse(self, matches) -> MakeInstanceStatement:
        return matches[0]

    def impasses(self, matches) -> List[MakeInstanceStatement]:
        return list(filter(lambda m: isinstance(m, MakeInstanceStatement), matches))

    def is_statement(self, matches) -> IsStatement:
        domain = matches[0]
        slot = str(matches[1])
        filler = matches[2]

        return IsStatement.instance(Space("EXE"), domain, slot, filler)

    def list(self, matches):
        return [matches]

    def list_element(self, matches):
        return matches[0]

    def make_instance_statement(self, matches) -> MakeInstanceStatement:
        in_graph = str(matches[0])
        of = matches[1]
        params = matches[2]

        return MakeInstanceStatement.instance(Space("EXE"), in_graph, of, params)

    def mp_statement(self, matches) -> MeaningProcedureStatement:
        params = matches[2]
        return MeaningProcedureStatement.instance(Space("EXE"), matches[1], params)

    def ontoagent_triple(self, matches) -> Tuple:
        slot = str(matches[0])
        if len(matches) == 2:
            facet = None
            filler = matches[1]
        else:
            facet = matches[1]
            filler = matches[2]

        return slot, facet, filler

    def output_argument(self, matches):
        return matches[0]

    def output_arguments(self, matches):
        return matches

    def output_statement(self, matches):
        template = matches[1]
        params = matches[2]
        agent = matches[4]

        return OutputXMRStatement.instance(Space("EXE"), template, params, agent)

    def output_xmr_template_include(self, matches) -> List[AssignOntoLangProcessor]:
        return matches[1:]

    def output_xmr_template_requires(self, matches) -> Identifier:
        return matches[1]

    def output_xmr_template_root(self, matches) -> Identifier:
        return matches[1]

    def output_xmr_template_type(self, matches) -> XMR.Type:
        return {
            "PHYSICAL": XMR.Type.ACTION,
            "MENTAL": XMR.Type.MENTAL,
            "VERBAL": XMR.Type.LANGUAGE
        }[matches[1]]

    def plan(self, matches) -> Plan:
        name = matches[1]
        select, negate = matches[2]
        steps = matches[3:]

        for i, v in enumerate(steps):
            v.frame["INDEX"] = i + 1

        return Plan.build(Space("EXE"), name, select, steps, negate=negate)

    def plan_do(self, matches):
        from backend.models.agenda import Step
        perform = matches[1]

        if str(perform) == "IDLE":
            perform = Step.IDLE

        return perform

    def plan_selection(self, matches):
        from backend.models.agenda import Plan
        select = matches[1]
        negate = False

        if str(select) == "DEFAULT":
            select = Plan.DEFAULT
        elif str(select) == "IF":
            if matches[2] == "NOT":
                select = matches[3]
                negate = True
            else:
                select = matches[2]

        return select, negate

    def plan_step(self, matches):
        return Step.build(Space("EXE"), -1, matches[1:])

    def priority(self, matches: List[Any]) -> Tuple[str, Union[float, MeaningProcedureStatement]]:
        return ("priority", matches[1])

    def resources(self, matches: List[Any]) -> Tuple[str, Union[float, MeaningProcedureStatement]]:
        return ("resources", matches[1])

    def statement(self, matches: List[Statement]) -> Statement:
        return matches[0]

    def statement_instance(self, matches):
        if isinstance(matches[0], Identifier):
            if matches[0].id == "SELF":
                return Frame("@SELF.ROBOT.1")
            return matches[0]
        if str(matches[0]) == "SELF":
            return Frame("@SELF.ROBOT.1")

        return matches[0]

    def transient_statement(self, matches):
        properties = list(filter(lambda m: isinstance(m, tuple), matches))
        properties = list(map(lambda p: BootstrapTriple(p[0], p[2], facet=p[1]), properties))

        return TransientFrameStatement.instance(Space("EXE"), properties)


class OntoAgentProcessorAddTrigger(OntoLangProcessor):

    def __init__(self, agenda: Union[str, Identifier, Frame, Agenda], definition: Union[str, Identifier, Frame, Goal], query: Query):
        self.agenda = agenda
        self.definition = definition
        self.query = query

    def run(self):
        agenda = self.agenda
        if isinstance(agenda, str):
            agenda = Frame(agenda)
        if isinstance(agenda, Identifier):
            agenda = Frame(agenda.id)
        if isinstance(agenda, Agenda):
            agenda = agenda.frame

        trigger = Trigger.build(agenda.space(), self.query, self.definition)
        Agenda(agenda).add_trigger(trigger)

    def __eq__(self, other):
        if isinstance(other, OntoAgentProcessorAddTrigger):
            return self.agenda == other.agenda and \
                    self.definition == other.definition and \
                    self.query == other.query
        return super().__eq__(other)


class OntoAgentProcessorDefineGoal(OntoLangProcessor):

    def __init__(self, goal: Goal):
        self.goal = goal

    def run(self):
        return self.goal


class OntoAgentProcessorDefineOutputXMRTemplate(OntoLangProcessor):

    def __init__(self, name: str, type: XMR.Type, capability: Union[str, Identifier, Frame, Capability], params: List[str], root: Union[str, Identifier, Frame, None], frames: List[AssignOntoLangProcessor]):
        self.name = name
        self.type = type
        self.capability = capability
        self.params = params
        self.root = root
        self.frames = frames

    def run(self):
        template = OutputXMRTemplate.build(self.name, self.type, self.capability, self.params)
        if self.root is not None:
            r = self.root
            if isinstance(r, Frame):
                r = r.id
            if isinstance(r, Identifier):
                r = r.id

            r = r.replace("@OUT", "@" + template.space.name)

            r = Frame(r)
            template.set_root(r)

        for frame in self.frames:
            if isinstance(frame.frame, str):
                frame.frame = frame.frame.replace("@OUT", "@" + template.space.name)
            else:
                frame.frame.id = frame.frame.id.replace("@OUT", "@" + template.space.name)

            for instruction in frame.instructions:
                i: AppendOntoLangProcessor = instruction

                if isinstance(i.frame, str):
                    i.frame = i.frame.replace("@OUT", "@" + template.space.name)
                else:
                    i.frame.id = i.frame.id.replace("@OUT", "@" + template.space.name)

                if isinstance(i.filler, Identifier):
                    i.filler.id = i.filler.id.replace("@OUT", "@" + template.space.name)

        for frame in self.frames:
            frame.run()

    def __eq__(self, other):
        if isinstance(other, OntoAgentProcessorDefineOutputXMRTemplate):
            return self.name == other.name and \
                self.type == other.type and \
                self.capability == other.capability and \
                self.params == other.params and \
                self.root == other.root and \
                self.frames == other.frames
        return super().__eq__(other)


class OntoAgentProcessorRegisterMP(OntoLangProcessor):

    def __init__(self, mp: Type[Union[AgentMethod, OutputMethod]], name: str=None):
        self.mp = mp
        self.name = name

    def run(self):
        name = self.name if self.name is not None else self.mp.__name__
        MPRegistry.register(self.mp, name)

    def __eq__(self, other):
        if isinstance(other, OntoAgentProcessorRegisterMP):
            return self.mp.__name__ == other.mp.__name__ and self.name == other.name
        return super().__eq__(other)