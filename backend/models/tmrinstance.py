from backend.models.instance import Instance


class TMRInstance(Instance):

    def __init__(self, inst_dict, name=None, uuid=None):
        name = name if name is not None else self.concept + "-X"
        concept = inst_dict["concept"]
        subtree = inst_dict["is-in-subtree"] if "is-in-subtree" in inst_dict else None

        properties = {}
        for key in inst_dict:
            if "_constraint_info" in key:
                pass
            if key == key.upper():
                properties[key] = inst_dict[key]

        super().__init__(name, concept, uuid=uuid, properties=properties, subtree=subtree)

        self.token_index = inst_dict["sent-word-ind"][1]