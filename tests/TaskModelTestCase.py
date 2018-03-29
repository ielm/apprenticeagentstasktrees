from taskmodel import TaskModel
from instructions import Instructions
from tests.ApprenticeAgentsTestCase import ApprenticeAgentsTestCase


class TaskModelTestCase(ApprenticeAgentsTestCase):

    def test_model_root(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json')
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=0, terminal=False, type="sequential")

    def test_model_one_action(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/actions/get-screwdriver.json'),
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "REQUEST-ACTION TAKE SCREWDRIVER"]), name="REQUEST-ACTION TAKE SCREWDRIVER", children=0, type="leaf")

    def test_model_two_actions(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/actions/get-screwdriver.json'),
            self.resource('resources/actions/get-screws.json'),
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=2, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "REQUEST-ACTION TAKE SCREWDRIVER"]), name="REQUEST-ACTION TAKE SCREWDRIVER", children=0, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "REQUEST-ACTION TAKE SCREW"]), name="REQUEST-ACTION TAKE SCREW", children=0, type="leaf")

    def test_model_one_child(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/tmrs/FirstINeedAScrewdriver.json'),
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=1, terminal=False, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER"]), name="EVENT WITH SCREWDRIVER", children=0, terminal=False, type="sequential")

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
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER", "REQUEST-ACTION TAKE SCREWDRIVER"]), name="REQUEST-ACTION TAKE SCREWDRIVER", children=0, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH BOX"]), name="EVENT WITH BOX", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH BOX", "REQUEST-ACTION TAKE SCREW"]), name="REQUEST-ACTION TAKE SCREW", children=0, type="leaf")

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
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER", "REQUEST-ACTION TAKE SCREWDRIVER"]), name="REQUEST-ACTION TAKE SCREWDRIVER", children=0, terminal=False, type="leaf")

    def test_model_closed_prefix(self):
        input = [
            self.resource('resources/tmrs/IPlanToBuildAChair.json'),
            self.resource('resources/tmrs/ThatsIt.json'),
        ]

        model = TaskModel().learn(Instructions(input))

        self.assertNode(model, children=1)
        self.assertNode(model.find(["BUILD CHAIR"]), name="BUILD CHAIR", children=0, terminal=False, type="sequential")

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
        self.assertNode(model.find(["BUILD CHAIR", "BUILD ARTIFACT-LEG", "REQUEST-ACTION TAKE SCREWDRIVER"]), name="REQUEST-ACTION TAKE SCREWDRIVER", children=0, terminal=False, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD SEAT"]), name="BUILD SEAT", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD SEAT", "REQUEST-ACTION TAKE SCREW"]), name="REQUEST-ACTION TAKE SCREW", children=0, terminal=False, type="leaf")

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
        self.assertNode(model.find(["BUILD CHAIR", "BUILD SEAT", "BUILD ARTIFACT-LEG", "REQUEST-ACTION TAKE SCREWDRIVER"]), name="REQUEST-ACTION TAKE SCREWDRIVER", children=0, terminal=False, type="leaf")

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
        self.assertNode(model.find(["BUILD CHAIR", "BUILD ARTIFACT-LEG", "REQUEST-ACTION TAKE SCREWDRIVER"]), name="REQUEST-ACTION TAKE SCREWDRIVER", children=0, terminal=False, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD ARTIFACT-LEG", "REQUEST-ACTION TAKE SCREW"]), name="REQUEST-ACTION TAKE SCREW", children=0, terminal=False, type="leaf")

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
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER", "REQUEST-ACTION TAKE SCREWDRIVER"]), name="REQUEST-ACTION TAKE SCREWDRIVER", children=0, terminal=False, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER", "REQUEST-ACTION TAKE SCREW"]), name="REQUEST-ACTION TAKE SCREW", children=0, terminal=False, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT"]), name="ATTACH CHAIR-BACK AND SEAT", children=2, terminal=True, type="sequential", disputed=model.find(["BUILD CHAIR", "BUILD ARTIFACT-LEG"]))
        self.assertNode(model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT", "REQUEST-ACTION TAKE SCREWDRIVER"]), name="REQUEST-ACTION TAKE SCREWDRIVER", children=0, terminal=False, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT", "REQUEST-ACTION TAKE SCREW"]), name="REQUEST-ACTION TAKE SCREW", children=0, terminal=False, type="leaf")

        self.assertTrue(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER"]).childrenStatus[0])
        self.assertTrue(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER"]).childrenStatus[1])
        self.assertTrue(model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT"]).childrenStatus[0])
        self.assertTrue(model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT"]).childrenStatus[1])

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
        self.assertNode(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER", "REQUEST-ACTION TAKE SCREWDRIVER"]), name="REQUEST-ACTION TAKE SCREWDRIVER", children=0, terminal=False, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT"]), name="ATTACH CHAIR-BACK AND SEAT", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT", "REQUEST-ACTION TAKE SCREW"]), name="REQUEST-ACTION TAKE SCREW", children=0, terminal=False, type="leaf")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD SEAT"]), name="BUILD SEAT", children=1, terminal=False, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD SEAT", "EVENT WITH SCREWDRIVER"]), name="EVENT WITH SCREWDRIVER", children=1, terminal=True, type="sequential")
        self.assertNode(model.find(["BUILD CHAIR", "BUILD SEAT", "EVENT WITH SCREWDRIVER", "REQUEST-ACTION TAKE SCREWDRIVER"]), name="REQUEST-ACTION TAKE SCREWDRIVER", children=0, terminal=False, type="leaf")

        self.assertFalse(model.find(["BUILD CHAIR", "EVENT WITH SCREWDRIVER"]).childrenStatus[0])
        self.assertFalse(model.find(["BUILD CHAIR", "ATTACH CHAIR-BACK AND SEAT"]).childrenStatus[0])
        self.assertFalse(model.find(["BUILD CHAIR", "BUILD SEAT", "EVENT WITH SCREWDRIVER"]).childrenStatus[0])

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
        self.assertNode(model.find(["BUILD CHAIR", "REQUEST-ACTION TAKE SCREWDRIVER"]), name="REQUEST-ACTION TAKE SCREWDRIVER", children=0, type="leaf")
