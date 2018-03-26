import json
import unittest
import maketree


class MakeTreeTestCase(unittest.TestCase):

    def resource(self, fp):
        r = None
        with open(fp) as f:
            r = json.load(f)
        return r

    def assertNode(self, node, name=None, children=None, terminal=None, type=None):
        if name:
            self.assertEqual(node.name, name)
        if children:
            self.assertEqual(len(node.children), children)
        if terminal is not None:
            self.assertEqual(node.terminal, terminal)
        if type:
            self.assertEqual(node.type, type)

    def test_tree_root(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json')
        ]

        tree = maketree.construct_tree(input, [])

        self.assertNode(tree, children=1)
        self.assertNode(tree.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=0, terminal=False, type="sequential")

    def test_tree_one_action(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/actions/get-screwdriver.json'),
        ]

        tree = maketree.construct_tree(input, [])

        self.assertNode(tree, children=1)
        self.assertNode(tree.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=1, terminal=True, type="sequential")
        self.assertNode(tree.find(["BUILD CHAIR", "get-screwdriver"]), name="get-screwdriver", children=0, type="leaf")

    def test_tree_two_actions(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/actions/get-screwdriver.json'),
            self.resource('resources/actions/get-screws.json'),
        ]

        tree = maketree.construct_tree(input, [])

        self.assertNode(tree, children=1)
        self.assertNode(tree.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=2, terminal=True, type="sequential")
        self.assertNode(tree.find(["BUILD CHAIR", "get-screwdriver"]), name="get-screwdriver", children=0, type="leaf")
        self.assertNode(tree.find(["BUILD CHAIR", "get-screws"]), name="get-screws", children=0, type="leaf")

    def test_tree_one_child(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/tmrs/FirstINeedAScrewdriver.json'),
        ]

        tree = maketree.construct_tree(input, [])

        self.assertNode(tree, children=1)
        self.assertNode(tree.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=1, terminal=False, type="sequential")
        self.assertNode(tree.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER"]), name="EVENT WITH SCREWDRIVER", children=0, terminal=False, type="sequential")

    def test_tree_two_children(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/tmrs/FirstINeedAScrewdriver.json'),
            self.resource('resources/actions/get-screwdriver.json'),
            self.resource('resources/tmrs/IAlsoNeedABoxOfScrews.json'),
            self.resource('resources/actions/get-screws.json'),
        ]

        tree = maketree.construct_tree(input, [])

        self.assertNode(tree, children=1)
        self.assertNode(tree.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=2, terminal=False, type="sequential")
        self.assertNode(tree.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER"]), name="EVENT WITH SCREWDRIVER", children=1, terminal=True, type="sequential")
        self.assertNode(tree.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER", "get-screwdriver"]), name="get-screwdriver", children=0, type="leaf")
        self.assertNode(tree.find(["BUILD CHAIR", "EVENT WITH BOX"]), name="EVENT WITH BOX", children=1, terminal=True, type="sequential")
        self.assertNode(tree.find(["BUILD CHAIR", "EVENT WITH BOX", "get-screws"]), name="get-screws", children=0, type="leaf")

    def test_tree_closed_prefix(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/tmrs/ThatsIt.json'),
        ]

        tree = maketree.construct_tree(input, [])

        self.assertNode(tree, children=1)
        self.assertNode(tree.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=0, terminal=False, type="sequential")


if __name__ == '__main__':
    unittest.main()
