# from taskmodel import TaskModel
# from models.instructions import Instructions
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase

from unittest import skip


@DeprecationWarning
@skip
class TaskModelTestCase(ApprenticeAgentsTestCase):

    @skip
    def test_model_root(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json')
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=0, terminal=False, type="sequential")

    @skip
    def test_model_one_action(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/actions/get-screwdriver.json'),
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "ROBOT GET(screwdriver)"]), name="ROBOT GET(screwdriver)", children=0, type="leaf")

    @skip
    def test_model_two_actions(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/actions/get-screwdriver.json'),
            self.resource('resources/actions/get-screws.json'),
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=2, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "ROBOT GET(screwdriver)"]), name="ROBOT GET(screwdriver)", children=0, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "ROBOT GET(screws)"]), name="ROBOT GET(screws)", children=0, type="leaf")

    @skip
    def test_model_one_child(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/tmrs/FirstINeedAScrewdriver.json'),
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=1, terminal=False, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER"]), name="EVENT WITH SCREWDRIVER", children=0, terminal=False, type="sequential")

    @skip
    def test_model_two_children(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/tmrs/FirstINeedAScrewdriver.json'),
            self.resource('resources/actions/get-screwdriver.json'),
            self.resource('resources/tmrs/IAlsoNeedABoxOfScrews.json'),
            self.resource('resources/actions/get-screws.json'),
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=2, terminal=False, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER"]), name="EVENT WITH SCREWDRIVER", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER", "ROBOT GET(screwdriver)"]), name="ROBOT GET(screwdriver)", children=0, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH BOX"]), name="EVENT WITH BOX", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH BOX", "ROBOT GET(screws)"]), name="ROBOT GET(screws)", children=0, type="leaf")

    @skip
    def test_model_inject_prefix_before_actions(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/actions/get-screwdriver.json'),
            self.resource('resources/tmrs/FirstINeedAScrewdriver.json'),
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=1, terminal=False, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER"]), name="EVENT WITH SCREWDRIVER", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER", "ROBOT GET(screwdriver)"]), name="ROBOT GET(screwdriver)", children=0, terminal=False, type="leaf")

    @skip
    def test_model_closed_prefix(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/tmrs/IWillBuildALeg.json'),
            self.resource('resources/actions/get-screwdriver.json'),
            self.resource('resources/tmrs/IBuiltALeg.json'),
        ]

        tm = TaskModel()
        model = tm.learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=0, terminal=False, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD ARTIFACT-LEG"]), name="BUILD ARTIFACT-LEG", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD ARTIFACT-LEG", "ROBOT GET(screwdriver)"]), name="ROBOT GET(screwdriver)", children=0, terminal=False, type="leaf")
        self.assertEqual(tm.active_node, model.find(["BUILD CHAIR"]))

    @skip
    def test_model_presumed_event(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/tmrs/IWillBuildALeg.json'),
            self.resource('resources/actions/get-screwdriver.json'),
            self.resource('resources/tmrs/IBuiltALeg.json'),
            self.resource('resources/actions/get-screws.json'),
            self.resource('resources/tmrs/IBuiltASeat.json'),
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=2, terminal=False, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD ARTIFACT-LEG"]), name="BUILD ARTIFACT-LEG", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD ARTIFACT-LEG", "ROBOT GET(screwdriver)"]), name="ROBOT GET(screwdriver)", children=0, terminal=False, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD SEAT"]), name="BUILD SEAT", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD SEAT", "ROBOT GET(screws)"]), name="ROBOT GET(screws)", children=0, terminal=False, type="leaf")

    @skip
    def test_model_inject_postfix_between_events(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/tmrs/IWillBuildALeg.json'),
            self.resource('resources/actions/get-screwdriver.json'),
            self.resource('resources/tmrs/IBuiltASeat.json'),
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=1, terminal=False, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD SEAT"]), name="BUILD SEAT", children=1, terminal=False, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD SEAT", "BUILD ARTIFACT-LEG"]), name="BUILD ARTIFACT-LEG", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD SEAT", "BUILD ARTIFACT-LEG", "ROBOT GET(screwdriver)"]), name="ROBOT GET(screwdriver)", children=0, terminal=False, type="leaf")

    @skip
    def test_model_inject_postfix_before_actions(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/actions/get-screwdriver.json'),
            self.resource('resources/actions/get-screws.json'),
            self.resource('resources/tmrs/IBuiltALeg.json'),
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=1, terminal=False, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD ARTIFACT-LEG"]), name="BUILD ARTIFACT-LEG", children=2, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD ARTIFACT-LEG", "ROBOT GET(screwdriver)"]), name="ROBOT GET(screwdriver)", children=0, terminal=False, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD ARTIFACT-LEG", "ROBOT GET(screws)"]), name="ROBOT GET(screws)", children=0, terminal=False, type="leaf")

    @skip
    def test_model_postfix_causes_disputes(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/tmrs/FirstINeedAScrewdriver.json'),
            self.resource('resources/actions/get-screwdriver.json'),
            self.resource('resources/actions/get-screws.json'),
            self.resource('resources/tmrs/IConnectedTheBackToTheSeat.json'),
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=2, terminal=False, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER"]), name="EVENT WITH SCREWDRIVER", children=2, terminal=True, type="sequential", disputed=model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT"]))
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER", "ROBOT GET(screwdriver)"]), name="ROBOT GET(screwdriver)", children=0, terminal=False, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER", "ROBOT GET(screws)"]), name="ROBOT GET(screws)", children=0, terminal=False, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT"]), name="ATTACH CHAIR-BACK AND SEAT", children=2, terminal=True, type="sequential", disputed=model.find(["BUILD CHAIR", "BUILD ARTIFACT-LEG"]))
        self.assertNode(model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT", "ROBOT GET(screwdriver)"]), name="ROBOT GET(screwdriver)", children=0, terminal=False, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT", "ROBOT GET(screws)"]), name="ROBOT GET(screws)", children=0, terminal=False, type="leaf")

        self.assertTrue(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER"]).childrenStatus[0])
        self.assertTrue(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER"]).childrenStatus[1])
        self.assertTrue(model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT"]).childrenStatus[0])
        self.assertTrue(model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT"]).childrenStatus[1])

    @skip
    def test_model_settle_disputes(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/tmrs/FirstINeedAScrewdriver.json'),
            self.resource('resources/actions/get-screwdriver.json'),
            self.resource('resources/actions/get-screws.json'),
            self.resource('resources/tmrs/IConnectedTheBackToTheSeat.json'),
            self.resource('resources/tmrs/IWillBuildASeat.json'),
            self.resource('resources/tmrs/FirstINeedAScrewdriver.json'),
            self.resource('resources/actions/get-screwdriver.json'),
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=3, terminal=False, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER"]), name="EVENT WITH SCREWDRIVER", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER", "ROBOT GET(screwdriver)"]), name="ROBOT GET(screwdriver)", children=0, terminal=False, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT"]), name="ATTACH CHAIR-BACK AND SEAT", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT", "ROBOT GET(screws)"]), name="ROBOT GET(screws)", children=0, terminal=False, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD SEAT"]), name="BUILD SEAT", children=1, terminal=False, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD SEAT", "EVENT WITH SCREWDRIVER"]), name="EVENT WITH SCREWDRIVER", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD SEAT", "EVENT WITH SCREWDRIVER", "ROBOT GET(screwdriver)"]), name="ROBOT GET(screwdriver)", children=0, terminal=False, type="leaf")

        self.assertFalse(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER"]).childrenStatus[0])
        self.assertFalse(model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT"]).childrenStatus[0])
        self.assertFalse(model.find(["BUILD CHAIR", "BUILD SEAT", "EVENT WITH SCREWDRIVER"]).childrenStatus[0])

    @skip
    def test_model_find_parallels(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/tmrs/IWillBuildALeg.json'),
            self.resource('resources/actions/get-screwdriver.json'),
            self.resource('resources/actions/get-screws.json'),
            self.resource('resources/tmrs/IBuiltALeg.json'),
            self.resource('resources/tmrs/IWillBuildALeg.json'),
            self.resource('resources/actions/get-screws.json'),
            self.resource('resources/actions/get-screwdriver.json'),
            self.resource('resources/tmrs/IBuiltALeg.json'),
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=2, terminal=False, type="sequential")
        self.assertNode(model.find_all(["BUILD CHAIR", "BUILD ARTIFACT-LEG"])[0], name="BUILD ARTIFACT-LEG", children=2, terminal=True, type="sequential", relationships=[[0, 0], [0, 0]])
        self.assertNode(model.find_all(["BUILD CHAIR", "BUILD ARTIFACT-LEG"])[1], name="BUILD ARTIFACT-LEG", children=2, terminal=True, type="sequential", relationships=[[0, 0], [0, 0]])

    @skip
    def test_model_multiple_inputs(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
        ]

        tm = TaskModel()

        model = tm.learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=0, terminal=False, type="sequential")

        input = [
            self.resource('resources/actions/get-screwdriver.json'),
        ]

        model = tm.learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "ROBOT GET(screwdriver)"]), name="ROBOT GET(screwdriver)", children=0, type="leaf")

    @skip
    def test_model_query(self):
        import os
        file = os.path.abspath(__package__) + "/resources/DemoMay2018_TMRs.json"
        demo = self.resource(file)

        input = [
            demo[0],  # We will build a chair.

            demo[3],  # First, we will build a front leg of the chair.
            demo[4],  # Get a foot bracket.
            demo[10],  # We have assembled a front leg.

            demo[40],  # Now we need to assemble the back.
            demo[42],  # Get a top bracket.
            demo[56],  # We have assembled the back.

            demo[68],  # We finished assembling the chair.
        ]

        tm = TaskModel()
        model = tm.learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=2, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD ARTIFACT-LEG"]), name="BUILD ARTIFACT-LEG", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD ARTIFACT-LEG", "ROBOT GET(FOOT_BRACKET)"]), name="ROBOT GET(FOOT_BRACKET)", children=0, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD BACK-OF-OBJECT"]), name="BUILD BACK-OF-OBJECT", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD BACK-OF-OBJECT", "ROBOT GET(bracket-top)"]), name="ROBOT GET(bracket-top)", children=0, type="leaf")

        query = demo[69]  # We will build the back first.

        from backend.models.tmr import TMR
        model = tm.query(TMR(query))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=2, type="sequential")
        self.assertEqual(list(map(lambda node: node.name, model.find(["BUILD CHAIR"]).children)), ["BUILD BACK-OF-OBJECT", "BUILD ARTIFACT-LEG"])

        self.assertEqual(list(map(lambda node: node.name, tm.root.find(["BUILD CHAIR"]).children)), ["BUILD ARTIFACT-LEG", "BUILD BACK-OF-OBJECT"])