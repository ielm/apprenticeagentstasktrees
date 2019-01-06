from backend.models.graph import Graph, Frame
from backend.utils.AtomicCounter import AtomicCounter
from backend.models.agenda import Step, Action


class ComplexTask(Graph):
    """
    A ComplexTask is a graph that holds ActionableTasks. ActionableTasks are recorded to _storage, whereas ComplexTasks are recorded to an ordered list of ComplexTasks.
    """

    counter = AtomicCounter()

    def __init__(self, task: Frame, namespace: str = None):
        if namespace is None:
            namespace = "COMPLEX-TASK" + str(ComplexTask.counter.increment())

        super().__init__(namespace)
        self.name = namespace

        self.complex_tasks = []

        for key in task:
            # self[key] = task[key].singleton()
            if key == "AGENT":
                # self[key] = task[key]
                self.agent = task[key].singleton()
            if key == "INSTRUMENT":
                self.instrument = task[key].singleton()
            if key == "THEME":
                self.theme = task[key].singleton()
        for subtask in task["HAS-EVENT-AS-PART"]:
            self.add_task(subtask.resolve())

    def add_task(self, task):
        if "HAS-EVENT-AS-PART" not in task._storage:
            actionable_task = ActionableTask(task, task.name(), task["INSTANCE-OF"])
            self[task.name()] = actionable_task
        else:
            complex_task = ComplexTask(task, task.name())
            self.complex_tasks.append(complex_task)

            for subtask in complex_task.subtasks():
                self.add_task(subtask)

            # for subtask in task["HAS-EVENT-AS-PART"]:
                # self.add_task(subtask.resolve())

    def subtasks(self):
        subtasks = []

        for item in self._storage:
            subtasks.append(self._storage[item])

        return subtasks

    def step(self, step, index, statement=None):
        print("Step: ", step)
        print("Type: ", type(step))
        step = Step.build(self, index, step)
        return step

    def steps(self):
        index = 0

        steps = []

        for subtask in self.subtasks():
            # TODO - should Step.build["PERFORM"] be the MP or target goal?
            s = self.step(subtask, index)
            # s = Step.build(self, index, subtask)
            index += 1
            steps.append(s)

        return steps

    def plan(self):
        """
        Generates a plan object with a set of step frames

        :return:
        """
        steps = self.steps()

        plan = Action.build(self, self.name, Action.DEFAULT, steps)

        return plan


class ActionableTask(Frame):

    def __init__(self, task, name, isa=None):
        super().__init__(name, isa=isa)

        for key in task._storage:
            self[key] = task._storage[key]
