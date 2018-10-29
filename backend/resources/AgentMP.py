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

# class FindTaskMP(AgentMethod):
#     def run(self, tmr):
#         return


class AcknowledgeInputMP(AgentMethod):
    def run(self, input_mr):
        return


class DecideOnLanguageInputMP(AgentMethod):
    def run(self, input_tmr):
        """
        Decides whether to RespondToQuery or PerformComplexTask
        :param input_tmr:
        :return: TMR or Task
        """

        # print("\n\nDECIDE Name: ", type(input_tmr), "\n\n")

        # TODO - Search for TMR#1 in agent._storage
        # ATTN - self.agent['TMR#1']['TMR#1.REQUEST-ACTION.1'] where AGENT=ONT.HUMAN & BENEFICIARY=ONT.ROBOT
        #   Find THEME of REQUEST-ACTION (BUILD.1)
        #   find REQUEST-ACTION[THEME] in LTM (LT.BUILD.1)

        xmr_graph = XMR(input_tmr)

        # print(xmr_graph.graph(self.agent))

        # REQUEST-ACTION
        request_action = xmr_graph.graph(self.agent).search(Frame.q(self.agent).isa("ONT.REQUEST-ACTION"))

        # TMR.BUILD.1
        action = request_action[0]["THEME"].singleton()

        # ONT.CHAIR
        action_theme = action["THEME"].singleton().parents()

        # ONT.BUILD
        action = action.parents()

        # real_task = self.agent.lt_memory.search(Frame.q(self.agent).isa(action[0]).fisa("THEME", action_theme[0]))
        task = self.agent.lt_memory.search(Frame.q(self.agent).isa(action[0]).fisa("THEME", "ONT.CHAIR"))

        # TODO - add PERFORM-COMPLEX-TASK(task) to agenda (either here or in goal definition)
        # self.agent.agenda().add_goal(Goal.instance_of(self.agent.internal, self.agent.exe["PERFORM-COMPLEX-TASK"], [task]))

        # Find LT.BUILD
        #     Request Action
        #     Agent = Human
        #     Benef = Robot
        # return LT.BUILD.1

        # return input_tmr


class RespondToQueryMP(AgentMethod):
    def run(self, input_tmr):
        return


class PerformComplexTaskMP(AgentMethod):
    def run(self, task):
        print(task.name())
        return


