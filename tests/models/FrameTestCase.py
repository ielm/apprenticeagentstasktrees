from backend.models.graph import Filler, Fillers, Frame, Graph

import unittest


class FillerTestCase(unittest.TestCase):

    def test_filler_compares_to_filler(self):
        f1 = Filler("value1")
        f2 = Filler("value1")
        f3 = Filler("value2")

        self.assertEqual(f1, f2)
        self.assertNotEqual(f1, f3)

    def test_filler_compares_to_value(self):
        f = Filler("value1")

        self.assertEqual(f, "value1")
        self.assertNotEqual(f, "value2")


class FillersTestCase(unittest.TestCase):

    def test_fillers_initialize_empty(self):
        fs = Fillers()

        self.assertEqual(list(), fs._storage)

    def test_fillers_initialize_single_filler(self):
        f1 = Filler("value1")
        fs = Fillers(f1)

        self.assertEqual([f1], fs._storage)

    def test_fillers_initialize_single_value(self):
        fs = Fillers("value1")

        self.assertEqual([Filler("value1")], fs._storage)
        self.assertEqual(["value1"], fs._storage)

    def test_fillers_initialize_multiple_fillers(self):
        f1 = Filler("value1")
        f2 = Filler("value2")
        fs = Fillers([f1, f2])

        self.assertEqual([f1, f2], fs._storage)

    def test_fillers_initialize_multiple_values(self):
        fs = Fillers(["value1", "value2"])

        self.assertEqual([Filler("value1"), Filler("value2")], fs._storage)
        self.assertEqual(["value1", "value2"], fs._storage)

    def test_fillers_compares_to_fillers(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertEqual(Fillers([f1, f2]), Fillers([f1, f2]))

    def test_fillers_compares_to_lists(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertEqual(Fillers([f1, f2]), [f1, f2])
        self.assertEqual(Fillers([f1, f2]), [f1._value, f2._value])

    def test_fillers_compares_to_single_filler(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertEqual(Fillers([f1]), f1)
        self.assertNotEqual(Fillers([f2]), f1)

    def test_fillers_compares_to_single_value(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertEqual(Fillers([f1]), "value1")
        self.assertNotEqual(Fillers([f2]), "value1")

    def test_fillers_length(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertEqual(0, len(Fillers()))
        self.assertEqual(2, len(Fillers([f1, f2])))

    def test_fillers_contains_filler(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertTrue(f1 in Fillers([f1]))
        self.assertTrue(Filler(f1._value) in Fillers([f1]))
        self.assertTrue(f1 in Fillers([f1, f2]))
        self.assertFalse(f2 in Fillers([f1]))

    def test_fillers_contains_value(self):
        f1 = Filler("value1")
        f2 = Filler("value2")

        self.assertTrue("value1" in Fillers([f1]))
        self.assertTrue("value1" in Fillers([f1, f2]))
        self.assertFalse("value2" in Fillers([f1]))

    def test_fillers_iterable(self):
        f1 = Filler(1)
        f2 = Filler(2)

        self.assertEqual([3, 4], list(map(lambda filler: filler._value + 2, Fillers([f1, f2]))))


class FrameTestCase(unittest.TestCase):

    def test_frame_assign_and_retrieve_value(self):
        f = Frame()
        f["SLOT"] = "VALUE"

        self.assertEqual(Fillers, type(f["SLOT"]))
        self.assertEqual(Filler, type(f["SLOT"]._storage[0]))
        self.assertEqual("VALUE", f["SLOT"]._storage[0]._value)

    def test_frame_assign_fillers(self):
        f = Frame()
        f["SLOT"] = Fillers("VALUE")

        self.assertEqual("VALUE", f["SLOT"])

    def test_frame_overwrite_fillers(self):
        f = Frame()

        f["SLOT"] = Fillers("VALUE1")
        self.assertEqual("VALUE1", f["SLOT"])

        f["SLOT"] = Fillers("VALUE2")
        self.assertEqual("VALUE2", f["SLOT"])

    def test_frame_retrieve_empty_value(self):
        f = Frame()

        self.assertEqual(f["SLOT"], Fillers())

    def test_frame_slot_defined(self):
        f = Frame()
        f["SLOT"] = "VALUE"

        self.assertTrue("SLOT" in f)
        self.assertFalse("OTHER" in f)

    def test_add_fillers_to_existing_slot(self):
        f = Frame()

        f["SLOT"] = "value1"
        self.assertEqual("value1", f["SLOT"])

        f["SLOT"] += "value2"
        self.assertEqual(["value1", "value2"], f["SLOT"])

    def test_slot_contains(self):
        f = Frame()
        f["SLOT"] = ["value1", "value2"]

        self.assertTrue("value1" in f["SLOT"])
        self.assertTrue("value2" in f["SLOT"])
        self.assertFalse("value3" in f["SLOT"])

    def test_delete_slot(self):
        f = Frame()
        f["SLOT"] = "value"

        del f["SLOT"]
        self.assertEqual([], f["SLOT"])
        self.assertFalse("SLOT" in f)

    def test_length(self):
        f = Frame()
        self.assertEqual(0, len(f))

        f["SLOT"] = "value"
        self.assertEqual(1, len(f))

    def test_iterable_slots(self):
        f = Frame()
        f["SLOT1"] = "value"
        f["SLOT2"] = "value"

        result = ""
        for slot in f:
            result += slot
        self.assertEqual(result, "SLOT1SLOT2")

    '''
    intersection compare ([v1, v2] ~= [v2, v3])
    concept compare (v1.concept == v2.concept) or (v1.concept == v2, where v2 is a concept)
    concept inherit compare (v1.concept ^= v2.concept) ...
    '''