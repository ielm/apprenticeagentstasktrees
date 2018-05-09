import unittest

from backend.models.frinstance import FRInstance


class FRInstanceTestCase(unittest.TestCase):

    def test_compare_fillers(self):
        filler1 = FRInstance.FRFiller(0, "value")
        filler2 = FRInstance.FRFiller(0, "value")
        self.assertEqual(filler1, filler2)

        filler1.add_ambiguity(3)
        self.assertNotEqual(filler1, filler2)

        filler2.add_ambiguity(3)
        self.assertEqual(filler1, filler2)

    def test_add_single_value(self):
        instance = FRInstance("name", "concept", 1)
        instance.remember("PROPERTY", "VALUE-1")

        values = instance["PROPERTY"]
        self.assertEqual(1, len(values))
        self.assertEqual(FRInstance.FRFiller, type(values[0]))
        self.assertEqual(0, values[0].time)
        self.assertEqual("VALUE-1", values[0].value)
        self.assertFalse(values[0].is_ambiguous())

    def test_add_multiple_values(self):
        instance = FRInstance("name", "concept", 1)
        instance.remember("PROPERTY-A", "VALUE-1")
        instance.remember("PROPERTY-A", {"VALUE-2"})
        instance.remember("PROPERTY-B", "VALUE-1")

        property_a = instance["PROPERTY-A"]
        property_b = instance["PROPERTY-B"]

        self.assertEqual(2, len(property_a))
        self.assertEqual(1, len(property_b))

        self.assertEqual(property_a[0], FRInstance.FRFiller(0, "VALUE-1"))
        self.assertEqual(property_a[1], FRInstance.FRFiller(0, "VALUE-2"))
        self.assertEqual(property_b[0], FRInstance.FRFiller(0, "VALUE-1"))

    def test_id_increases(self):
        instance = FRInstance("name", "concept", 1)
        instance.remember("PROPERTY", "VALUE-1")
        instance.remember("PROPERTY", "VALUE-2")

        values = instance["PROPERTY"]
        self.assertEqual(values[0].id + 1, values[1].id)

    def test_add_ambiguous_values(self):
        instance = FRInstance("name", "concept", 1)
        instance.remember("PROPERTY", {"VALUE-1", "VALUE-2"})

        values = instance["PROPERTY"]
        value1 = values[0]
        value2 = values[1]

        if value1.value == "VALUE-2":
            value1 = values[1]
            value2 = values[0]

        self.assertEqual(2, len(values))
        self.assertTrue(FRInstance.FRFiller(0, "VALUE-1", {value2.id}) in values)
        self.assertTrue(FRInstance.FRFiller(0, "VALUE-2", {value1.id}) in values)

    def test_add_redundant_values(self):
        instance = FRInstance("name", "concept", 1)

        instance.remember("PROPERTY", "VALUE-1")
        self.assertEqual(instance["PROPERTY"], [FRInstance.FRFiller(0, "VALUE-1")])

        instance.remember("PROPERTY", "VALUE-1")
        self.assertEqual(instance["PROPERTY"], [FRInstance.FRFiller(0, "VALUE-1")])

        instance.remember("PROPERTY", "VALUE-1", filter_redundant=False)
        self.assertEqual(instance["PROPERTY"], [FRInstance.FRFiller(0, "VALUE-1"), FRInstance.FRFiller(0, "VALUE-1")])

    def test_advance_time(self):
        instance = FRInstance("name", "concept", 1)
        instance.remember("PROPERTY", "VALUE-1")
        instance.advance()
        instance.remember("PROPERTY", "VALUE-1")

        values = instance["PROPERTY"]
        self.assertEqual(2, len(values))
        self.assertEqual(values[0], FRInstance.FRFiller(0, "VALUE-1"))
        self.assertEqual(values[1], FRInstance.FRFiller(1, "VALUE-1"))