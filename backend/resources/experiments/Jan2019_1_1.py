from backend.models.mps import AgentMethod, OutputMethod
from backend.models.xmr import XMR
from ontograph.Frame import Frame, Role
from ontograph.Index import Identifier
from ontograph.Query import AndComparator, InSpaceComparator, IsAComparator, Query


class SelectGoalFromLanguageInput(AgentMethod):
    def run(self, input_tmr):
        tmr = XMR(input_tmr).space()

        query = Query(AndComparator([InSpaceComparator(tmr.name), IsAComparator("@ONT.REQUEST-INFO")]))

        if len(query.start()) > 0:
            return Frame("@EXE.RESPOND-TO-QUERY")

        print("TODO: choose a goal intelligently")
        return Frame("@EXE.BUILD-A-CHAIR")


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

        try:
            id = target["visual-object-id"].singleton()

            from backend.utils.YaleUtils import signal_action

            signal_action("get", id, self.callback.frame.name())
        except:
            print("Warning: unable to signal robot to fetch " + str(target) + ".")


class SpeakCapability(OutputMethod):
    def run(self):
        try:
            sentence = ""
            if Identifier.parse(self.output.root()["THEME"].singleton().id)[1] == "GREET":
                target = self.output.root()["THEME"].singleton()["THEME"].singleton()
                if "HAS-NAME" in target:
                    sentence = "Hi " + target["HAS-NAME", Role.LOC].singleton() + "."
                else:
                    sentence = "Hi."

            elif Identifier.parse(self.output.root()["THEME"].singleton().id)[1] == "DESCRIBE":
                target = self.output.root()["THEME"].singleton()["THEME"].singleton()
                target = Identifier.parse(target.id)[0]
                for output in self.agent.outputs:
                    output = XMR.from_instance(output)
                    if output.space().name == target:
                        sentence = output.render()

            self.output.frame["SENTENCE"] = sentence

            print("TODO: issue command to robot to speak " + str(sentence))
        except: pass


class ShouldAcknowledgeVisualInput(AgentMethod):
    def run(self, input_vmr):
        vmr = XMR(input_vmr).space()

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
            if Identifier.parse(frame.id)[1] == "LOCATION":
                domain = frame["DOMAIN"].singleton()
                if domain ^ "@ONT.HUMAN":
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
        vmr = XMR(input_vmr).space()

        return self._acknowledge_due_to_human_entering(vmr)

    def _acknowledge_due_to_human_entering(self, vmr):
        # 1) Check to see that there is at least a previous history
        history = self.agent.env().history()
        if len(history) < 2:
            return False

        # 2) Find all LOCATIONs with a DOMAIN of ONT.HUMAN
        #    If that human is currently in the environment, AND was not previously in the environment, return True
        for frame in vmr:
            if Identifier.parse(frame.id)[1] == "LOCATION":
                domain = frame["DOMAIN"].singleton()
                if domain ^ "@ONT.HUMAN":
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
        vmr = XMR(input_vmr).space()

        history = self.agent.env().history()
        if len(history) < 2:
            return None

        for frame in vmr:
            if Identifier.parse(frame.id)[1] == "LOCATION":
                domain = frame["DOMAIN"].singleton()
                if domain ^ "@ONT.HUMAN":
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


class DetermineCurrentAction(AgentMethod):
    def run(self):
        from backend.models.agenda import Decision

        decisions = self.agent.decisions()
        decisions = list(filter(lambda d: d.status() == Decision.Status.EXECUTING, decisions))

        # TODO
        if len(decisions) > 0:
            return decisions[0].outputs()[0].root()

        return None
