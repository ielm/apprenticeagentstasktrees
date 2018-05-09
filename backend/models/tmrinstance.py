from backend.models.instance import Instance
from uuid import uuid4


class TMRInstance(Instance):

    def __init__(self, inst_dict, name=None):
        super().__init__(inst_dict, name=name)
        self.token_index = inst_dict["sent-word-ind"][1]
        self.uuid = uuid4()