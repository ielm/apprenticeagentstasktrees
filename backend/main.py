import traceback
import json
from flask import Flask, request, abort, send_from_directory
from flask_cors import CORS, cross_origin

import maketree

app = Flask(__name__)
CORS(app)

@app.errorhandler(Exception)
def server_error(error):
  tb_str = traceback.format_exc()
  app.logger.debug(tb_str)
  return tb_str, 500, { "Access-Control-Allow-Origin": "*"}

@app.route('/alpha/maketree', methods=['GET'])
@app.route('/', methods=['GET'])
def serveindex():
  return servefile("index.html")

@app.route('/alpha/maketree/<path:filename>', methods=['GET'])
def servefile(filename):
  return send_from_directory("../frontend", filename)

@app.route('/alpha/maketree', methods=['POST'])
def start():
  if not request.json:
    abort(400)
  steps = []
  new_tree = maketree.construct_tree(request.json, steps)
  return json.dumps(steps)

current_tree = None

@app.route('/alpha/mergetree', methods=['POST'])
def start_with_merging():
  if not request.json:
    abort(400)
  steps = []
  new_tree = maketree.construct_tree(request.json, steps)
  global current_tree
  if current_tree is None:
    current_tree = new_tree
  else:
    maketree.settle_disputes(new_tree, current_tree)
    maketree.settle_disputes(current_tree, new_tree)
    maketree.find_parallels(new_tree, current_tree)
    maketree.find_parallels(current_tree, new_tree)
    #if stuff gets weird enough, might have to disambiguate the two of them back and forth for a while
    mergetree.merge_tree(current_tree, new_tree)
  list = []
  maketree.tree_to_json_format(current_tree, list)
  #return json.dumps(list)
  return json.dumps([{"input":"(input not shown)", "tree": list}])

@app.route('/alpha/mergetree', methods=['DELETE'])
def clear_merged_tree():
  global current_tree
  current_tree = None
  return json.dumps({"result":True})
  
if __name__ == '__main__':
  app.run(host="0.0.0.0", debug=True, port=5000)
