from backend.models.graph import Network, Graph, Frame
from backend.utils.AtomicCounter import AtomicCounter
from backend.models.agenda import Step, Plan
from backend.models.output import OutputXMRTemplate
from backend.models.statement import OutputXMRStatement


class ComplexTask(Graph):
    """
    A ComplexTask is a graph that holds ActionableTasks. ActionableTasks are recorded to _storage, whereas ComplexTasks are recorded to an ordered list of ComplexTasks.
    """

    counter = AtomicCounter()

    def __init__(self, agent: Network, task: Frame, namespace: str = None):
        if namespace is None:
            namespace = "COMPLEX-TASK" + str(ComplexTask.counter.increment())

        super().__init__(namespace)
        self.name = namespace

        self.agent = agent

        self.complex_tasks = []

        for key in task:
            # self[key] = task[key].singleton()
            # if key == "AGENT":
                # self[key] = task[key]
                # self.agent = task[key].singleton()
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
            complex_task = ComplexTask(self.agent, task, task.name())
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

    def get_statement(self, step):
        # TODO - return OutputXMRStatement for now. In the future this may also return other statement types
        # step_id = step.name().split(".")[-2]
        template = ""

        # print(step["INSTANCE-OF"])
        ont_event = step["INSTANCE-OF"]
        for t in OutputXMRTemplate.list(self.agent):
            # print(t.capability())
            # if t.name().upper() == step_id:
            #     template = t
            if t.capability()["COVERS-EVENT"].singleton() == ont_event.singleton():
                template = t

        params = [step["AGENT"], step["THEME"]]

        statement = OutputXMRStatement.instance(self.agent['EXE'], template=template, params=params, agent=step["AGENT"])
        return statement

    def step(self, step, index):
        statement = self.get_statement(step=step)
        step = Step.build(self, index, perform=statement)
        return step

    def steps(self):
        index = 0
        steps = []

        for subtask in self.subtasks():
            s = self.step(subtask, index)
            index += 1
            steps.append(s)

        return steps

    def plan(self):
        """
        Generates a plan object with a set of step frames
        :return: Plan
        """
        steps = self.steps()
        plan = Plan.build(self, self.name, Plan.DEFAULT, steps)

        return plan


class ActionableTask(Frame):

    def __init__(self, task, name, isa=None):
        super().__init__(name, isa=isa)

        for key in task._storage:
            self[key] = task._storage[key]
