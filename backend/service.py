import json
import traceback
from flask import Flask, request, abort, render_template, send_from_directory
from flask_cors import CORS


from backend.agent import Agent
from backend.contexts.LCTContext import LCTContext
from backend.models.grammar import Grammar
from backend.models.graph import Frame, Identifier, Network
from backend.models.ontology import Ontology
from backend.utils.YaleUtils import format_learned_event_yale, input_to_tmrs

app = Flask(__name__, template_folder="../frontend/templates/")
CORS(app)


n = Network()
ontology = n.register(Ontology.init_default())
agent = Agent(n, ontology)


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
                    converted["attributes"].append({
                        "slot": s,
                        "value": filler._value.value
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
    return render_template("index.html", network=n._storage.keys())


@app.route("/grammar", methods=["GET"])
def grammar():
    return render_template("grammar.html")


@app.route("/reset", methods=["DELETE"])
def reset():
    global n
    global ontology
    global agent

    n = Network()
    ontology = n.register(Ontology.init_default())
    agent = Agent(n, ontology)

    return "OK"


@app.route("/network", methods=["GET"])
def network():
    return json.dumps(list(n._storage.keys()))


@app.route("/view", methods=["POST"])
def view():
    data = request.data.decode("utf-8")
    view = Grammar.parse(n, data)
    view_graph = view.view()
    return graph_to_json(view_graph)


@app.route("/graph", methods=["GET"])
def graph():
    if "id" not in request.args:
        abort(400)

    id = request.args["id"]

    return graph_to_json(n[id])


@app.route("/input", methods=["POST"])
def input():
    if not request.get_json():
        abort(400)

    data = request.get_json()
    tmrs = input_to_tmrs(data)

    for tmr in tmrs:
        agent.input(tmr)

    if isinstance(agent.context, LCTContext):
        learning = list(map(lambda instance: instance.name(), agent.wo_memory.search(Frame.q(agent.network).f(LCTContext.LEARNING, True))))
        return json.dumps({
            LCTContext.LEARNING: learning
        })

    return "OK"


@app.route("/htn", methods=["GET"])
def htn():
    if "instance" not in request.args:
        abort(400)

    instance = request.args["instance"]
    instance = agent.wo_memory[instance]

    return json.dumps(format_learned_event_yale(instance, ontology), indent=4)


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
