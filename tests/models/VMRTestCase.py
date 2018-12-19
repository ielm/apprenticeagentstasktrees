from backend.models.graph import Identifier, Network
from backend.models.vmr import VMR, VMRInstance

from pkgutil import get_data
import json
import unittest


class VMRTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.n = Network()

        self.ontology = self.n.register("ONT")
        self.ontology.register("ALL")
        self.ontology.register("OBJECT", isa="ALL")
        self.ontology.register("EVENT", isa="ALL")
        self.ontology.register("PROPERTY", isa="ALL")

    @staticmethod
    def load_resource(module: str, file: str, parse_json: bool=False):
        binary = get_data(module, file)

        if not parse_json:
            return str(binary)

        return json.loads(binary)

    def test_vmr_as_graph(self):
        vmr = VMR.new(self.ontology)

        agent1 = vmr.register("AGENT")
        event1 = vmr.register("EVENT")
        theme1 = vmr.register("THEME")