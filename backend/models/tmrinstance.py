from backend.models.instance import Instance


@DeprecationWarning
class TMRInstanceX(Instance):

    def __init__(self, properties=None, name=None, concept=None, uuid=None, subtree=None, index=None):
        self.concept = concept
        self.name = name if name is not None else self.concept + "-X"
        self.subtree = subtree

        if properties is None:
            properties = {}

        _properties = {}
        for key in properties:
            if "_constraint_info" in key:
                pass
            if key == key.upper():
                _properties[key] = properties[key]

        super().__init__(name, concept, uuid=uuid, properties=_properties, subtree=subtree)

        self.token_index = index