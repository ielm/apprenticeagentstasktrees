import json
import traceback
from flask import Flask, request, abort, send_from_directory
from flask_cors import CORS

from backend.models.instructions import Instructions
from backend.ontology import Ontology
from backend.taskmodel import TaskModel
from backend.utils.YaleUtils import format_treenode_yale, input_to_tmrs
from backend.treenode import TreeNode

app = Flask(__name__)
CORS(app)

Ontology.init_default()
tm = TaskModel()
ont = Ontology.ontology


@app.errorhandler(Exception)
def server_error(error):
  tb_str = traceback.format_exc()
  app.logger.debug(tb_str)
  return tb_str, 500, { "Access-Control-Allow-Origin": "*"}


@app.route('/alpha/', methods=['GET'])
def serveindex():
  return servefile("index.html")


@app.route('/alpha/<path:filename>', methods=['GET'])
def servefile(filename):
  return send_from_directory("../frontend", filename)


@app.route('/alpha/maketree', methods=['POST'])
def start():
  if not request.json:
    abort(400)

  from backend.ontology import Ontology
  Ontology.init_from_ontology(ont)

  instructions = Instructions(request.json)
  model = tm.learn(instructions)

  return json.dumps(format_treenode_yale(model))


@app.route('/alpha/gettree', methods=['GET'])
def get_tree():
  format = "pretty"
  if "format" in request.args:
    format = request.args["format"]

  if format == "pretty":
    return str(tm.root)
  elif format == "json":
    return json.dumps(format_treenode_yale(tm.root), indent=4)

  return str(tm.root)


@app.route('/alpha/reset', methods=['DELETE'])
def reset_tree():
  global tm
  TreeNode.id = 0
  tm = TaskModel()
  return "Ok"


@app.route('/learn', methods=['POST'])
def learn():
  if not request.get_json():
    abort(400)

  from backend.ontology import Ontology
  Ontology.init_from_ontology(ont)

  data = request.get_json()
  tmrs = input_to_tmrs(data)

  instructions = Instructions(tmrs)
  model = tm.learn(instructions)

  return json.dumps(format_treenode_yale(model), indent=4)


@app.route("/query", methods=["POST"])
def query():
  if not request.get_json():
    abort(400)

  from backend.ontology import Ontology
  Ontology.init_from_ontology(ont)

  data = request.get_json()
  tmrs = input_to_tmrs(data)

  if len(tmrs) != 1:
    abort(400)

  from backend.models.tmr import TMR
  tmr = TMR(tmrs[0])
  model = tm.query(tmr)

  return json.dumps(format_treenode_yale(model), indent=4)

  
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
