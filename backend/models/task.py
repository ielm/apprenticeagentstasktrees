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

        self.complex_tasks = []

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
        # for subtask in self.subtasks():
        #     Create Step from subtask
        step = Step.build(self, index, step)
        return step

    def plan(self):
        """
        Generates a plan object with a set of step frames

        :return:
        """
        index = 0

        steps = []

        for subtask in self.subtasks():
            s = self.step(subtask, index)
            index += 1
            steps.append(s)

        # TODO - Create Plan (Action Object) from steps and return Plan

        return steps


class ActionableTask(Frame):

    def __init__(self, task, name, isa=None):
        super().__init__(name, isa=isa)

        for key in task._storage:
            self[key] = task._storage[key]
