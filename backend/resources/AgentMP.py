from backend.models.mps import AgentMethod
from backend.models.agenda import Goal


class FindSomethingToDoMP(AgentMethod):
    def run(self):
        self.agent.agenda().add_goal(Goal.instance_of(self.agent.internal, self.agent.exe["ACKNOWLEDGE-INPUT"], []))


# ATTN - Not Needed
class AddGoalMP(AgentMethod):
    def run(self, input):
        self.agent.agenda().add_goal(Goal.instance_of(self.agent.internal, self.agent.exe["ACKNOWLEDGE-INPUT"], [input]))


class PrintTMR(AgentMethod):
    def run(self, tmr):
        print("\nName: ", tmr.name())
        print("\nISA: ", tmr.concept())


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

        print("\nDECIDE Name: ", input_tmr.name())

        # Find LT.BUILD.1
        #     Request Action
        #     Agent = Human
        #     Benef = Robot
        # return LT.BUILD.1

        return input_tmr


class RespondToQueryMP(AgentMethod):
    def run(self, input_tmr):
        return


class PerformComplexTaskMP(AgentMethod):
    def run(self, task):
        return


