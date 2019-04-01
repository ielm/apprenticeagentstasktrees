from backend import agent
from backend.models.agenda import Goal
from backend.models.mps import AgentMethod, OutputMethod
from backend.models.xmr import XMR
from ontograph.Frame import Frame, Role
from ontograph.Index import Identifier


class FetchObjectCapability(OutputMethod):
    def run(self):
        target = self.output.root()["THEME"].singleton()

        try:
            id = target["visual-object-id"].singleton()

            from backend.utils.YaleUtils import signal_action

            signal_action("get", id, self.callback.frame.id)
        except:
            print("Warning: unable to signal robot to fetch " + target.id + ".")


class InitGreetHumanGoal(AgentMethod):

    def run(self, input_vmr):
        human = self.find_human(input_vmr)
        goal = Goal.instance_of(agent.internal, Frame("@ONT.GREET-HUMAN"), [human])
        agent.agenda().add_goal(goal)

    def find_human(self, input_vmr):
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

            from backend.utils.YaleUtils import signal_speech
            signal_speech(sentence, self.callback.frame.id)
        except:
            print("Warning: unable to signal robot to speak '" + str(sentence) + "'.")