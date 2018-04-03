import traceback
from flask import Flask, request, abort, send_from_directory
from flask_cors import CORS

from instructions import Instructions
from mini_ontology import init_from_file
from taskmodel import TaskModel

app = Flask(__name__)
CORS(app)

init_from_file("resources/ontology_May_2017.p")
tm = TaskModel()


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

  instructions = Instructions(request.json)
  model = tm.learn(instructions)
  return str(model)


@app.route('/alpha/gettree', methods=['GET'])
def get_tree():
  return str(tm.root)


@app.route('/alpha/reset', methods=['DELETE'])
def reset_tree():
  global tm
  tm = TaskModel()
  return "Ok"

  
if __name__ == '__main__':
  app.run(host="0.0.0.0", debug=True, port=5000)
