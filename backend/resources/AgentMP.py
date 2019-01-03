from backend.models.mps import AgentMethod
from backend.models.agenda import Goal
from backend.models.graph import Frame
from backend.models.xmr import XMR
from backend.agent import Agent
from backend.models.effectors import Capability


class FindSomethingToDoMP(AgentMethod):
    def run(self):
        self.agent.agenda().add_goal(Goal.instance_of(self.agent.internal, self.agent.exe["ACKNOWLEDGE-INPUT"], []))


class AddGoalMP(AgentMethod):
    def run(self, input):
        self.agent.agenda().add_goal(Goal.instance_of(self.agent.internal, self.agent.exe["ACKNOWLEDGE-INPUT"], [input]))


class PrintTMR(AgentMethod):
    def run(self, tmr):
        print("\nName: ", tmr.name())
        print("\nISA: ", tmr.concept())
        return


class AcknowledgeInputMP(AgentMethod):
    def run(self, input_mr):
        print(input_mr)
        return


class DecideOnLanguageInputMP(AgentMethod):
    def run(self, input_tmr):
        """
        Decides whether to RespondToQuery or PerformComplexTask
        TODO - Decision between response vs perform task.
        TODO - Return task
        TODO - Remove agenda.add_goal from MP and add goal in goal definition

        :param input_tmr:
        :return: TMR or Task
        """
        xmr = XMR(input_tmr)

        # REQUEST-ACTION
        request_action = xmr.graph(self.agent).search(Frame.q(self.agent).isa("ONT.REQUEST-ACTION"))
        
        if len(request_action) == 0: 
            return
        
        # TMR.BUILD.1
        action = request_action[0]["THEME"].singleton()
        # ONT.CHAIR
        action_theme = action["THEME"].singleton().parents()
        # ONT.BUILD
        action = action.parents()

        task = self.agent.lt_memory.search(Frame.q(self.agent).isa(action[0]).fisa("THEME", action_theme[0]))

        self.agent.agenda().add_goal(Goal.instance_of(self.agent.internal, self.agent.exe["PERFORM-COMPLEX-TASK"], [task[0]]))
        # return task


class RespondToQueryMP(AgentMethod):
    def run(self, input_tmr):
        return


class PerformComplexTaskMP(AgentMethod):
    def run(self, task, statement=None):
        """
        :param task: The current task
        :param statement:
        """
        target = task["HAS-EVENT-AS-PART"][0].resolve()["THEME"].singleton()

        # Create an or query for all targets. i.e. Screwdriver or Wrench or Hammer
        # For now there will only be one target
        q = Frame.q(self.agent, comparator="or")
        for p in target.parents():
            q.isa(p)

        # Search for the target in the environment
        env_target = self.agent.environment.search(q)[0]

        # Get the effector that is reserved by the current Goal
        reserved_effector = self.varmap.reserved_effector()

        # Get the capability that is used by reserved_effector
        capability = Capability(reserved_effector.frame["USES"].singleton())

        # Run the capability with the env_target as the target of the capability
        capability.run(self.agent, env_target, statement=statement, graph=self.agent.exe, varmap=self.varmap)
        return

    def capabilities(self, task):
        """
        Returns a list of capabilities available for the MP
        :param task: The current task
        :return: a list of capabilities
        """
        capabilities = []

        step = task["HAS-EVENT-AS-PART"][0]
        if step ^ "ONT.TAKE":
            step = step.resolve()
            effectors = self.agent.effectors()

            for e in effectors:
                if e.frame["HAS-CAPABILITY"] == 'GET-CAPABILITY':
                    capabilities.append(e.capabilities())

            return [item for sublist in capabilities for item in sublist]
        return capabilities


class GetPhysicalObjectCapabilityMP(AgentMethod):
    def run(self, target: Frame):
        self.agent.logger().log("Executed GET(" + target._identifier.render() + ")")
        return


class SpeakCapabilityMP(AgentMethod):
    def run(self):
        return


class ReactToVisualInputMP(AgentMethod):
    def run(self, vmr):
        return


class HoldPhysicalObjectMP(AgentMethod):
    def run(self, target: Frame):
        self.agent.logger().log("Executed HOLD(" + target._identifier.render() + ")")
        return


class FastenPhysicalObjectMP(AgentMethod):
    def run(self, target: Frame):
        self.agent.logger().log("Executed FASTEN(" + target._identifier.render() + ")")
        return


class RestrainPhysicalObjectMP(AgentMethod):
    def run(self, target: Frame):
        self.agent.logger().log("Executed RESTRAIN(" + target._identifier.render() + ")")
        return
