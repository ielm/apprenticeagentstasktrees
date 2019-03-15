from backend.models.vmr import VMR
from ontograph import graph
from ontograph.Frame import Frame
from ontograph.Space import Space

from pkgutil import get_data
import json
import unittest


class VMRTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()
        graph.reset()

        Frame("@ONT.ALL")
        Frame("@ONT.OBJECT").add_parent("@ONT.ALL")
        Frame("@ONT.EVENT").add_parent("@ONT.ALL")
        Frame("@ONT.PROPERTY").add_parent("@ONT.ALL")
        Frame("@ONT.LOCATION").add_parent("@ONT.OBJECT")

        from backend.utils.AtomicCounter import AtomicCounter
        VMR.counter = AtomicCounter()

    @staticmethod
    def load_resource(module: str, file: str, parse_json: bool=False):
        binary = get_data(module, file)

        if not parse_json:
            return str(binary)

        return json.loads(binary)

    def test_vmr_init_with_environment(self):
        loc1 = Frame("@ENV.LOCATION.?")
        human1 = Frame("@ENV.HUMAN.?")
        human2 = Frame("@ENV.HUMAN.?")
        object1 = Frame("@ENV.OBJECT.?")

        input = {
            "ENVIRONMENT": {
                "_refers_to": "ENV",
                "timestamp": "...",
                "contains": {
                    "@ENV.HUMAN.1": {
                        "LOCATION": "HERE"
                    },
                    "@ENV.HUMAN.2": {
                        "LOCATION": "NOT-HERE"
                    },
                    "@ENV.OBJECT.1": {
                        "LOCATION": "@ENV.LOCATION.1"
                    }
                }
            }
        }

        vmr = VMR.from_json(input)
        vmr = vmr.graph()

        self.assertEqual("ENV", Frame("@VMR#1.ENVIRONMENT")["REFERS-TO"].singleton())
        self.assertIn("@VMR#1.LOCATION.1", vmr)
        self.assertIn("@VMR#1.LOCATION.2", vmr)
        self.assertNotIn("@VMR#1.LOCATION.3", vmr)

        if Frame("@VMR#1.LOCATION.1")["DOMAIN"].singleton() == human1:
            self.assertEqual(Frame("@VMR#1.ENVIRONMENT"), Frame("@VMR#1.LOCATION.1")["RANGE"].singleton())
        else:
            self.assertEqual(loc1, Frame("@VMR#1.LOCATION.1")["RANGE"].singleton())

        if Frame("@VMR#1.LOCATION.2")["DOMAIN"].singleton() == human1:
            self.assertEqual(Frame("@VMR#1.ENVIRONMENT"), Frame("@VMR#1.LOCATION.2")["RANGE"].singleton())
        else:
            self.assertEqual(loc1, Frame("@VMR#1.LOCATION.2")["RANGE"].singleton())

    def test_vmr_init_with_events(self):
        human1 = Frame("@ENV.HUMAN.?")
        human2 = Frame("@ENV.HUMAN.?")
        human3 = Frame("@ENV.HUMAN.?")
        human4 = Frame("@ENV.HUMAN.?")
        object1 = Frame("@ENV.OBJECT.?")
        object2 = Frame("@ENV.OBJECT.?")

        input = {
            "EVENTS": {
                "@PHYSICAL-EVENT.1": {
                    "ISA": ["@ONT.PHYSICAL-EVENT"],
                    "AGENT": ["@ENV.HUMAN.1", "@ENV.HUMAN.2"],
                    "THEME": ["@ENV.OBJECT.1"]
                },
                "@PHYSICAL-EVENT.2": {
                    "ISA": ["@ONT.PHYSICAL-EVENT"],
                    "AGENT": ["@ENV.HUMAN.3", "@ENV.HUMAN.4"],
                    "THEME": ["@ENV.OBJECT.2"]
                }
            }
        }

        vmr = VMR.from_json(input)
        vmr = vmr.graph()

        self.assertIn("@VMR#1.PHYSICAL-EVENT.1", vmr)
        self.assertIn("@VMR#1.PHYSICAL-EVENT.2", vmr)

        self.assertEqual(["@VMR#1.PHYSICAL-EVENT.1", "@VMR#1.PHYSICAL-EVENT.2"], Frame("@VMR#1.EVENTS")["HAS-EVENT"])

        self.assertEqual([human1, human2], Frame("@VMR#1.PHYSICAL-EVENT.1")["AGENT"])
        self.assertEqual([object1], Frame("@VMR#1.PHYSICAL-EVENT.1")["THEME"])
        self.assertEqual([human3, human4], Frame("@VMR#1.PHYSICAL-EVENT.2")["AGENT"])
        self.assertEqual([object2], Frame("@VMR#1.PHYSICAL-EVENT.2")["THEME"])

    def test_vmr_new(self):
        loc1 = Frame("@ENV.LOCATION.?")
        human1 = Frame("@ENV.HUMAN.?")
        human2 = Frame("@ENV.HUMAN.?")
        object1 = Frame("@ENV.OBJECT.?")

        contains = {
            "@ENV.HUMAN.1": {
                "LOCATION": "HERE"
            },
            "@ENV.HUMAN.2": {
                "LOCATION": "NOT-HERE"
            },
            "@ENV.OBJECT.1": {
                "LOCATION": "@ENV.LOCATION.1"
            }
        }

        events = {
            "@PHYSICAL-EVENT.1": {
                "ISA": ["@ONT.PHYSICAL-EVENT"],
                "AGENT": ["@ENV.HUMAN.1"],
                "THEME": ["@ENV.OBJECT.1"]
            },
            "@PHYSICAL-EVENT.2": {
                "ISA": ["@ONT.PHYSICAL-EVENT"],
                "AGENT": ["@ENV.HUMAN.2"],
                "THEME": ["@ENV.OBJECT.1"]
            }
        }

        vmr = VMR.from_contents(contains=contains, events=events)
        vmr = vmr.graph()

        self.assertEqual("ENV", Frame("@VMR#1.ENVIRONMENT")["REFERS-TO"].singleton())
        self.assertIn("@VMR#1.LOCATION.1", vmr)
        self.assertIn("@VMR#1.LOCATION.2", vmr)
        self.assertNotIn("@VMR#1.LOCATION.3", vmr)

        if Frame("@VMR#1.LOCATION.1")["DOMAIN"].singleton() == human1:
            self.assertEqual(Frame("@VMR#1.ENVIRONMENT"), Frame("@VMR#1.LOCATION.1")["RANGE"].singleton())
        else:
            self.assertEqual(loc1, Frame("@VMR#1.LOCATION.1")["RANGE"].singleton())

        if Frame("@VMR#1.LOCATION.2")["DOMAIN"].singleton() == human1:
            self.assertEqual(Frame("@VMR#1.ENVIRONMENT"), Frame("@VMR#1.LOCATION.2")["RANGE"].singleton())
        else:
            self.assertEqual(loc1, Frame("@VMR#1.LOCATION.2")["RANGE"].singleton())

        self.assertIn("@VMR#1.PHYSICAL-EVENT.1", vmr)
        self.assertIn("@VMR#1.PHYSICAL-EVENT.2", vmr)

        self.assertEqual(["@VMR#1.PHYSICAL-EVENT.1", "@VMR#1.PHYSICAL-EVENT.2"], Frame("@VMR#1.EVENTS")["HAS-EVENT"])

        self.assertEqual([human1], Frame("@VMR#1.PHYSICAL-EVENT.1")["AGENT"])
        self.assertEqual([human2], Frame("@VMR#1.PHYSICAL-EVENT.2")["AGENT"])
        self.assertEqual([object1], Frame("@VMR#1.PHYSICAL-EVENT.1")["THEME"])
        self.assertEqual([object1], Frame("@VMR#1.PHYSICAL-EVENT.2")["THEME"])

    def test_vmr_update_environment(self):
        from backend.models.environment import Environment

        loc1 = Frame("@ENV.LOCATION.?")
        loc2 = Frame("@ENV.LOCATION.?")
        human1 = Frame("@ENV.HUMAN.?")
        human2 = Frame("@ENV.HUMAN.?")
        object1 = Frame("@ENV.OBJECT.?")

        input1 = {
            "ENVIRONMENT": {
                "_refers_to": "ENV",
                "timestamp": "...",
                "contains": {
                    "@ENV.HUMAN.1": {
                        "LOCATION": "HERE"
                    },
                    "@ENV.HUMAN.2": {
                        "LOCATION": "NOT-HERE"
                    },
                    "@ENV.OBJECT.1": {
                        "LOCATION": "@ENV.LOCATION.1"
                    }
                }
            }
        }

        vmr = VMR.from_json(input1)
        vmr.update_environment(Space("ENV"))

        e = Environment(Space("ENV"))
        self.assertEqual(Frame("@ONT.LOCATION"), e.location(human1))
        self.assertEqual(Frame("@ENV.LOCATION.1"), e.location(object1))
        with self.assertRaises(Exception):
            e.location(human2)

        input2 = {
            "ENVIRONMENT": {
                "_refers_to": "ENV",
                "timestamp": "...",
                "contains": {
                    "@ENV.HUMAN.1": {
                        "LOCATION": "NOT-HERE"
                    },
                    "@ENV.HUMAN.2": {
                        "LOCATION": "HERE"
                    },
                    "@ENV.OBJECT.1": {
                        "LOCATION": "@ENV.LOCATION.2"
                    }
                }
            }
        }

        vmr = VMR.from_json(input2)
        vmr.update_environment(Space("ENV"))

        e = Environment(Space("ENV"))
        self.assertEqual(Frame("@ONT.LOCATION"), e.location(human2))
        self.assertEqual(Frame("@ENV.LOCATION.2"), e.location(object1))
        with self.assertRaises(Exception):
            e.location(human1)

    def test_vmr_update_working_memory(self):
        Frame("@WM.PHYSICAL-EVENT.?")

        events = {
            "@PHYSICAL-EVENT.1": {
                "ISA": ["@ONT.PHYSICAL-EVENT"],
                "AGENT": ["@ENV.HUMAN.1"],
                "THEME": ["@ENV.OBJECT.1"]
            },
            "@PHYSICAL-EVENT.2": {
                "ISA": ["@ONT.PHYSICAL-EVENT"],
                "AGENT": ["@ENV.HUMAN.2"],
                "THEME": ["@ENV.OBJECT.1"]
            }
        }

        vmr = VMR.from_contents(events=events)
        vmr.update_memory(Space("WM"))

        self.assertEqual(3, len(Space("WM")))
        self.assertIn("@WM.PHYSICAL-EVENT.1", Space("WM"))
        self.assertIn("@WM.PHYSICAL-EVENT.2", Space("WM"))
        self.assertIn("@WM.PHYSICAL-EVENT.3", Space("WM"))

        self.assertNotIn("AGENT", Frame("@WM.PHYSICAL-EVENT.1"))
        self.assertEqual("@ENV.HUMAN.1", Frame("@WM.PHYSICAL-EVENT.2")["AGENT"])
        self.assertEqual("@ENV.HUMAN.2", Frame("@WM.PHYSICAL-EVENT.3")["AGENT"])

        self.assertNotIn("THEME", Frame("@WM.PHYSICAL-EVENT.1"))
        self.assertEqual("@ENV.OBJECT.1", Frame("@WM.PHYSICAL-EVENT.2")["THEME"])
        self.assertEqual("@ENV.OBJECT.1", Frame("@WM.PHYSICAL-EVENT.3")["THEME"])