from backend.models.grammar import Grammar
from backend.models.graph import Identifier, Literal, Network
from backend.models.path import Path
from backend.models.query import AndQuery, ExactQuery, FillerQuery, FrameQuery, IdentifierQuery, LiteralQuery, NameQuery, NotQuery, OrQuery, SlotQuery
from backend.models.view import View

import unittest


class GrammarTestCase(unittest.TestCase):

    def setUp(self):
        self.n = Network()

    def test_parse_instance(self):
        self.assertEqual(1, Grammar.parse(self.n, "1", start="instance"))
        self.assertEqual(123, Grammar.parse(self.n, "123", start="instance"))

    def test_parse_name(self):
        self.assertEqual("EVENT", Grammar.parse(self.n, "EVENT", start="name"))
        self.assertEqual("EvEnT", Grammar.parse(self.n, "EvEnT", start="name"))
        self.assertEqual("EvEn_T", Grammar.parse(self.n, "EvEn_T", start="name"))
        self.assertEqual("*EvEn.T", Grammar.parse(self.n, "*EvEn.T", start="name"))

    def test_parse_graph(self):
        self.assertEqual("WM", Grammar.parse(self.n, "WM", start="graph"))
        self.assertEqual("TmR", Grammar.parse(self.n, "TmR", start="graph"))
        self.assertEqual("TMR#123456", Grammar.parse(self.n, "TMR#123456", start="graph"))

    def test_parse_identifier(self):
        self.assertEqual(Identifier("WM", "EVENT", instance=1), Grammar.parse(self.n, "WM.EVENT.1", start="identifier"))
        self.assertEqual(Identifier(None, "EVENT", instance=1), Grammar.parse(self.n, "EVENT.1", start="identifier"))
        self.assertEqual(Identifier("WM", "EVENT"), Grammar.parse(self.n, "WM.EVENT", start="identifier"))
        self.assertEqual(Identifier(None, "EVENT"), Grammar.parse(self.n, "EVENT", start="identifier"))
        with self.assertRaises(Exception):
            Grammar.parse(self.n, "True", start="identifier")
        with self.assertRaises(Exception):
            Grammar.parse(self.n, "False", start="identifier")

    def test_parse_integer(self):
        self.assertEqual(1, Grammar.parse(self.n, "1", start="integer"))
        self.assertEqual(123, Grammar.parse(self.n, "123", start="integer"))

    def test_parse_double(self):
        self.assertEqual(1.0, Grammar.parse(self.n, "1.0", start="double"))
        self.assertEqual(1.01, Grammar.parse(self.n, "1.01", start="double"))

    def test_parse_string(self):
        self.assertEqual("test", Grammar.parse(self.n, "\"test\"", start="string"))
        self.assertEqual("123", Grammar.parse(self.n, "\"123\"", start="string"))
        self.assertEqual("12ac3b3", Grammar.parse(self.n, "\"12ac3b3\"", start="string"))

    def test_parse_literal(self):
        self.assertEqual(Literal(1), Grammar.parse(self.n, "1", start="literal"))
        self.assertEqual(Literal(1.0), Grammar.parse(self.n, "1.0", start="literal"))
        self.assertEqual(Literal("test"), Grammar.parse(self.n, "\"test\"", start="literal"))
        self.assertEqual(Literal("123"), Grammar.parse(self.n, "\"123\"", start="literal"))
        self.assertEqual("12ac3b3", Grammar.parse(self.n, "\"12ac3b3\"", start="literal"))
        self.assertEqual(True, Grammar.parse(self.n, "True", start="literal"))
        self.assertEqual(True, Grammar.parse(self.n, "TRUE", start="literal"))
        self.assertEqual(False, Grammar.parse(self.n, "False", start="literal"))
        self.assertEqual(False, Grammar.parse(self.n, "FaLsE", start="literal"))

    def test_parse_literal_query(self):
        self.assertEqual(LiteralQuery(self.n, 123), Grammar.parse(self.n, "=123", start="literal_query"))
        self.assertEqual(LiteralQuery(self.n, 123), Grammar.parse(self.n, "= 123", start="literal_query"))

    def test_parse_identifier_query(self):
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.EQUALS), Grammar.parse(self.n, "=WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.EQUALS), Grammar.parse(self.n, "= WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.EQUALS, set=False), Grammar.parse(self.n, "=! WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.ISA), Grammar.parse(self.n, "^WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.ISA), Grammar.parse(self.n, "^ WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.ISA, set=False), Grammar.parse(self.n, "^! WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.ISPARENT), Grammar.parse(self.n, "^.WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.ISPARENT), Grammar.parse(self.n, "^. WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.ISPARENT, set=False), Grammar.parse(self.n, "^.! WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.SUBCLASSES), Grammar.parse(self.n, ">WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.SUBCLASSES), Grammar.parse(self.n, "> WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.SUBCLASSES, set=False), Grammar.parse(self.n, ">! WM.HUMAN.1", start="identifier_query"))
        self.assertEqual(IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.SUBCLASSES, from_concept=True), Grammar.parse(self.n, "~> WM.HUMAN.1", start="identifier_query"))

    def test_parse_filler_query(self):
        self.assertEqual(FillerQuery(self.n, LiteralQuery(self.n, 123)), Grammar.parse(self.n, "=123", start="filler_query"))
        self.assertEqual(FillerQuery(self.n, IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.EQUALS)), Grammar.parse(self.n, "=WM.HUMAN.1", start="filler_query"))

    def test_parse_slot_query(self):
        nq = NameQuery(self.n, "THEME")
        fq1 = FillerQuery(self.n, LiteralQuery(self.n, 123))
        fq2 = FillerQuery(self.n, LiteralQuery(self.n, 456))

        self.assertEqual(SlotQuery(self.n, nq), Grammar.parse(self.n, "HAS THEME", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, nq), Grammar.parse(self.n, "has THEME", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, fq1), Grammar.parse(self.n, "* = 123", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, fq1), Grammar.parse(self.n, "* (= 123)", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, AndQuery(self.n, [NameQuery(self.n, "*CTX.SLOT"), fq1])), Grammar.parse(self.n, "*CTX.SLOT = 123", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, AndQuery(self.n, [fq1, fq2])), Grammar.parse(self.n, "* (= 123 AND = 456)", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, AndQuery(self.n, [fq1, fq2])), Grammar.parse(self.n, "* (= 123 and = 456)", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, OrQuery(self.n, [fq1, fq2])), Grammar.parse(self.n, "* (= 123 OR = 456)", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, OrQuery(self.n, [fq1, fq2])), Grammar.parse(self.n, "* (= 123 or = 456)", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, NotQuery(self.n, fq1)), Grammar.parse(self.n, "* NOT = 123", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, NotQuery(self.n, fq1)), Grammar.parse(self.n, "* not = 123", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, NotQuery(self.n, fq1)), Grammar.parse(self.n, "* NOT (= 123)", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, ExactQuery(self.n, [fq1, fq2])), Grammar.parse(self.n, "* EXACTLY (= 123 AND = 456)", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, ExactQuery(self.n, [fq1, fq2])), Grammar.parse(self.n, "* exactly (= 123 AND = 456)", start="slot_query"))
        self.assertEqual(SlotQuery(self.n, AndQuery(self.n, [nq, ExactQuery(self.n, [fq1, fq2])])), Grammar.parse(self.n, "THEME EXACTLY (= 123 AND = 456)", start="slot_query"))

    def test_parse_frame_query(self):
        iq = IdentifierQuery(self.n, "WM.HUMAN.1", IdentifierQuery.Comparator.EQUALS)
        sq1 = SlotQuery(self.n, AndQuery(self.n, [NameQuery(self.n, "THEME"), FillerQuery(self.n, LiteralQuery(self.n, 123))]))
        sq2 = SlotQuery(self.n, AndQuery(self.n, [NameQuery(self.n, "THEME"), FillerQuery(self.n, LiteralQuery(self.n, 456))]))

        self.assertEqual(FrameQuery(self.n, sq1), Grammar.parse(self.n, "WHERE THEME = 123", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, sq1), Grammar.parse(self.n, "where THEME = 123", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, sq1), Grammar.parse(self.n, "SHOW FRAMES WHERE THEME = 123", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, sq1), Grammar.parse(self.n, "show frames where THEME = 123", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, sq1), Grammar.parse(self.n, "WHERE (THEME = 123)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, AndQuery(self.n, [sq1, sq2])), Grammar.parse(self.n, "WHERE (THEME = 123 AND THEME = 456)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, AndQuery(self.n, [sq1, sq2])), Grammar.parse(self.n, "WHERE (THEME = 123 and THEME = 456)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, OrQuery(self.n, [sq1, sq2])), Grammar.parse(self.n, "WHERE (THEME = 123 OR THEME = 456)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, OrQuery(self.n, [sq1, sq2])), Grammar.parse(self.n, "WHERE (THEME = 123 or THEME = 456)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, NotQuery(self.n, sq1)), Grammar.parse(self.n, "WHERE NOT THEME = 123", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, NotQuery(self.n, sq1)), Grammar.parse(self.n, "WHERE not THEME = 123", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, NotQuery(self.n, sq1)), Grammar.parse(self.n, "WHERE NOT (THEME = 123)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, ExactQuery(self.n, [sq1, sq2])), Grammar.parse(self.n, "WHERE EXACTLY (THEME = 123 AND THEME = 456)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, ExactQuery(self.n, [sq1, sq2])), Grammar.parse(self.n, "WHERE exactly (THEME = 123 AND THEME = 456)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, iq), Grammar.parse(self.n, "WHERE @ =WM.HUMAN.1", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, AndQuery(self.n, [iq, sq1])), Grammar.parse(self.n, "WHERE (@ =WM.HUMAN.1 AND THEME = 123)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, OrQuery(self.n, [iq, sq1])), Grammar.parse(self.n, "WHERE (@ =WM.HUMAN.1 OR THEME = 123)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, NotQuery(self.n, iq)), Grammar.parse(self.n, "WHERE NOT (@ =WM.HUMAN.1)", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, NotQuery(self.n, iq)), Grammar.parse(self.n, "WHERE NOT @ =WM.HUMAN.1", start="frame_query"))
        self.assertEqual(FrameQuery(self.n, IdentifierQuery(self.n, "ONT.EVENT", IdentifierQuery.Comparator.ISA)), Grammar.parse(self.n, "WHERE @^ONT.EVENT", start="frame_query"))

    def test_parse_view_graph(self):
        g1 = self.n.register("TEST")
        g2 = self.n.register("TMR#123")
        self.assertEqual(View(self.n, g1), Grammar.parse(self.n, "VIEW TEST SHOW ALL"))
        self.assertEqual(View(self.n, g1), Grammar.parse(self.n, "view TEST show all"))
        self.assertEqual(View(self.n, g2), Grammar.parse(self.n, "view TMR#123 show all"))

    def test_parse_view_graph_with_query(self):
        g = self.n.register("TEST")
        query = FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))
        self.assertEqual(View(self.n, g, query=query), Grammar.parse(self.n, "VIEW TEST SHOW FRAMES WHERE @=TEST.FRAME.1"))
        self.assertEqual(View(self.n, g, query=query), Grammar.parse(self.n, "view TEST show frames where @=TEST.FRAME.1"))

    def test_parse_follow(self):
        self.assertEqual(Path().to("REL"), Grammar.parse(self.n, "[REL]->", start="path"))
        self.assertEqual(Path().to("*"), Grammar.parse(self.n, "[*]->", start="path"))
        self.assertEqual(Path().to("REL1").to("REL2"), Grammar.parse(self.n, "[REL1]->[REL2]->", start="path"))
        self.assertEqual(Path().to("REL1").to("REL2"), Grammar.parse(self.n, "[REL1]-> [REL2]->", start="path"))
        self.assertEqual(Path().to("REL1").to("REL2"), Grammar.parse(self.n, "[REL1]-> THEN [REL2]->", start="path"))
        self.assertEqual(Path().to("REL", recursive=True), Grammar.parse(self.n, "[REL*]->", start="path"))
        self.assertEqual(Path().to("REL", recursive=True), Grammar.parse(self.n, "[REL *]->", start="path"))
        self.assertEqual(Path().to("REL", query=FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))), Grammar.parse(self.n, "[REL]->TO @ = TEST.FRAME.1", start="path"))
        self.assertEqual(Path().to("REL", query=FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))), Grammar.parse(self.n, "[REL]-> TO @ = TEST.FRAME.1", start="path"))
        self.assertEqual(Path().to("REL", query=FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))).to("OTHER"), Grammar.parse(self.n, "[REL]-> TO @ = TEST.FRAME.1 [OTHER]->", start="path"))
        self.assertEqual(Path().to("REL", query=FrameQuery(self.n, IdentifierQuery(self.n, "TEST.FRAME.1", IdentifierQuery.Comparator.EQUALS))).to("OTHER"), Grammar.parse(self.n, "[REL]-> TO @ = TEST.FRAME.1 THEN [OTHER]->", start="path"))

    def test_parse_view_graph_with_path(self):
        g = self.n.register("TEST")
        self.assertEqual(View(self.n, g, follow=Path().to("REL")), Grammar.parse(self.n, "VIEW TEST SHOW ALL FOLLOW [REL]->"))
        self.assertEqual(View(self.n, g, follow=Path().to("REL").to("OTHER")), Grammar.parse(self.n, "view TEST SHOW ALL FOLLOW [REL]->[OTHER]->"))
        self.assertEqual(View(self.n, g, follow=[Path().to("REL1"), Path().to("REL2")]), Grammar.parse(self.n, "view TEST SHOW ALL FOLLOW [REL1]-> AND FOLLOW [REL2]->"))