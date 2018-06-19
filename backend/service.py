import json
import traceback
from flask import Flask, request, abort
from flask_cors import CORS


from backend.agent import Agent
from backend.contexts.LCTContext import LCTContext
from backend.models.graph import Network
from backend.models.ontology import Ontology
from backend.utils.YaleUtils import format_learned_event_yale, input_to_tmrs

app = Flask(__name__)
CORS(app)


n = Network()
ontology = n.register(Ontology.init_default())
agent = Agent(n, ontology)


@app.errorhandler(Exception)
def server_error(error):
    tb_str = traceback.format_exc()
    app.logger.debug(tb_str)
    return tb_str, 500, {"Access-Control-Allow-Origin": "*"}


@app.route("/reset", methods=["DELETE"])
def reset():
    global n
    global ontology
    global agent

    n = Network()
    ontology = n.register(Ontology.init_default())
    agent = Agent(n, ontology)

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
        learning = list(map(lambda instance: instance.name(), agent.wo_memory.search(context={LCTContext.LEARNING: True})))
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
