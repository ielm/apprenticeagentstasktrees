from backend.models.mps import AgentMethod, OutputMethod


class SelectGoalFromLanguageInput(AgentMethod):
    def run(self, input_tmr):
        print("TODO: choose a goal intelligently")
        return self.agent.lookup("EXE.BUILD-A-CHAIR")


class InitGoalCapability(OutputMethod):
    def run(self):
        from backend.models.agenda import Goal

        print("TODO: handle possible parameters")

        definition = self.output.root()["THEME"].singleton()
        goal = Goal.instance_of(self.agent.internal, definition, [])
        self.agent.agenda().add_goal(goal)

        self.agent.callback(self.callback)


class SelectObjectOfType(AgentMethod):
    def run(self, concept):
        from backend.models.graph import Frame

        print("TODO: choose an object intelligently")

        target = self.agent.environment.search(Frame.q(self.agent).isa(concept))[0]
        return target


class FetchObjectCapability(OutputMethod):
    def run(self):
        target = self.output.root()["THEME"].singleton()

        print("TODO: issue command to robot to fetch " + str(target))


class ExampleCapability(OutputMethod):
    def run(self):
        target = self.output.root()["THEME"].singleton()
        print("Issuing example capability with target " + str(target))