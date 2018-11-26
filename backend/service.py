import json
import traceback
from flask import Flask, redirect, request, abort, render_template, send_from_directory
from flask_cors import CORS


from backend.agent import Agent
from backend.models.effectors import Callback
from backend.models.bootstrap import Bootstrap
from backend.contexts.LCTContext import LCTContext
from backend.models.agenda import Action, Goal
from backend.models.grammar import Grammar
from backend.models.graph import Frame, Identifier, Literal
from backend.models.ontology import Ontology
from backend.models.xmr import XMR
from backend.utils.AgentLogger import CachedAgentLogger
from backend.utils.YaleUtils import format_learned_event_yale, input_to_tmrs

app = Flask(__name__, template_folder="../frontend/templates/")
CORS(app)


# n = Network()
# ontology = n.register(Ontology.init_default())
agent = Agent(ontology=Ontology.init_default())
agent.logger().enable()

# TEST HACK
from pkgutil import get_data
# agent.input(json.loads(get_data("tests.resources", "DemoMay2018_Analyses.json"))[0])
# agent.input(json.loads(get_data("tests.resources", "DemoMay2018_Analyses.json"))[1])
# agent.input(json.loads(get_data("tests.resources", "DemoMay2018_Analyses.json"))[2])
# agent.input(json.loads(get_data("tests.resources", "DemoMay2018_Analyses.json"))[3])
# agent.input(json.loads(get_data("tests.resources", "DemoMay2018_Analyses.json"))[4])
# agent.input(json.loads(get_data("tests.resources", "DemoMay2018_Analyses.json"))[5])
# agent.input(json.loads(get_data("tests.resources", "DemoMay2018_Analyses.json"))[6])
# agent.input(json.loads(get_data("tests.resources", "DemoMay2018_Analyses.json"))[7])
# agent.input(json.loads(get_data("tests.resources", "DemoMay2018_Analyses.json"))[8])
# agent.input(json.loads(get_data("tests.resources", "DemoMay2018_Analyses.json"))[9])
# agent.input(json.loads(get_data("tests.resources", "DemoMay2018_Analyses.json"))[10])
# agent.input(json.loads(get_data("tests.resources", "DemoMay2018_Analyses.json"))[11])


def graph_to_json(graph):
    frames = []

    for f in graph:
        frame = graph[f]

        converted = {
            "type": frame.__class__.__name__,
            "graph": graph._namespace if frame._identifier.graph is None else frame._identifier.graph,
            "name": frame._identifier.render(graph=False),
            "relations": [],
            "attributes": []
        }

        for s in frame:
            slot = frame[s]
            for filler in slot:
                if isinstance(filler._value, Identifier):

                    modified = Identifier(filler._value.graph, filler._value.name, instance=filler._value.instance)
                    if modified.graph is None:
                        modified.graph = graph._namespace

                    converted["relations"].append({
                        "graph": modified.graph,
                        "slot": s,
                        "value": modified.render(graph=False),
                    })
                else:
                    value = filler._value.value
                    if isinstance(value, type):
                        value = value.__module__ + '.' + value.__name__
                    elif isinstance(value, int):
                        value = value
                    else:
                        value = str(value)

                    converted["attributes"].append({
                        "slot": s,
                        "value": value
                    })

        frames.append(converted)

    return json.dumps(frames)


@app.errorhandler(Exception)
def server_error(error):
    tb_str = traceback.format_exc()
    app.logger.debug(tb_str)
    return tb_str, 500, {"Access-Control-Allow-Origin": "*"}


@app.route('/assets/<path:filename>', methods=['GET'])
def servefile(filename):
  return send_from_directory("../frontend/assets/", filename)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", network=agent._storage.keys())


@app.route("/grammar", methods=["GET"])
def grammar():
    return render_template("grammar.html")


@app.route("/reset", methods=["DELETE"])
def reset():
    # global n
    # global ontology
    global agent

    # n = Network()
    # ontology = n.register(Ontology.init_default())
    agent = Agent(Ontology.init_default())

    return "OK"


@app.route("/network", methods=["GET"])
def network():
    return json.dumps(list(agent._storage.keys()))


@app.route("/view", methods=["POST"])
def view():
    data = request.data.decode("utf-8")
    view = Grammar.parse(agent, data)
    view_graph = view.view()
    return graph_to_json(view_graph)


@app.route("/graph", methods=["GET"])
def graph():
    if "id" not in request.args:
        abort(400)

    id = request.args["id"]

    return graph_to_json(agent[id])


class IIDEAConverter(object):

    @classmethod
    def inputs(cls):
        return list(map(lambda input: IIDEAConverter.convert_input(input.resolve()), agent.identity["HAS-INPUT"]))

    @classmethod
    def convert_input(cls, input):
        status = XMR(input).status().value.lower()

        return {
            "name": input["REFERS-TO-GRAPH"][0].resolve().value,
            "status": status
        }

    @classmethod
    def agenda(cls):
        return list(map(lambda goal: IIDEAConverter.convert_goal(goal.resolve()), agent.identity["HAS-GOAL"]))

    @classmethod
    def convert_goal(cls, goal):
        goal = Goal(goal)

        return {
            "name": goal.name(),
            "id": goal.frame.name(),
            "priority": goal._cached_priority(),
            "resources": goal._cached_resources(),
            "decision": round(goal.decision(), 3),
            "pending": goal.is_pending(),
            "active": goal.is_active(),
            "satisfied": goal.is_satisfied(),
            "abandoned": goal.is_abandoned(),
            "plan": list(map(lambda action: IIDEAConverter.convert_action(action.resolve(), goal), goal.frame["PLAN"])),
            "params": list(map(lambda variable: {"var": variable, "value": IIDEAConverter.convert_value(goal.resolve(variable))}, goal.variables()))
        }

    @classmethod
    def convert_value(cls, value):
        if isinstance(value, Literal):
            return value.value
        if isinstance(value, Frame):
            return value._identifier.render()
        if isinstance(value, Identifier):
            return value.render()
        return value

    @classmethod
    def convert_action(cls, action, goal):
        action = Action(action)

        return {
            "name": action.name(),
            "selected": action in agent.agenda().action() and goal.is_active(),
            "current-step": len(list(filter(lambda step: step.is_finished(), action.steps()))),
            "total-steps": len(action.steps())
        }

    @classmethod
    def effectors(cls):
        return list(map(lambda e: IIDEAConverter.convert_effector(e), agent.effectors()))

    @classmethod
    def convert_effector(cls, effector):
        return {
            "name": effector.frame.name(),
            "type": effector.type().name,
            "status": effector.is_free(),
            "effecting": effector.effecting().frame.name() if effector.effecting() is not None else None,
            "capabilities": list(map(lambda c: IIDEAConverter.convert_capability(c, effector), effector.capabilities()))
        }

    @classmethod
    def convert_capability(cls, capability, wrt_effector):
        return {
            "name": capability.frame.name(),
            "selected": capability.used_by() == wrt_effector,
            "callbacks": list(map(lambda cb: cb.name(), Callback.find(agent, wrt_effector, capability)))
        }

    @classmethod
    def triggers(cls):
        return list(map(lambda t: IIDEAConverter.convert_trigger(t), agent.agenda().triggers()))

    @classmethod
    def convert_trigger(cls, trigger):
        return {
            "query": str(trigger.query()),
            "goal": trigger.definition().name(),
            "triggered-on": list(map(lambda to: str(to), trigger.triggered_on()))
        }

    @classmethod
    def logs(cls):
        if isinstance(agent.logger(), CachedAgentLogger):
            return agent.logger()._cache
        return []


@app.route("/iidea", methods=["GET"])
def iidea():
    time = agent.IDEA.time()
    stage = agent.IDEA.stage()
    inputs = IIDEAConverter.inputs()
    agenda = IIDEAConverter.agenda()
    effectors = IIDEAConverter.effectors()
    triggers = IIDEAConverter.triggers()
    logs = IIDEAConverter.logs()

    return render_template("iidea.html", time=time, stage=stage, inputs=inputs, agenda=agenda, aj=json.dumps(agenda), effectors=effectors, ej=json.dumps(effectors), tj=json.dumps(triggers), lj=json.dumps(logs))


@app.route("/iidea/advance", methods=["GET"])
def iidea_advance():
    agent.iidea()
    return json.dumps({
        "time": agent.IDEA.time(),
        "stage": agent.IDEA.stage(),
        "inputs": IIDEAConverter.inputs(),
        "agenda": IIDEAConverter.agenda(),
        "effectors": IIDEAConverter.effectors(),
        "triggers": IIDEAConverter.triggers(),
        "logs": IIDEAConverter.logs()
    })


@app.route("/iidea/input", methods=["POST"])
def iidea_input():
    if not request.get_json():
        abort(400)

    data = request.get_json()

    if data["input"] == "Let's build a chair.":
        tmr = json.loads(get_data("tests.resources", "DemoJan2019_Analyses.json").decode('ascii'))[0]
    else:
        from backend.utils.YaleUtils import analyze
        tmr = analyze(data["input"])

    agent._input(input=tmr, source=data["source"], type=data["type"])

    return json.dumps({
        "time": agent.IDEA.time(),
        "stage": agent.IDEA.stage(),
        "inputs": IIDEAConverter.inputs(),
        "agenda": IIDEAConverter.agenda()
    })


@app.route("/iidea/observe", methods=["POST"])
def iidea_observe():
    if not request.get_json():
        abort(400)

    data = request.get_json()

    observations = json.loads(get_data("tests.resources", "DemoJan2019_Observations_VMR.json").decode('ascii'))
    observation = observations[data["observation"]]
    agent._input(observation, type=XMR.Type.VISUAL.name)

    return json.dumps({
        "time": agent.IDEA.time(),
        "stage": agent.IDEA.stage(),
        "inputs": IIDEAConverter.inputs(),
        "agenda": IIDEAConverter.agenda()
    })


@app.route("/iidea/callback", methods=["POST"])
def iidea_callback():
    if not request.get_json():
        abort(400)

    data = request.get_json()

    callback = data["callback-id"]
    agent.callback(callback)

    return json.dumps({
        "time": agent.IDEA.time(),
        "stage": agent.IDEA.stage(),
        "inputs": IIDEAConverter.inputs(),
        "agenda": IIDEAConverter.agenda(),
        "effectors": IIDEAConverter.effectors(),
        "triggers": IIDEAConverter.triggers(),
        "logs": IIDEAConverter.logs()
    })


@app.route("/input", methods=["POST"])
def input():
    if not request.get_json():
        abort(400)

    data = request.get_json()
    tmrs = input_to_tmrs(data)

    for tmr in tmrs:
        agent.input(tmr)

    if isinstance(agent.context, LCTContext):
        learning = list(map(lambda instance: instance.name(), agent.wo_memory.search(Frame.q(network).f(LCTContext.LEARNING, True))))
        return json.dumps({
            LCTContext.LEARNING: learning
        })

    return "OK"


@app.route("/htn", methods=["GET"])
def htn():
    if "instance" not in request.args:
        return render_template("htn.html")

    instance = request.args["instance"]

    from backend.models.fr import FRInstance
    instance: FRInstance = agent.search(Frame.q(agent).id(instance))[0]

    return json.dumps(format_learned_event_yale(instance, agent.ontology), indent=4)


@app.route("/bootstrap", methods=["GET", "POST"])
def bootstrap():
    if request.method == "POST":
        script = request.form["custom-bootstrap"]
        script = script.replace("\r\n", "\n")
        Bootstrap.bootstrap_script(agent, script)
        return redirect("/bootstrap", code=302)

    if "package" in request.args and "resource" in request.args:
        package = request.args["package"]
        resource = request.args["resource"]
        Bootstrap.bootstrap_resource(agent, package, resource)
        return redirect("/bootstrap", code=302)

    resources = Bootstrap.list_resources("backend.resources") + Bootstrap.list_resources("backend.resources.experiments")
    resources = map(lambda r: {"resource": r, "loaded": r[0] + "." + r[1] in Bootstrap.loaded}, resources)

    return render_template("bootstrap.html", resources=resources)


if __name__ == '__main__':
    host = "127.0.0.1"
    port = 5002

    import sys

    for arg in sys.argv:
        if '=' in arg:
            k = arg.split("=")[0]
            v = arg.split("=")[1]

            if k == "host":
                host = v
            if k == "port":
                port = int(v)

    app.run(host=host, port=port, debug=False)


'''
IIDEA How To Run:

1) From LEAIServices/composite:
docker-compose -f static-knowledge.yml -f ontosem-analyzer.yml up

2) Run service.py

'''
