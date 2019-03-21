from backend.agent import Agent
from backend.models.agenda import Decision, Expectation, Goal, Plan, Step, Trigger
from backend.models.effectors import Callback, Capability, Effector
from backend.models.xmr import XMR
from backend.utils.AgentLogger import CachedAgentLogger
from ontograph.Frame import Frame


class IIDEAConverter(object):

    @classmethod
    def io(cls, agent: Agent):
        from datetime import datetime

        payload = []

        # 1) Gather all of the inputs and outputs
        payload.extend(agent.inputs)
        payload.extend(agent.outputs)

        # 2) Map them to the correct XMR objects
        payload = list(map(lambda frame: XMR.from_instance(frame), payload))

        # 3) Sort by timestamp
        payload = sorted(payload, key=lambda xmr: xmr.timestamp())

        # 4) Map them to simple dictionaries
        def source(xmr: XMR) -> str:
            if xmr.source() is not None:
                return xmr.source().id
            if xmr.signal() == XMR.Signal.INPUT:
                return "ONT.HUMAN"
            return "SELF.ROBOT.1"

        payload = list(map(lambda xmr: {
            "type": xmr.type().value,
            "timestamp": datetime.utcfromtimestamp(xmr.timestamp()).strftime('%H:%M:%S'),
            "source": source(xmr),
            "rendered": xmr.render(),
            "id": xmr.frame.id,
            "graph": xmr.graph().name
        }, payload))

        return payload

    @classmethod
    def inputs(cls, agent: Agent):
        return list(map(lambda input: IIDEAConverter.convert_input(input), agent.identity["HAS-INPUT"]))

    @classmethod
    def convert_input(cls, input: Frame):
        status = XMR(input).status().value.lower()

        return {
            "name": input["REFERS-TO-GRAPH"][0],
            "status": status
        }

    @classmethod
    def agenda(cls, agent: Agent):
        return list(map(lambda goal: IIDEAConverter.convert_goal(agent, goal), agent.identity["HAS-GOAL"]))

    @classmethod
    def convert_goal(cls, agent: Agent, goal: Frame):
        goal = Goal(goal)

        return {
            "name": goal.name(),
            "id": goal.frame.id,
            "pending": goal.is_pending(),
            "active": goal.is_active(),
            "satisfied": goal.is_satisfied(),
            "abandoned": goal.is_abandoned(),
            "plan": list(map(lambda plan: IIDEAConverter.convert_plan(agent, plan, goal), goal.frame["PLAN"])),
            "params": list(map(lambda variable: {"var": variable, "value": IIDEAConverter.convert_value(goal.resolve(variable))}, goal.variables()))
        }

    @classmethod
    def convert_value(cls, value):
        if isinstance(value, Frame):
            return value.id
        return value

    @classmethod
    def convert_plan(cls, agent: Agent, plan: Frame, goal: Goal):
        plan = Plan(plan)

        return {
            "name": plan.name(),
            "selected": plan in agent.agenda().plan() and goal.is_active(),
            "steps": list(map(lambda step: IIDEAConverter.convert_step(agent, step), plan.steps()))
        }

    @classmethod
    def convert_step(cls, agent: Agent, step: Step):
        next = False
        blocked = False

        decisions = list(filter(lambda d: d.step() == step, agent.decisions()))
        if len(decisions) == 1:
            if decisions[0].status() == Decision.Status.BLOCKED:
                blocked = True
            if decisions[0].status() == Decision.Status.PENDING or \
                decisions[0].status() == Decision.Status.SELECTED or \
                decisions[0].status() == Decision.Status.EXECUTING:
                next = True

        return {
            "name": "Step " + str(step.index()),
            "next": next,
            "blocked": blocked,
            "finished": step.is_finished()
        }

    @classmethod
    def decisions(cls, agent: Agent):
        return list(map(lambda d: IIDEAConverter.convert_decision(agent, d), agent.decisions()))

    @classmethod
    def convert_decision(cls, agent: Agent, decision: Decision):
        return {
            "id": decision.frame.id,
            "goal": decision.goal().name(),
            "plan": decision.plan().name(),
            "step": "Step " + str(decision.step().index()),
            "outputs": list(map(lambda output: IIDEAConverter.convert_output(output), decision.outputs())),
            "priority": decision.priority(),
            "cost": decision.cost(),
            "requires": list(map(lambda required: required.frame.id, decision.requires())),
            "status": decision.status().name,
            "effectors": list(map(lambda effector: effector.frame.id, decision.effectors())),
            "callbacks": list(map(lambda callback: callback.frame.id, decision.callbacks())),
            "impasses": list(map(lambda impasse: impasse.frame.id, decision.impasses())),
            "expectations": list(map(lambda expectation: IIDEAConverter.convert_expectation(expectation), decision.expectations()))
        }

    @classmethod
    def convert_output(cls, output: XMR):
        return {
            "frame": output.frame.id,
            "graph": output.graph().name,
            "status": output.status().name
        }

    @classmethod
    def convert_expectation(cls, expectation: Expectation):
        from backend.models.statement import ExistsStatement, IsStatement, MeaningProcedureStatement

        condition = expectation.condition()
        if isinstance(condition, IsStatement):
            condition = str(condition.frame["DOMAIN"].singleton()) + "[" + condition.frame["SLOT"].singleton() + "] == " + str(condition.frame["FILLER"].singleton())
        elif isinstance(condition, ExistsStatement):
            condition = str(condition.frame["FIND"].singleton())
        elif isinstance(condition, MeaningProcedureStatement):
            condition = condition.frame["CALLS"].singleton() + "(" + ",".join(map(str, condition.frame["PARAMS"])) + ")"
        else:
            condition = str(condition)

        return {
            "frame": expectation.frame.id,
            "status": expectation.status().name,
            "condition": condition
        }

    @classmethod
    def effectors(cls, agent: Agent):
        return list(map(lambda e: IIDEAConverter.convert_effector(agent, e), agent.effectors()))

    @classmethod
    def convert_effector(cls, agent: Agent, effector: Effector):
        effecting = None
        if not effector.is_free():
            effecting = effector.on_decision().goal().frame.id

        return {
            "name": effector.frame.id,
            "type": effector.type().name,
            "status": effector.is_free(),
            "effecting": effecting,
            "capabilities": list(map(lambda c: IIDEAConverter.convert_capability(agent, c, effector), effector.capabilities()))
        }

    @classmethod
    def convert_capability(cls, agent: Agent, capability: Capability, wrt_effector: Effector):

        selected = "not"

        for d in agent.decisions():
            if d.status() == Decision.Status.EXECUTING:
                if capability in list(map(lambda output: output.capability(), d.outputs())):
                    selected = "elsewhere"

        if wrt_effector.on_capability() == capability:
            selected = "here"

        callbacks = []
        if wrt_effector.on_capability() == capability and wrt_effector.on_decision() is not None:
            callbacks = wrt_effector.on_decision().callbacks()
            callbacks = list(filter(lambda callback: callback.effector() == wrt_effector, callbacks))
            callbacks = list(map(lambda cb: {"name": cb.frame.id, "waiting": cb.status() == Callback.Status.WAITING}, callbacks))

        return {
            "name": capability.frame.id,
            "not_selected": selected == "not",
            "selected_elsewhere": selected == "elsewhere",
            "selected_here": selected == "here",
            "callbacks": callbacks
        }

    @classmethod
    def triggers(cls, agent: Agent):
        return list(map(lambda t: IIDEAConverter.convert_trigger(t), agent.agenda().triggers()))

    @classmethod
    def convert_trigger(cls, trigger: Trigger):
        return {
            "query": str(trigger.query()),
            "goal": trigger.definition().name(),
            "triggered-on": list(map(lambda to: str(to), trigger.triggered_on()))
        }

    @classmethod
    def logs(cls, agent: Agent):
        if isinstance(agent.logger(), CachedAgentLogger):
            return agent.logger()._cache
        return []