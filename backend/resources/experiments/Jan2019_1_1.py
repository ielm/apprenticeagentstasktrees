from backend.models.mps import AgentMethod, OutputMethod
from backend.models.agenda import Goal
from backend.models.graph import Frame
from backend.models.xmr import XMR
from backend.models.effectors import Capability


class SelectGoalFromLanguageInput(AgentMethod):
    def run(self, input_tmr):
        print("TODO: choose a goal intelligently")
        return self.agent.lookup("EXE.BUILD-A-CHAIR")


class InitGoalCapability(OutputMethod):
    def run(self):
        from backend.models.agenda import Goal

        params = []
        try:
            params = list(self.output.root()["PARAMS"])
        except: pass

        definition = self.output.root()["THEME"].singleton()
        goal = Goal.instance_of(self.agent.internal, definition, params)
        self.agent.agenda().add_goal(goal)

        self.agent.callback(self.callback)


class FetchObjectCapability(OutputMethod):
    def run(self):
        target = self.output.root()["THEME"].singleton()

        print("TODO: issue command to robot to fetch " + str(target))


class SpeakCapability(OutputMethod):
    def run(self):
        print("TODO: convert tmr to language, speak it")


class ShouldAcknowledgeVisualInput(AgentMethod):
    def run(self, input_vmr):
        vmr = XMR(input_vmr).graph(self.agent)

        if self._acknowledge_due_to_human_entering(vmr):
            return True

        return False

    def _acknowledge_due_to_human_entering(self, vmr):
        # 1) Check to see that there is at least a previous history
        history = self.agent.env().history()
        if len(history) < 2:
            return False

        # 2) Find all LOCATIONs with a DOMAIN of ONT.HUMAN
        #    If that human is currently in the environment, AND was not previously in the environment, return True
        for frame in vmr:
            frame = vmr[frame]
            if frame._identifier.name == "LOCATION":
                domain = frame["DOMAIN"].singleton()
                if domain ^ "ONT.HUMAN":
                    try:
                        # The agent is currently in the environment
                        self.agent.env().location(domain)
                    except:
                        continue
                    try:
                        # The agent was not previously in the environment
                        self.agent.env().location(domain, epoch=len(history) - 2)
                    except:
                        return True
        return False


class ShouldGreetHuman(AgentMethod):
    def run(self, input_vmr):
        vmr = XMR(input_vmr).graph(self.agent)

        return self._acknowledge_due_to_human_entering(vmr)

    def _acknowledge_due_to_human_entering(self, vmr):
        # 1) Check to see that there is at least a previous history
        history = self.agent.env().history()
        if len(history) < 2:
            return False

        # 2) Find all LOCATIONs with a DOMAIN of ONT.HUMAN
        #    If that human is currently in the environment, AND was not previously in the environment, return True
        for frame in vmr:
            frame = vmr[frame]
            if frame._identifier.name == "LOCATION":
                domain = frame["DOMAIN"].singleton()
                if domain ^ "ONT.HUMAN":
                    try:
                        # The agent is currently in the environment
                        self.agent.env().location(domain)
                    except:
                        continue
                    try:
                        # The agent was not previously in the environment
                        self.agent.env().location(domain, epoch=len(history) - 2)
                    except:
                        return True
        return False


class SelectHumanToGreet(AgentMethod):
    def run(self, input_vmr):
        vmr = XMR(input_vmr).graph(self.agent)

        history = self.agent.env().history()
        if len(history) < 2:
            return None

        for frame in vmr:
            frame = vmr[frame]
            if frame._identifier.name == "LOCATION":
                domain = frame["DOMAIN"].singleton()
                if domain ^ "ONT.HUMAN":
                    try:
                        # The agent is currently in the environment
                        self.agent.env().location(domain)
                    except:
                        continue
                    try:
                        # The agent was not previously in the environment
                        self.agent.env().location(domain, epoch=len(history) - 2)
                    except:
                        return domain

        return None


######################

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


class UnderstandInputMP(AgentMethod):
    def run(self, tmr_frame):
        tmr = self.agent[tmr_frame["REFERS-TO-GRAPH"].singleton()]
        agenda = self.agent.context.default_understanding()
        agenda.logger(self.agent._logger)
        agenda.process(self.agent, tmr)
        if self.callback is not None:
            self.agent.callback(self.callback)


class PrioritizeLearningMP(AgentMethod):
    def run(self, tmr_frame):
        return 0.75


class EvalResourcesMP(AgentMethod):
    def run(self, tmr_frame):
        return 0.5