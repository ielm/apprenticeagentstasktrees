

import unittest


class Jan2019Experiment(unittest.TestCase):

    def test_1_1(self):
        fail()

        # Pa) Load LTM with the chair building instructions, as taught by "Jake"
        # Pb) Load WM with an instance of "Jake", location = "here";  Possibly use an ENV graph (see 3b).
        # Pc) All other typical bootstrapping is done as well

        # 1a) Input from "Jake", "Let's build a chair."
        # 1b) IIDEA loop
        # 1c) TEST: An instance of ACKNOWLEDGE-INPUT with the correct TMR is on the agenda
        # 1d) IIDEA loop
        # 1e) TEST: An instance of DECIDE-ON-LANGUAGE-INPUT with the correct TMR is on the agenda
        # 1f) IIDEA loop
        # 1g) TEST: An instance of PERFORM-COMPLEX-TASK with the LTM instructions root is on the agenda

        # 2a) Visual input "Jake leaves"
        # 2b) IIDEA loop
        # 2c) TEST: An instance of ACKNOWLEDGE-INPUT with the correct TMR is on the agenda
        # 2d) TEST: The only PHYSICAL-EFFECTOR is reserved to PERFORM-COMPLEX-TASK (using capability GET(screwdriver))
        # 2e) IIDEA loop
        # 2f) TEST: An instance of REACT-TO-VISUAL-INPUT with the correct VMR is on the agenda
        # 2g) TEST: The PHYSICAL-EFFECTOR is still reserved; PERFORM-COMPLEX-TASK is still "active"
        # 2h) IIDEA loop
        # 2i) TEST: REACT-TO-VISUAL-INPUT is satisfied (only 2 goals: FSTD and PERFORM-COMPLEX-TASK)
        # 2j) TEST: The PHYSICAL-EFFECTOR is still reserved; PERFORM-COMPLEX-TASK is still "active"

        # 3a) Callback input capability GET(screwdriver) is complete
        # 3b) MOCK: The status of the screwdriver must be changed in WM (to reflect what would happen in a real environment)
        #           Should we have an ENV graph?  Probably.
        # 3c) IIDEA loop
        # 3d) TEST: The only PHYSICAL-EFFECTOR is reserved to PERFORM-COMPLEX-TASK (using capability GET(foot_bracket))
        # 3e) TEST: PERFORM-COMPLEX-TASK is still "active"

        # 4a) Visual input "Jake returns"
        # 4b) IIDEA loop
        # 4c) TEST: An instance of ACKNOWLEDGE-INPUT with the correct TMR is on the agenda
        # 4d) TEST: PERFORM-COMPLEX-TASK is still "active"
        # 4e) IIDEA loop
        # 4f) TEST: An instance of REACT-TO-VISUAL-INPUT with the correct VMR is on the agenda
        # 4g) TEST: PERFORM-COMPLEX-TASK is still "active"
        # 4h) IIDEA loop
        # 4i) TEST: An instance of ACKNOWLEDGE-HUMAN with the correct @human instance is on the agenda
        # 4j) TEST: PERFORM-COMPLEX-TASK is still "active"
        # 4k) IIDEA loop
        # 4l) TEST: The only VERBAL-EFFECTOR is reserved to ACKNOWLEDGE-HUMAN (using capability SPEAK("Hi Jake."))
        # 4m) TEST: ACKNOWLEDGE-HUMAN is "active"
        # 4n) TEST: PERFORM-COMPLEX-TASK is still "active"

        # 5a) Callback input capability SPEAK("Hi Jake.") is complete
        # 5b) IIDEA loop
        # 5c) TEST: ACKNOWLEDGE-HUMAN is "satisfied"
        # 5d) TEST: PERFORM-COMPLEX-TASK is still "active"

        # 6a) Input from "Jake", "What are you doing?"
        # 6b) IIDEA loop
        # 6c) TEST: An instance of ACKNOWLEDGE-INPUT with the correct TMR is on the agenda
        # 6d) TEST: PERFORM-COMPLEX-TASK is still "active"
        # 6e) IIDEA loop
        # 6f) TEST: An instance of DECIDE-ON-LANGUAGE-INPUT with the correct TMR is on the agenda
        # 6g) TEST: PERFORM-COMPLEX-TASK is still "active"
        # 6h) IIDEA loop
        # 6i) TEST: An instance of RESPOND-TO-QUERY with the LTM instructions root is on the agenda
        # 6j) TEST: PERFORM-COMPLEX-TASK is still "active"
        # 6k) IIDEA loop
        # 6l) TEST: The only VERBAL-EFFECTOR is reserved to RESPOND-TO-QUERY (using capability SPEAK("I am fetching a foot bracket."))
        # 6m) TEST: PERFORM-COMPLEX-TASK is still "active"

        # 7a) Callback input capability SPEAK("I am fetching a front bracket.") is complete
        # 7b) IIDEA loop
        # 7c) TEST: RESPOND-TO-QUERY is "satisfied"
        # 7d) TEST: PERFORM-COMPLEX-TASK is still "active"

        # 8a) Callback input capability GET(foot_bracket)
        # 8b) IIDEA loop
        # 8c) TEST: The PHYSICAL-EFFECTOR is released
        # 8d) TEST: PERFORM-COMPLEX-TASK is still "active" (the chair is not yet built)


