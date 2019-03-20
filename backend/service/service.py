import json
import traceback
from flask import Flask, redirect, request, abort, render_template, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from pkgutil import get_data

from backend.agent import Agent
# from backend.models.bootstrap import Bootstrap
# from backend.contexts.LCTContext import LCTContext
# from backend.models.grammar import Grammar
# from backend.models.graph import Frame, Identifier
# from backend.models.ontology import Ontology
from backend.models.xmr import XMR
from backend.service.AgentAdvanceThread import AgentAdvanceThread
from backend.service.IIDEAConverter import IIDEAConverter
from backend.utils.OntologyLoader import OntologyServiceLoader
from backend.utils.YaleUtils import format_learned_event_yale, input_to_tmrs, lookup_by_visual_id
from ontograph import graph as g
from ontograph.Frame import Frame
from ontograph.Space import Space


app = Flask(__name__, template_folder="../../frontend/templates/")
CORS(app)
socketio = SocketIO(app)

agent = Agent()
agent.logger().enable()
OntologyServiceLoader().load()
thread = None


def build_payload():
    return {
        "time": agent.IDEA.time(),
        "stage": agent.IDEA.stage(),
        "inputs": IIDEAConverter.inputs(agent),
        "agenda": IIDEAConverter.agenda(agent),
        "effectors": IIDEAConverter.effectors(agent),
        "triggers": IIDEAConverter.triggers(agent),
        "logs": IIDEAConverter.logs(agent),
        "decisions": IIDEAConverter.decisions(agent),
        "running": not thread.stopped() and thread.is_alive(),
        "io": IIDEAConverter.io(agent)
    }


def graph_to_json(space: Space):
    frames = []

    for frame in space:

        t = frame.__class__.__name__
        if frame.space() == g.ontology():
            t = "OntologyFrame"
        if frame.space() is not None and frame.space().name.startswith("TMR#"):
            t = "TMRFrame"

        converted = {
            "type": t,
            "graph": space.name if frame.space() is None else frame.space().name,
            "name": frame.id,
            "relations": [],
            "attributes": []
        }

        for slot in frame:
            for filler in slot:
                if isinstance(filler, Frame):
                    converted["relations"].append({
                        "graph": space.name if filler.space() is None else filler.space().name,
                        "slot": slot.property,
                        "value": filler.id
                    })
                else:
                    value = filler
                    if isinstance(value, type):
                        value = value.__module__ + '.' + value.__name__
                    elif isinstance(value, int):
                        value = value
                    else:
                        value = str(value)

                    converted["attributes"].append({
                        "slot": slot.property,
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
  return send_from_directory("../../frontend/assets/", filename)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory("../../frontend/assets/", "favicon.ico", mimetype='image/vnd.microsoft.icon')


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", network=agent._storage.keys())


@app.route("/grammar", methods=["GET"])
def grammar():
    return render_template("grammar.html")


@app.route("/reset", methods=["DELETE"])
def reset():
    g.reset()

    global agent
    agent = Agent()

    return "OK"


@app.route("/network", methods=["GET"])
def network():
    return json.dumps(list(map(lambda s: s.name, g)))


@app.route("/view", methods=["POST"])
def view():
    data = request.data.decode("utf-8")
    return graph_to_json(g.ontolang().run(data))
    # from backend.models.view import View
    # data = request.data.decode("utf-8")
    # q_processor = g.ontolang().parse(data)[0]
    # view = View(agent, q_processor.start, query=q_processor.query)
    # view_graph = view.view()
    # return graph_to_json(view_graph)


@app.route("/graph", methods=["GET"])
def graph():
    if "id" not in request.args:
        abort(400)

    id = request.args["id"]

    return graph_to_json(Space(id))


@app.route("/iidea/start", methods=["GET"])
def start():
    global thread

    if thread.is_alive():
        abort(400)

    thread = AgentAdvanceThread(host, port)
    thread.start()

    return "OK"


@app.route("/iidea/stop", methods=["GET"])
def stop():
    thread.stop()

    return "OK"


@app.route("/iidea", methods=["GET"])
def iidea():
    payload = build_payload()
    return render_template("iidea.html", time=payload["time"], stage=payload["stage"], inputs=payload["inputs"], agenda=payload["agenda"], payload=json.dumps(payload))


@app.route("/iidea/data", methods=["GET"])
def iidea_data():
    return json.dumps(build_payload())


@app.route("/iidea/advance", methods=["GET"])
def iidea_advance():
    agent.iidea()

    payload = build_payload()

    socketio.emit("iidea updated", payload)

    return json.dumps(payload)


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

    source = lookup_by_visual_id(agent, data["source"])
    agent._input(input=tmr, source=source, type=data["type"])

    return json.dumps(build_payload())


@app.route("/iidea/observe", methods=["POST"])
def iidea_observe():
    if not request.get_json():
        abort(400)

    data = request.get_json()

    observations = json.loads(get_data("tests.resources", "DemoJan2019_Observations_VMR.json").decode('ascii'))
    observation = observations[data["observation"]]
    agent._input(observation, type=XMR.Type.VISUAL.name)

    return json.dumps(build_payload())


@app.route("/iidea/callback", methods=["POST"])
def iidea_callback():
    if not request.get_json():
        abort(400)

    data = request.get_json()

    callback = data["callback-id"]
    agent.callback(callback)

    return json.dumps(build_payload())


@app.route("/yale/bootstrap", methods=["POST"])
def yale_bootstrap():
    if not request.get_json():
        abort(400)

    data = request.get_json()

    from backend.utils import YaleUtils

    YaleUtils.bootstrap(data, agent.environment)

    return "OK"


@app.route("/yale/visual-input", methods=["POST"])
def yale_visual_input():
    if not request.get_json():
        abort(400)

    data = request.get_json()

    from backend.utils import YaleUtils

    data = YaleUtils.visual_input(data, agent.environment)

    agent._input(data, type="VISUAL")

    return "OK"


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


@app.route("/components/graph", methods=["GET"])
def components_graph():
    if "namespace" not in request.args:
        abort(400)

    include_sources = True
    if "include_sources" in request.args:
        include_sources = request.args["include_sources"].lower() == "true"

    graph = request.args["namespace"]
    graph = graph_to_json(agent[graph])
    return render_template("graph.html", gj=json.loads(graph), include_sources=include_sources)


@app.route("/io", methods=["GET"])
def io():
    return render_template("io.html", ioj=json.dumps(IIDEAConverter.io(agent)))


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

    resources = Bootstrap.list_resources("backend.resources") + Bootstrap.list_resources("backend.resources.experiments") + Bootstrap.list_resources("backend.resources.example")
    resources = map(lambda r: {"resource": r, "loaded": r[0] + "." + r[1] in Bootstrap.loaded}, resources)

    return render_template("bootstrap.html", resources=resources)


if __name__ == '__main__':
    host = "127.0.0.1"
    port = 5002

    thread = AgentAdvanceThread(host, port)

    import sys

    for arg in sys.argv:
        if '=' in arg:
            k = arg.split("=")[0]
            v = arg.split("=")[1]

            if k == "host":
                host = v
            if k == "port":
                port = int(v)

    socketio.run(app, host=host, port=port, debug=False)


'''
IIDEA How To Run:

1) From LEAIServices/composite:
docker-compose -f static-knowledge.yml -f ontosem-analyzer.yml up

2) Run service.py

'''
