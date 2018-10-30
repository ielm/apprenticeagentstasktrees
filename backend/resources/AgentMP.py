from backend.models.mps import AgentMethod
from backend.models.agenda import Goal
from backend.models.graph import Frame
from backend.models.xmr import XMR


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
    def run(self, task):
        return


