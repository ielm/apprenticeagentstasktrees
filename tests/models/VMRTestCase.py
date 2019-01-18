from backend.models.graph import Identifier, Network
from backend.models.vmr import VMR

from pkgutil import get_data
import json
import unittest


class VMRTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()

        self.n = Network()
        self.n.register("INPUTS")

        self.ontology = self.n.register("ONT")
        self.ontology.register("ALL")
        self.ontology.register("OBJECT", isa="ALL")
        self.ontology.register("EVENT", isa="ALL")
        self.ontology.register("PROPERTY", isa="ALL")
        self.ontology.register("LOCATION", isa="OBJECT")

        from backend.utils.AtomicCounter import AtomicCounter
        VMR.counter = AtomicCounter()

    @staticmethod
    def load_resource(module: str, file: str, parse_json: bool=False):
        binary = get_data(module, file)

        if not parse_json:
            return str(binary)

        return json.loads(binary)

    def test_vmr_init_with_environment(self):
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

        vmr = VMR.from_json(self.n, self.ontology, input)
        vmr = vmr.graph(self.n)

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

    def test_vmr_init_with_events(self):
        env = self.n.register("ENV")
        human1 = env.register("HUMAN", generate_index=True)
        human2 = env.register("HUMAN", generate_index=True)
        human3 = env.register("HUMAN", generate_index=True)
        human4 = env.register("HUMAN", generate_index=True)
        object1 = env.register("OBJECT", generate_index=True)
        object2 = env.register("OBJECT", generate_index=True)

        input = {
            "EVENTS": {
                "PHYSICAL-EVENT.1": {
                    "ISA": ["ONT.PHYSICAL-EVENT"],
                    "AGENT": ["ENV.HUMAN.1", "ENV.HUMAN.2"],
                    "THEME": ["ENV.OBJECT.1"]
                },
                "PHYSICAL-EVENT.2": {
                    "ISA": ["ONT.PHYSICAL-EVENT"],
                    "AGENT": ["ENV.HUMAN.3", "ENV.HUMAN.4"],
                    "THEME": ["ENV.OBJECT.2"]
                }
            }
        }

        vmr = VMR.from_json(self.n, self.ontology, input)
        vmr = vmr.graph(self.n)

        self.assertIn("PHYSICAL-EVENT.1", vmr)
        self.assertIn("PHYSICAL-EVENT.2", vmr)

        self.assertEqual(["VMR#1.PHYSICAL-EVENT.1", "VMR#1.PHYSICAL-EVENT.2"], vmr["EVENTS"]["HAS-EVENT"])

        self.assertEqual([human1, human2], vmr["PHYSICAL-EVENT.1"]["AGENT"])
        self.assertEqual([object1], vmr["PHYSICAL-EVENT.1"]["THEME"])
        self.assertEqual([human3, human4], vmr["PHYSICAL-EVENT.2"]["AGENT"])
        self.assertEqual([object2], vmr["PHYSICAL-EVENT.2"]["THEME"])

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

        events = {
            "PHYSICAL-EVENT.1": {
                "ISA": ["ONT.PHYSICAL-EVENT"],
                "AGENT": ["ENV.HUMAN.1"],
                "THEME": ["ENV.OBJECT.1"]
            },
            "PHYSICAL-EVENT.2": {
                "ISA": ["ONT.PHYSICAL-EVENT"],
                "AGENT": ["ENV.HUMAN.2"],
                "THEME": ["ENV.OBJECT.1"]
            }
        }

        vmr = VMR.from_contents(self.n, self.ontology, contains=contains, events=events)
        vmr = vmr.graph(self.n)

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

        self.assertIn("PHYSICAL-EVENT.1", vmr)
        self.assertIn("PHYSICAL-EVENT.2", vmr)

        self.assertEqual(["VMR#1.PHYSICAL-EVENT.1", "VMR#1.PHYSICAL-EVENT.2"], vmr["EVENTS"]["HAS-EVENT"])

        self.assertEqual([human1], vmr["PHYSICAL-EVENT.1"]["AGENT"])
        self.assertEqual([human2], vmr["PHYSICAL-EVENT.2"]["AGENT"])
        self.assertEqual([object1], vmr["PHYSICAL-EVENT.1"]["THEME"])
        self.assertEqual([object1], vmr["PHYSICAL-EVENT.2"]["THEME"])

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

        vmr = VMR.from_json(self.n, self.ontology, input1)
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

        vmr = VMR.from_json(self.n, self.ontology, input2)
        vmr.update_environment(env)

        e = Environment(env)
        self.assertEqual(self.ontology["LOCATION"], e.location(human2))
        self.assertEqual(env["LOCATION.2"], e.location(object1))
        with self.assertRaises(Exception):
            e.location(human1)

    def test_vmr_update_working_memory(self):
        wm = self.n.register("WM")
        wm.register("PHYSICAL-EVENT", generate_index=True)

        events = {
            "PHYSICAL-EVENT.1": {
                "ISA": ["ONT.PHYSICAL-EVENT"],
                "AGENT": ["ENV.HUMAN.1"],
                "THEME": ["ENV.OBJECT.1"]
            },
            "PHYSICAL-EVENT.2": {
                "ISA": ["ONT.PHYSICAL-EVENT"],
                "AGENT": ["ENV.HUMAN.2"],
                "THEME": ["ENV.OBJECT.1"]
            }
        }

        vmr = VMR.from_contents(self.n, self.ontology, events=events)
        vmr.update_memory(wm)

        self.assertEqual(3, len(wm))
        self.assertIn("PHYSICAL-EVENT.1", wm)
        self.assertIn("PHYSICAL-EVENT.2", wm)
        self.assertIn("PHYSICAL-EVENT.3", wm)

        self.assertNotIn("AGENT", wm["PHYSICAL-EVENT.1"])
        self.assertEqual("ENV.HUMAN.1", wm["PHYSICAL-EVENT.2"]["AGENT"])
        self.assertEqual("ENV.HUMAN.2", wm["PHYSICAL-EVENT.3"]["AGENT"])

        self.assertNotIn("THEME", wm["PHYSICAL-EVENT.1"])
        self.assertEqual("ENV.OBJECT.1", wm["PHYSICAL-EVENT.2"]["THEME"])
        self.assertEqual("ENV.OBJECT.1", wm["PHYSICAL-EVENT.3"]["THEME"])