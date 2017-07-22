/**
 * Construct a new TreeNode object.
 *
 *  TreeNode([options])
 *     options (object, optional): The options parameter, if provided, specifies
 *         additional parameters for the created TreeNode. Possible options are:
 *           name (string): The name of the new TreeNode. Defaults to the empty string.
 *           nodeId (int): The node ID of this TreeNode. Defaults to 0.
 *           renderId (int): The render ID of this TreeNode. Defaults to 0.
 *           parent (TreeNode): The parent of this TreeNode. Defaults to null.
 *           children (array[TreeNode]): The children of this TreeNode. Defaults to
 *               an empty array.
 *           properties (object): Other arbitrary properties for this TreeNode.
 *               Defaults to an object with no own properties.
 *
 *         If the options argument is omitted, the TreeNode's properties all
 *         assume their default values.
 * 
 * TreeNode public methods (described along with their implementations below):
 *    name()        renderId()
 *    nodeId()      parent()
 *    children()    child()
 *    numChildren() appendChild()
 *    insertChild() forEachChild()
 *    properties()
 *
 * TreeNode static methods (described along with their implementations below):
 *    TreeNode.copy()
 *
 * TreeNode instance properties (should be regarded as private):
 *  name_ (string): The name of this TreeNode.
 *  renderId_ (int): The render ID of this TreeNode.
 *  nodeId_ (int): The node ID of this TreeNode.
 *  parent_ (TreeNode): The parent of this TreeNode.
 *  children_ (array[TreeNode]): The children of this TreeNode.
 *  properties_ (object): Other arbitrary properties for this TreeNode.
 * */
function TreeNode(options) {
  this.name_ = "";
  this.renderId_ = 0;
  this.nodeId_ = 0;
  this.parent_ = null;
  this.children_ = [];
  this.properties_ = {};

  if (options) {
    for (prop in options) {
      if (prop === "name")
        this.name_ = options[prop];
      else if (prop === "renderId")
        this.renderId_ = options[prop];
      else if (prop === "nodeId")
        this.nodeId_ = options[prop];
      else if (prop === "parent")
        this.parent_ = options[prop];
      else if (prop === "children")
        this.children_ = options[prop];
      else if (prop === "properties")
        this.properties_ = options[prop];
    }
  }
}

TreeNode.prototype = new TreeNode();
Object.assign(TreeNode.prototype, {

  /**
   * Set or retrieve the name of this TreeNode.
   *
   *  name(newName)
   *      newName (string): The new name for this TreeNode.
   *
   *    Returns this TreeNode.
   *
   *  name()
   *    Returns the name of this TreeNode.
   * */
  name: function name(newName) {
    if (typeof newName === "string") {
      this.name_ = newName;
      return this;
    }
    else return this.name_;
  },

  /**
   * Set or retrieve the render ID of this TreeNode.
   *
   *  renderId(id)
   *      id (int): The new render ID for this TreeNode.
   *
   *    Returns this TreeNode.
   *
   *  renderId()
   *    Returns the render ID of this TreeNode.
   * */
  renderId: function renderId(id) {
    if (typeof id === "number") {
      this.renderId_ = id;
      return this;
    }
    else return this.renderId_;
  },

  /**
   * Set or retrieve the node ID of this TreeNode.
   *
   *  nodeId(id)
   *      id (int): The new node ID for this TreeNode.
   *
   *    Returns this TreeNode.
   *
   *  nodeId()
   *    Returns the node ID of this TreeNode.
   * */
  nodeId: function nodeId(id) {
    if (typeof id === "number") {
      this.nodeId_ = id;
      return this;
    }
    else return this.nodeId_;
  },

  /**
   * Set or retrieve the parent of this TreeNode.
   *
   *  parent(newParent)
   *      newParent (TreeNode): The new parent for this TreeNode.
   *
   *    Returns this TreeNode.
   *
   *  parent()
   *    Returns the parent of this TreeNode.
   * */
  parent: function parent(newParent) {
    if (newParent instanceof TreeNode) {
      this.parent_ = newParent;
      return this;
    }

    else return this.parent_;
  },

  /**
   * Set or retrieve the children array of this TreeNode.
   *
   *  children(newChildren)
   *      newChildren (array[TreeNode]): The new array of children for this
   *          TreeNode.
   *
   *    Returns this TreeNode.
   *  
   *  children()
   *    Returns a shallow copy of this TreeNode's children array.
   * */
  children: function children(newChildren) {
    if (newChildren instanceof Array) {
      this.children_ = newChildren;
      return this;
    }
    else return Array.from(this.children_);
  },

  /**
   * Set or retrieve a specific child of this TreeNode.
   *
   *  child(index, newChild)
   *      index (int): The index of the child to replace or set.
   *      newChild (TreeNode): The new child to place in this TreeNode's
   *          children array.
   *
   *    Returns this TreeNode.
   *
   *  child(index)
   *      index (int): The index of the child to retrieve.
   *
   *    Returns the TreeNode at the given index in this TreeNode's children array.
   * */
  child: function child(index, newChild) {
    if (newChild instanceof TreeNode) {
      this.children_[index] = newChild;
      return this;
    }
    else return this.children_[index];
  },

  /**
   *  numChildren()
   *    Returns the length of this TreeNode's children array.
   *
   *    Equivalent to node.children().length, but does not copy the
   *    array.
   * */
  numChildren: function numChildren() {
    return this.children_.length;
  },

  /**
   * Append a TreeNode to the back of this TreeNode's children array.
   *
   *  appendChild(child)
   *      child (TreeNode): The child to append.
   *
   *    Returns this TreeNode.
   * */
  appendChild: function appendChild(child) {
    this.children_.push(child);
    return this;
  },

  /**
   * Insert a TreeNode into this TreeNode's children array at a specific index.
   *
   *  insertChild(beforeIndex, child)
   *      beforeIndex (int): The index in the children array before which to
   *          insert the child.
   *      child (TreeNode): The child to be inserted.
   *    
   *    Returns this TreeNode.
   * */
  insertChild: function insertChild(beforeIndex, child) {
    this.children_.splice(beforeIndex, 0, child);
    return this;
  },

  /**
   * Call a function for each child of this TreeNode.
   *
   *  forEachChild(callback [, thisContext])
   *      callback (function): The function to evaluate for each child. This
   *          function is passed the child object, the index of the child, and
   *          this TreeNode.
   *      thisContext (object, optional): If provided, the callback will be
   *          executed with thisContext, instead of the global object, as its
   *          this context.
   *
   *    Returns this TreeNode.
   * */
  forEachChild: function forEachChild(callback, thisContext) {
    var that = thisContext? thisContext : window;
    this.children_.forEach(function(child, i) {
      callback.call(that, child, i, this);
    }, this);
    return this;
  },

  /**
   * Retrieve a reference to this TreeNode's properties object.
   *
   *  properties()
   *    Adds an empty properties object to this TreeNode if it is undefined.
   *
   *    Returns a reference to this TreeNode's properties object.
   * */
  properties: function properties() {
    if (!this.properties_) this.properties_ = {};
    return this.properties_;
  }
});

/**
 * Create a copy of the tree rooted at the given TreeNode.
 *
 *  TreeNode.copy(inst)
 *      inst (TreeNode): The TreeNode to copy.
 *
 *    Returns the root TreeNode of a deep copy of the tree rooted at inst. The
 *      parent of the returned TreeNode will refer to the same instance as the
 *      given TreeNode's parent, if any (i.e. parent nodes are not copied). The
 *      properties objects of each TreeNode in the new tree are shallow copies
 *      of those of their corresponding nodes in the original tree.
 *    Throws TypeError if inst is not a TreeNode.
 * */
TreeNode.copy = function copy(inst) {
  if (!inst instanceof TreeNode)
    throw new TypeError("inst is not a TreeNode");
  
  var newNode = new TreeNode({
    name: inst.name_,
    nodeId: inst.nodeId_,
    renderId: inst.renderId_,
    parent: inst.parent_
  });
  Object.assign(newNode.properties_, inst.properties);

  inst.forEachChild(function(c, i) {
    newNode.appendChild(TreeNode.copy(c));
    newNode.child(i).parent(newNode);
  });

  return newNode;
};

/**
 * Construct a new Forest object. A Forest is a container for multiple disjoint
 * trees. The render IDs of all TreeNodes in all trees in each Forest must be
 * unique within that Forest.
 *
 *  Forest([trees])
 *      trees (array[TreeNode], optional): An array of TreeNodes, each of which
 *          is the root of a tree in this Forest. If omitted, the constructed
 *          Forest is initially empty.
 *
 * Forest public methods (described with their implementations below):
 *    insertTree()    appendTree()
 *    tree()          trees()
 *    numTrees()      forEachTree()
 *    node()
 *
 * Forest static methods (described with their implementations below):
 *    Forest.copy()
 *
 * Forest instance properties (should be regarded as private):
 *  trees_ (array[TreeNode]): The roots of all trees in this Forest.
 *  nodes_ (object): An object with properties mapping node render IDs to the
 *      corresponding TreeNode objects in this Forest.
 * */
function Forest(trees) {
  if (trees instanceof Array)
    this.trees(trees);

  else {
    this.trees_ = [];
    this.nodes_ = {};
  }
}

Forest.prototype = new Forest();
Object.assign(Forest.prototype, {

  /**
   * Insert a tree into this Forest at a specific index.
   *
   *  insertTree(beforeIndex, root)
   *      beforeIndex (int): The index in the trees array before which to
   *          insert the tree.
   *      root (TreeNode): The root of the tree to be inserted.
   *    
   *    Returns this Forest.
   *    Throws Error if the inserted tree contains a TreeNode with a render ID
   *        that is shared by a node already in this Forest.
   * */
  insertTree: function insertTree(beforeIndex, root) {
    this.trees_.splice(beforeIndex, 0, root);

    function addIds(root) {
      if (!root) return;
      if (this.nodes_[root.renderId()] !== undefined)
        throw new Error("Node with render ID " + root.renderId() +
          " already exists in this Forest");

      this.nodes_[root.renderId()] = root;
      root.forEachChild(addIds, this);
    }

    addIds.call(this, root);
  },

  /**
   * Append a tree to the end of this Forest's trees array.
   *
   *  appendTree(root)
   *      root (TreeNode): The root of the tree to be appended.
   *
   *    Returns this Forest.
   *    Throws Error if the appended tree contains a TreeNode with a render ID
   *        that is shared by a node already in this Forest.
   * */
  appendTree: function appendTree(root) {
    this.insertTree(this.trees_.length, root);
  },

  /**
   * Set or retrieve the root of a tree in this Forest with specified index.
   *
   *  tree(index)
   *      index (int): The index of the tree to retrieve.
   *
   *    Returns the TreeNode that is the root of the specified tree.
   *  
   *  tree(index, root)
   *      index (int): The index of the tree to set.
   *      root (TreeNode): The root of the tree being assigned.
   *
   *    Returns this Forest.
   *    Throws Error if the assigned tree contains a node with a render ID that
   *        is shared by a node already in this Forest (after removing the
   *        nodes of any tree the assigned tree may be replacing).
   * */
  tree: function tree(index, root) {
    if (root instanceof TreeNode) {
      function removeIds(root) {
        if (!root) return;
        delete this.nodes_[root.renderId()];
        root.forEachChild(removeIds, this);
      }
      removeIds.call(this, this.trees_[index]);

      this.trees_.splice(index, 1);
      this.insertTree(index, root);
    }

    else return this.trees_[index];
  },

  /**
   * Set or retrieve this Forest's array of trees.
   *
   *  trees(roots)
   *      roots (array[TreeNode]): The array of trees to assign to this Forest.
   *          Each element should be the root of its tree.
   *    
   *    Returns this Forest.
   *    Throws Error if any node in the given trees shares a render ID with any
   *        other node in the given trees.
   *
   *  trees()
   *    Returns a shallow copy of the this Forest's array of trees. Each element
   *        is the TreeNode that is the root of its tree.
   * */
  trees: function trees(roots) {
    if (roots instanceof Array) {
      this.nodes_ = {};
      this.trees_ = [];
      roots.forEach(this.appendTree, this);
    }
    else return Array.from(this.trees_);
  },

  /**
   *  numTrees()
   *    Returns the length of this Forest's trees array.
   *
   *    Equivalent to forest.trees().length, but does not copy the array.
   * */
  numTrees: function numTrees() {
    return this.trees_.length;
  },

  /**
   * Call a function for each tree in this TreeNode.
   *
   *  forEachTree(callback [, thisContext])
   *      callback (function): The function to evaluate for each tree. This
   *          function is passed the root TreeNode object, the index of the
   *          tree, and this Forest.
   *      thisContext (object, optional): If provided, the callback will be
   *          executed with thisContext, instead of the global object, as its
   *          this context.
   *
   *    Returns this Forest.
   * */
  forEachTree: function forEachTree(callback, thisContext) {
    var that = thisContext? thisContext : window;
    this.trees_.forEach(function(root, i) {
      callback.call(that, root, i, this);
    }, this);
    return this;
  },

  /**
   *  node(renderId)
   *      renderId (int): The render ID of the node to retrieve.
   *
   *    Returns the TreeNode with the given render ID if it exists in this
   *        Forest. Returns undefined otherwise.
   * */
  node: function node(renderId) {
    return this.nodes_[renderId];
  }
});

/**
 * Create a copy of the given Forest.
 *
 *  Forest.copy(inst)
 *      inst (Forest): The Forest to copy.
 *
 *    Returns a new Forest consisting of deep copies of each tree in the
 *      original Forest, as returned by TreeNode.copy.
 *    Throws TypeError if inst is not a Forest.
 * */
Forest.copy = function copy(inst) {
  if (!inst instanceof Forest)
    throw new TypeError("inst is not a Forest");

  var newForest = new Forest();
  inst.forEachTree(function(root) {
    newForest.appendTree(TreeNode.copy(root));
  });

  return newForest;
};

/**
 * Construct a new TreeSeq object. TreeSeqs represent a sequence of stages in
 * the growth of a tree or forest.
 *
 *  TreeSeq([forests])
 *      forests (array[Forest], optional): The initial array of Forests for this
 *          TreeSeq, each element of which represents a single stage. The
 *          TreeSeq will copy these Forests and modify the render IDs of nodes
 *          so as to reuse the render IDs of nodes with shared node IDs between
 *          stages, where appropriate. If this argument is omitted, the TreeSeq
 *          is initially empty.
 *
 * TreeSeq public methods (described along with their implementations below):
 *    appendForest()    forests()
 *    forest()          numForests()
 *    forEachForest()
 *
 * TreeSeq instance properties (should be regarded as private):
 *  forests_ (array[Forest]): The array of Forests in this TreeSeq.
 *  prevInfo_ (object): An object used internally to map node IDs to
 *      information about each node in the previously added Forest
 *  nextId_ (int): The next highest render ID that has not yet been assigned to
 *      a node in this TreeSeq.
 * */
function TreeSeq(forests) {
  if (forests instanceof Array)
    this.forests(forests);
  else this.forests([]);
}

TreeSeq.prototype = new TreeSeq();
Object.assign(TreeSeq.prototype, {

  /**
   * Append a copy of the given Forest to the back of this TreeSeq. The nodes
   * of the appended copy are modified so as to maintain consistency in render
   * IDs between nodes of matching node IDs between stages of the TreeSeq.
   *
   *  appendForest(forest)
   *      forest (Forest): The Forest to copy and append.
   *
   *    Returns this TreeSeq.
   * */
  appendForest: function appendForest(forest) {
    this.forests_.push(Forest.copy(forest));
    var curForest = this.forests_.back;
    var curInfo = {};

    for (let renderId in curForest.nodes_) {
      var n = curForest.node(renderId);
      if (!curInfo[n.nodeId()])
        curInfo[n.nodeId()] = { instances: [], parentNodeIds: [] };

      var curNodeInfo = curInfo[n.nodeId()];
      curNodeInfo.instances.push(n);
      if (n.parent() && !curNodeInfo.parentNodeIds.includes(n.parent().nodeId()))
        curNodeInfo.parentNodeIds.push(n.parent().nodeId());
    }

    function assignRenderIds(root) {
      var prevNodeInfo = this.prevInfo_[root.nodeId()];
      if (!prevNodeInfo) prevNodeInfo = { instances: [], parentNodeIds: [] };
      var curNodeInfo = curInfo[root.nodeId()];

      var oldInstances = prevNodeInfo.instances;

      var oldInst = oldInstances.find(function(old) {
        return old.parent() && root.parent()
          && old.parent().renderId() === root.parent().renderId();
      });

      if (!oldInst) {
        oldInst = oldInstances.find(function(old) {
          return old.parent() === null || old.parent() === undefined;
        });

        if (!oldInst) {
          oldInst = oldInstances.find(function(old) {
            return !curNodeInfo.parentNodeIds.find(function(parId) {
              return old.parent().nodeId() === parId;
            });
          });
        }
      }

      if (oldInst) {
        root.renderId(oldInst.renderId());
        var index = oldInstances.findIndex(function(n) {
          return n.renderId() === oldInst.renderId();
        });
        oldInstances.splice(index, 1);
      }
      else root.renderId(this.nextId_++);

      if (curNodeInfo.instances.length > 1)
        root.properties().questioned = true;

      root.forEachChild(assignRenderIds, this);
    }

    curForest.forEachTree(assignRenderIds, this);
    curForest.trees(curForest.trees());

    return this;
  },
  
  /**
   * Retrieve or set this TreeSeq's sequence of Forests.
   *
   *  forests(newForests)
   *      newForests (array[Forest]): The new sequence of Forests for this
   *          TreeSeq. As in the constructor, the TreeSeq will copy these
   *          Forests and modify nodes' render IDs so as to keep render IDs
   *          consistent between nodes in different stages with the same node
   *          IDs, where possible.
   *
   *    Returns this TreeSeq.
   *
   *  forests()
   *    Returns a shallow copy of this TreeSeq's sequence of Forests
   *        (array[Forest]).
   * */
  forests: function forests(newForests) {
    if (newForests instanceof Array) {
      this.forests_ = [];
      this.prevInfo_ = {};
      this.nextId_ = 0;
      newForests.forEach(function(f) {
        this.appendForest(f);
      }, this);
    }

    else return Array.from(this.forests_);
  },

  /**
   * Retrieve the Forest in this TreeSeq with the specified index.
   *
   *  forest(index)
   *      index (int): The index of the Forest to retrieve.
   *
   *    Returns the Forest at the specified index if it exists, or undefined
   *        otherwise.
   * */
  forest: function forest(index) {
    return this.forests_[index];
  },

  /**
   *  numForests()
   *    Returns the length of this TreeSeq's forests array.
   *
   *    Equivalent to treeSeq.forests().length, but avoids copying the array.
   * */
  numForests: function numForests() {
    return this.forests_.length;
  },

  /**
   * Call a function for each Forest in this TreeSeq.
   *
   *  forEachForest(callback [, thisContext])
   *      callback (function): The function to evaluate for each Forest. This
   *          function is passed the Forest, the index of the Forest, and this
   *          TreeSeq.
   *      thisContext (object, optional): If provided, the callback will be
   *          executed with thisContext, instead of the global object, as its
   *          this context.
   *
   *    Returns this TreeSeq.
   * */
  forEachForest: function forEachForest(callback, thisContext) {
    var that = thisContext? thisContext : window;
    this.forests_.forEach(function(forest, i) {
      callback.call(that, forest, i, this);
    }, this);
    return this;
  }
});
