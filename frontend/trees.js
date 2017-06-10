/**
 * Construct a new TreeNode object.
 *
 * Parameters:
 *  name (string): the name of this node.
 *  renderId (int): the unique id of this instance of this node, used to
 *      identify it during rendering.
 *  nodeId (int): the unique id of this node shared by all identical instances
 *      of it. There may be more than one instance of a node if more than one
 *      node claims it as a child.
 *  children (array[TreeNode]): the children of this node. If empty, null, or
 *      undefined, this node is treated as a leaf node.
 *  childMatrix (array[array[int]]): an adjacency matrix representing the
 *      relative order of this node's children in the task hierarchy. This
 *      should be a square matrix of dimensions equal to the number of children.
 *      The rows and columns correspond to the children in the same relative
 *      order as in the children array. A value of -1 indicates that child
 *      <row> appears before child <col>, 1 indicates that child <row> appears
 *      after child <col>, and 0 indicates that these children are parallel to
 *      each other (i.e. can switch relative places). It is not a requirement,
 *      but canonically the diagonal of the matrix should consist only of
 *      zeroes.
 *  parent (TreeNode): the parent of this node. If null or undefined, this node
 *      is treated as a root node.
 *  propertiesObj (object, optional): an arbitrary object that will be assigned`
 *      to this node's properties field.
 *  options (Object, optional): an object with key-value pairs specifying
 *      further options for this TreeNode:
 *        questioned: (boolean) -- Set to true if this node might possibly be
 *            the child of more than one parent node. Defaults to false.
 * 
 * TreeNode instance members:
 *  treeNode.name (string): the name of this node.
 *  treeNode.renderId (int): the unique id of this instance of this TreeNode
 *  treeNode.nodeId (int): the unique id shared by all instances of this TreeNode
 *  treeNode.children (array[TreeNode]): the children of this node. If
 *      empty, null, or undefined, this node is a leaf node.
 *  treeNode.childMatrix (array[array[int]]): the child matrix of this
 *      node, as defined above.
 *  treeNode.parent (TreeNode): the parent of this node. If null or undefined,
 *      this node is a root node.
 *  treeNode.properties (Object): an arbitrary object with additional properties
 *      for this node.
 * */
function TreeNode(name, renderId, nodeId, children, childMatrix, parent, propertiesObj, options) {
  this.name = name;
  this.renderId = renderId;
  this.nodeId = nodeId;
  this.children = children;
  this.childMatrix = childMatrix;
  this.parent = parent;
  this.properties = {};

  if (options && "questioned" in options && typeof options.questioned === "boolean")
    this.questioned = options.questioned;
  else
    this.questioned = false;

  this.type = (!this.childMatrix || this.childMatrix.length === 0) ?
    "leaf" : "sequential";

  outerloop:
  for (var row in this.childMatrix) {
    for (var col in this.childMatrix) {
      if (row === col) continue;
      if (this.childMatrix[row][col] === 0) {
        this.type = "parallel";
        break outerloop;
      }
    }
  }

  if (propertiesObj) {
    Object.assign(this.properties, propertiesObj);
  }
}
TreeNode.prototype = {};

/**
 * Construct a new Forest object. Forests are containers for multiple disjoint
 * trees consisting of TreeNodes.
 *
 * Parameters:
 *  trees (TreeNode or array[TreeNode], optional): zero or more TreeNodes, each
 *      of which represents the root of one tree in this Forest. Each of these
 *      TreeNodes must have a null or undefined parent.
 *
 * Throws TypeError if any node in any tree is not an instance of TreeNode.
 * Throws TypeError if any of the passed roots have a parent.
 * Throws Error if any two nodes in any tree passed to the Forest have the same
 *    id property.
 *
 * Forest instance members:
 *  forest.trees (array[TreeNodes]): array of the roots of the trees contained
 *      in this Forest.
 *  forest.nodes (object): an object used as a map from node id's to references
 *      to the nodes themselves. Forest.nodes[TreeNode.renderId] will return a
 *      reference to the TreeNode if it exists in any tree in this Forest, or
 *      undefined if it does not.
 *
 * It is not recommended to directly assign to these members. Instead, use the
 * methods defined below.
 * */
function Forest(trees) {
  if (trees === undefined) {
    this.trees = [];
  }
  else if (! trees instanceof Array) {
    this.trees = [ trees ];
  }
  else {
    this.trees = trees;
  }

  this.nodes = {};

  this.trees.forEach(function(t) {
    if (t.parent !== null && t.parent !== undefined)
      throw new TypeError("Root node " + t.name + ", id " + t.renderId + ", has a parent");

    (function addIds(n) {
      if (!n instanceof TreeNode)
        throw new TypeError("Found an invalid TreeNode object");
      if (this.nodes[n.renderId] !== undefined)
        throw new Error("Nodes \"" + n.name + "\"." + n.renderId + " and \""
          + this.nodes[n.renderId].name + "\"." + this.nodes[n.renderId].renderId + " share IDs");

      this.nodes[n.renderId] = n;
      n.children.forEach(addIds, this);
    }).call(this, t);
  }, this);
}
Forest.prototype = {
  /**
   * Add a non-root TreeNode to the Forest as a child of the given parent node.
   *
   * Parameters:
   *  node (TreeNode): the node to add to the tree. This node should have an ID
   *      that is unique among it and the other nodes in this Forest. The
   *      parent field of the node will be modified as necessary to match the
   *      parent indicated in the parameters to this method.
   *  parent (int or TreeNode): the parent node of the added node. If this
   *      parameter is an int, it must be the render ID of a node in this Forest. If
   *      it is a TreeNode, it must have a name and render ID that match a TreeNode in
   *      this Forest.
   *  index (int, optional): the desired index of the added node in the
   *      parent's children array. This must be in the range 0 to
   *      parent.children.length, inclusive. Any children after this index are
   *      shifted. If this parameter is omitted, the new node is appended to
   *      the end of the parent's children array.
   *
   * Throws TypeError if node is not an instance of TreeNode
   * Throws Error if a TreeNode with the same id as node already exists in this
   *    Forest.
   * Throws TypeError if the parent is neither an integer nor a TreeNode.
   * Throws Error if the parent is invalid. The parent is invalid if 1. the
   *    specified render ID does not exist in this Forest, or 2. if the specified
   *    TreeNode has render id and name properties that do not match any TreeNode in
   *    this Forest.
   * Throws TypeError if index is not an integer.
   * Throws Error if index is invalid. The index is invalid if 1. it is not an
   *    integer, or 2. it is outside the bounds of the parent's children array.
   * */
  addNode: function(node, parent, index) {
    if (! node instanceof TreeNode)
      throw new TypeError("node is not a valid TreeNode object");

    if (typeof(parent) === "number" && Number.isInteger(parent)) {
      var par = this.nodes[parent];
      if (par === undefined)
        throw new Error("Invalid parent ID for this Forest");
    }
    else if (parent instanceof TreeNode) {
      var par = this.nodes[parent.renderId];
      if (par === undefined || par.name !== parent.name)
        throw new Error("Provided parent does not match any in this Forest");
    }
    else {
      throw new TypeError("Expected int or TreeNode for parent");
    }

    if (index === undefined) index = par.children.length;
    if (typeof(index) !== "number" || !Number.isInteger(index))
      throw new TypeError("Expected integer for index");
    if (!Number.isInteger(index) || index < 0 || index > par.children.length)
      throw new Error("index out of bounds of parent's children array.");

    par.children.splice(index, 0, node);
    this.nodes[node.renderId] = node;
  }
};

/**
 * Construct a new TreeSeq object. TreeSeqs represent a sequence of stages in
 * the growth of a tree or forest.
 *
 * Parameters:
 *  stages (array[Forest], optional): if provided, the stages of this TreeSeq
 *      are initialized to the stages array. Otherwise, the TreeSeq's stages
 *      are initialized to an empty array.
 *
 * Throws TypeError if stages is defined but not an array.
 * Throws TypeError if any element of stages is not an instance of Forest.
 *
 * TreeSeq instance members:
 *  treeSeq.stages (array[Forest]): the array of stages in this TreeSeq.
 *
 * (Note: this could just as easily be a simple array rather than a class, but
 * I kinda anticipate having to add more information to these objects, so I
 * went ahead and made it a class.)
 * */
function TreeSeq(stages) {
  if (stages === undefined) this.stages = [];
  else if (! stages instanceof Array)
    throw new TypeError("Expected array for stages, got " + typeof(stages));
  else this.stages = stages;

  this.stages.forEach(function(t) {
    if (!t instanceof Forest)
      throw new TypeError("Expected Forest elements in stages");
  });
}
TreeSeq.prototype = {};

/**
 * Create a TreeSeq from the passed data.
 *
 * Parameters:
 *  data (object): an object parsed from an input JSON file. The format of the
 *      file is described elsewhere.
 *
 * Returns a TreeSeq generated from the data object. The first Forest in the
 * sequence will be empty, followed by Forests based on the input data.
 *
 * The input data is modified by this function. Specifically, the properties
 * 'id', 'name', 'children', and 'childMatrix' are removed from the input data
 * for each node.
 * */
function treeSeqFromData(data) {
  var seqData = {};
  var forests = [];
  var nextId = 0;
  
  data.forEach(function(stage) {

    // get new children for each node in the input
    stage.tree.forEach(function(inputNode) {
      var nodeId = inputNode.id;
      if (!seqData[nodeId]) seqData[nodeId] = {
        name: "",
        children: [],
        parents: [],
        childMatrix: [],
        properties: {},
        instances: []
      };
      if (inputNode.name !== undefined)
        seqData[nodeId].name = inputNode.name;

      if (inputNode.children !== undefined)
        seqData[nodeId].children = inputNode.children;

      if (inputNode.childMatrix !== undefined) {
        seqData[nodeId].childMatrix = inputNode.childMatrix;
      }

      // get any other properties of the node from the input
      delete inputNode.id;
      if (inputNode.name !== undefined) delete inputNode.name;
      if (inputNode.children !== undefined) delete inputNode.children;
      if (inputNode.childMatrix !== undefined) delete inputNode.childMatrix;
      Object.assign(seqData[nodeId].properties, inputNode);
    });

    // calculate new parents
    for (var nodeId in seqData) {
      seqData[nodeId].children.forEach(function(childId) {
        if (!seqData[childId].newParents) seqData[childId].newParents = [];
        seqData[childId].newParents.push(nodeId);
      });
    }

    // identify roots and construct trees for each one that we find
    var roots = [];
    var rootsInfo = [];
    for (var nodeId in seqData) {
      if (!seqData[nodeId].newParents) seqData[nodeId].newParents = [];
      if (seqData[nodeId].newParents.length === 0) {
        seqData[nodeId].newInstances = [
          new TreeNode(seqData[nodeId].name, 0, nodeId, [],
            seqData[nodeId].childMatrix, null, seqData[nodeId].properties)
        ];

        function constructTree(root, nodeId) {
          var rootInfo = seqData[nodeId];

          // update children's newInstances and recurse down the tree
          rootInfo.children.forEach(function(childId) {
            /*
            var treeNodeOptions = {};
            if (seqData[childId].newParents.length > 1)
              treeNodeOptions.questioned = true;
              */

            root.children.push(new TreeNode(
              seqData[childId].name, 0, childId, [], seqData[childId].childMatrix,
              root, seqData[childId].properties)
            );

            if (!seqData[childId].newInstances) seqData[childId].newInstances = [];
            seqData[childId].newInstances.push(root.children.back);
            constructTree(root.children.back, childId);
          });
        }

        constructTree(seqData[nodeId].newInstances[0], nodeId);
        roots.push(seqData[nodeId].newInstances[0]);
        rootsInfo.push(seqData[nodeId]);
      }
    }

    function assignRenderIds(node) {
      var nodeInfo = seqData[node.nodeId];
      var oldInst = nodeInfo.instances.find(function(old) {
        return old.parent && node.parent && old.parent.renderId === node.parent.renderId;
      });

      if (!oldInst) {
        oldInst = nodeInfo.instances.find(function(old) {
          return old.parent === null || old.parent === undefined;
        });
        
        if (!oldInst) {
          oldInst = nodeInfo.instances.find(function(old) {
            return !nodeInfo.newParents.find(function(parId) { old.parent.renderId === parId; });
          });
        }
      }

      if (oldInst) {
        node.renderId = oldInst.renderId;
        var index = nodeInfo.instances.findIndex(function(n) { return n.renderId === oldInst.renderId; });
        nodeInfo.instances.splice(index, 1);
      }
      else node.renderId = nextId++;

      if (nodeInfo.newInstances.length > 1)
        node.questioned = true;

      node.children.forEach(assignRenderIds);
    }
    roots.forEach(assignRenderIds);

    forests.push(new Forest(roots));

    // clean up newParents and newInstances
    for (var node in seqData) {
      seqData[node].parents = seqData[node].newParents;
      seqData[node].instances = seqData[node].newInstances;
      delete seqData[node].newParents;
      delete seqData[node].newInstances;
    }
  });

  forests.unshift(new Forest());
  return new TreeSeq(forests);
}
