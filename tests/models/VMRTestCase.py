from backend.models.graph import Identifier, Network
from backend.models.vmr import VMR

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
        self.ontology.register("LOCATION", isa="OBJECT")

    @staticmethod
    def load_resource(module: str, file: str, parse_json: bool=False):
        binary = get_data(module, file)

        if not parse_json:
            return str(binary)

        return json.loads(binary)

    def test_vmr_init(self):
        env = self.n.register("ENV")
        loc1 = env.register("LOCATION", generate_index=True)
        human1 = env.register("HUMAN", generate_index=True)
        human2 = env.register("HUMAN", generate_index=True)
        object1 = env.register("OBJECT", generate_index=True)

        input = {
            "ENVIRONMENT": {
                "_refers_to": "ENV",
                "timestamp": "...",
                "contains": {
                    "ENV.HUMAN.1": {
                        "LOCATION": "HERE"
                    },
                    "ENV.HUMAN.2": {
                        "LOCATION": "NOT-HERE"
                    },
                    "ENV.OBJECT.1": {
                        "LOCATION": "ENV.LOCATION.1"
                    }
                }
            }
        }

        vmr = self.n.register(VMR(input, self.ontology))

        self.assertEqual("ENV", vmr["ENVIRONMENT"]["REFERS-TO"].singleton())
        self.assertIn("LOCATION.1", vmr)
        self.assertIn("LOCATION.2", vmr)
        self.assertNotIn("LOCATION.3", vmr)

        if vmr["LOCATION.1"]["DOMAIN"].singleton() == human1:
            self.assertEqual(vmr["ENVIRONMENT"], vmr["LOCATION.1"]["RANGE"].singleton())
        else:
            self.assertEqual(loc1, vmr["LOCATION.1"]["RANGE"].singleton())

        if vmr["LOCATION.2"]["DOMAIN"].singleton() == human1:
            self.assertEqual(vmr["ENVIRONMENT"], vmr["LOCATION.2"]["RANGE"].singleton())
        else:
            self.assertEqual(loc1, vmr["LOCATION.2"]["RANGE"].singleton())

    def test_vmr_new(self):
        env = self.n.register("ENV")
        loc1 = env.register("LOCATION", generate_index=True)
        human1 = env.register("HUMAN", generate_index=True)
        human2 = env.register("HUMAN", generate_index=True)
        object1 = env.register("OBJECT", generate_index=True)

        contains = {
            "ENV.HUMAN.1": {
                "LOCATION": "HERE"
            },
            "ENV.HUMAN.2": {
                "LOCATION": "NOT-HERE"
            },
            "ENV.OBJECT.1": {
                "LOCATION": "ENV.LOCATION.1"
            }
        }

        vmr = self.n.register(VMR.new(self.ontology, contains=contains))

        self.assertEqual("ENV", vmr["ENVIRONMENT"]["REFERS-TO"].singleton())
        self.assertIn("LOCATION.1", vmr)
        self.assertIn("LOCATION.2", vmr)
        self.assertNotIn("LOCATION.3", vmr)

        if vmr["LOCATION.1"]["DOMAIN"].singleton() == human1:
            self.assertEqual(vmr["ENVIRONMENT"], vmr["LOCATION.1"]["RANGE"].singleton())
        else:
            self.assertEqual(loc1, vmr["LOCATION.1"]["RANGE"].singleton())

        if vmr["LOCATION.2"]["DOMAIN"].singleton() == human1:
            self.assertEqual(vmr["ENVIRONMENT"], vmr["LOCATION.2"]["RANGE"].singleton())
        else:
            self.assertEqual(loc1, vmr["LOCATION.2"]["RANGE"].singleton())

    def test_vmr_update_environment(self):
        from backend.models.environment import Environment

        env = self.n.register("ENV")
        env.register("EPOCH")

        loc1 = env.register("LOCATION", generate_index=True)
        loc2 = env.register("LOCATION", generate_index=True)
        human1 = env.register("HUMAN", generate_index=True)
        human2 = env.register("HUMAN", generate_index=True)
        object1 = env.register("OBJECT", generate_index=True)

        input1 = {
            "ENVIRONMENT": {
                "_refers_to": "ENV",
                "timestamp": "...",
                "contains": {
                    "ENV.HUMAN.1": {
                        "LOCATION": "HERE"
                    },
                    "ENV.HUMAN.2": {
                        "LOCATION": "NOT-HERE"
                    },
                    "ENV.OBJECT.1": {
                        "LOCATION": "ENV.LOCATION.1"
                    }
                }
            }
        }

        vmr = self.n.register(VMR(input1, self.ontology))
        vmr.update_environment(env)

        e = Environment(env)
        self.assertEqual(self.ontology["LOCATION"], e.location(human1))
        self.assertEqual(env["LOCATION.1"], e.location(object1))
        with self.assertRaises(Exception):
            e.location(human2)

        input2 = {
            "ENVIRONMENT": {
                "_refers_to": "ENV",
                "timestamp": "...",
                "contains": {
                    "ENV.HUMAN.1": {
                        "LOCATION": "NOT-HERE"
                    },
                    "ENV.HUMAN.2": {
                        "LOCATION": "HERE"
                    },
                    "ENV.OBJECT.1": {
                        "LOCATION": "ENV.LOCATION.2"
                    }
                }
            }
        }

        vmr = self.n.register(VMR(input2, self.ontology))
        vmr.update_environment(env)

        e = Environment(env)
        self.assertEqual(self.ontology["LOCATION"], e.location(human2))
        self.assertEqual(env["LOCATION.2"], e.location(object1))
        with self.assertRaises(Exception):
            e.location(human1)