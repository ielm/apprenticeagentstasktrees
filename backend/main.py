import json
import traceback
from flask import Flask, request, abort, send_from_directory
from flask_cors import CORS

from instructions import Instructions
from mini_ontology import Ontology
from taskmodel import TaskModel
from utils.YaleUtils import format_treenode_yale, input_to_tmrs

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

  from backend.mini_ontology import Ontology
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
    return json.dumps(format_treenode_yale(tm.root))

  return str(tm.root)


@app.route('/alpha/reset', methods=['DELETE'])
def reset_tree():
  global tm
  tm = TaskModel()
  return "Ok"


@app.route('/learn', methods=['POST'])
def learn():
  if not request.json:
    abort(400)

  from backend.mini_ontology import Ontology
  Ontology.init_from_ontology(ont)

  data = request.json
  tmrs = input_to_tmrs(data)

  instructions = Instructions(tmrs)
  model = tm.learn(instructions)
  print(model)

  return json.dumps(format_treenode_yale(model))


  
if __name__ == '__main__':
  app.run(host="0.0.0.0", debug=True, port=5002)
