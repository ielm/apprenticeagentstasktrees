from backend.models.tmr import TMR


@DeprecationWarning
class Instructions:

    instructions = []

    def __init__(self, instructions, ontology):
        self.instructions = instructions
        self.ontology = ontology

    def __iter__(self):
        return self.__generator()

    def __generator(self):
        action_buffer = []
        for instruction in self.instructions:
            if TMR(instruction, self.ontology).is_utterance():
                if len(action_buffer) > 0:
                    yield action_buffer
                    action_buffer = []
                yield [instruction]
            else:
                action_buffer.append(instruction)

        if len(action_buffer) > 0:
            yield action_buffer