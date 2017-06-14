/**
 * Construct a new ForestRenderData object. ForestRenderDatas contain a D3.js
 * representation of each tree in a forest.
 *
 * Parameters:
 *  forest (Forest): the Forest object from which to generate this render data.
 *  width (int): the width, in pixels, of the area in which this forest is to
 *      be rendered.
 *  height (int): the height, in pixels, of the area in which this forest is to
 *      be rendered.
 *  separation (float): the minimum separation between adjacently-placed
 *      trees. This is a relative measure, with 1 being equal to the minimum
 *      separation between sibling nodes of the same tree.
 *
 * ForestRenderData instance members:
 *  forestRenderData.trees (array[D3 node]): the array of tree roots in this
 *      forest, in the format of a D3.js hierarchy with a tree layout applied.
 *  forestRenderData.nodes (Object): an Object that maps each node's render ID
 *      to the corresponding D3.js node in this forest.
 *  forestRenderData.forest (Forest): the original Forest used to construct
 *      this ForestRenderData.
 * */
function ForestRenderData(forest, width, height, separation) {
  this.trees = [];
  this.nodes = {};
  this.forest = forest;
  var nodes = this.nodes;
  var minMaxes = [];

  var globalMax = 1;
  var maxHeight = 0;
  
  forest.trees.forEach(function(tree, treeIndex) {
    this.trees.push(this.treeLayout(d3.hierarchy(tree)));
    if (this.trees.back.height > maxHeight) maxHeight = this.trees.back.height;

    minMaxes.push({ min: this.trees.back.x,
                    max: this.trees.back.x,
                    heightMins: [],
                    heightMaxes: [] });

    var minMax = minMaxes.back;
    var tree = this.trees.back;

    this.trees.back.each(function(node) {
      var nodeHeight = tree.height - node.depth;
      if (node.x < minMax.min)
        minMax.min = node.x;
      if (node.x > minMax.max)
        minMax.max = node.x;
      if (minMax.heightMins[nodeHeight] === undefined || node.x < minMax.heightMins[nodeHeight])
        minMax.heightMins[nodeHeight] = node.x;
      if (minMax.heightMaxes[nodeHeight] === undefined || node.x > minMax.heightMaxes[nodeHeight])
        minMax.heightMaxes[nodeHeight] = node.x;
    });

    var shift = 0;
    if (treeIndex === 0) {
      var shift = globalMax - minMax.min;
    }
    else {
      var prevMinMax = minMaxes[minMaxes.length - 2];
      prevMinMax.heightMaxes.forEach(function(prevHMax, i) {
        if (minMax.heightMins[i] === undefined) return;
        if (shift + minMax.heightMins[i] < prevHMax + separation)
          shift = prevHMax + separation - minMax.heightMins[i];
      });
    }

    this.trees.back.each(function(node) { node.x += shift; });
    minMax.min += shift;
    minMax.max += shift;
    minMax.heightMins.forEach(function(x, i, arr) { arr[i] += shift; });
    minMax.heightMaxes.forEach(function(x, i, arr) { arr[i] += shift; });

    globalMax = minMax.max;
  }, this);

  globalMax += 1;
  var mult = width / globalMax;

  var ySteps = maxHeight + 2;
  var yStepStride = height / ySteps;

  this.trees.forEach(function(root) {
    root.each(function(node) {
      var nodeHeight = root.height - node.depth;
      node.x *= mult;
      node.y = height - yStepStride * (nodeHeight + 1);
      nodes[node.data.renderId] = node;
    });
  }, this);
}
ForestRenderData.prototype = {
  /**
   * The D3 tree layout function used by this ForestRenderData.
   * */
  treeLayout: d3.tree().nodeSize([1,1])
                .separation(function(a,b) { return a.parent === b.parent ? 1 : 1.075; }),

  /**
   * A wrapper around the D3 node object's descendants function. Returns an
   * array of all D3 nodes in this ForestRenderData.
   * */
  descendants: function() {
    var ret = [];
    this.trees.forEach(function(tree) {
      ret = ret.concat(tree.descendants());
    });
    return ret;
  },

  /**
   * A wrapper around the D3 node object's links function. Returns an array of
   * all D3 links (objects with properties 'source' and 'target' set to D3
   * nodes) in this ForestRenderData.
   * */
  links: function() {
    var ret = [];
    this.trees.forEach(function(tree) {
      ret = ret.concat(tree.links());
    });
    return ret;
  },

  /**
   * Reconstruct this ForestRenderData with new width, height, and separation
   * values.
   * */
  regenerateData: function(width, height, separation) {
    ForestRenderData.call(this, this.forest, width, height, separation);
  }
};

/**
 * Construct a new TreeRenderer object, with its tree data initialized to
 * the given TreeSeq. TreeRenderers use D3.js to draw trees into SVG elements
 * with specified IDs.
 *
 * Parameters:
 *  width (int): the width in pixels of the SVG in which the tree will be drawn.
 *  height (int): the height in pixels of the SVG in which the tree will be drawn.
 *  svgId (string): the CSS selector -- ID, class, or tag name -- by which the
 *      SVG element(s) in which to draw this tree can be identified.
 *  treeSeq (TreeSeq): the initial TreeSeq object for this renderer.
 *
 * TreeRenderer instance members:
 *  treeRenderer.width (int): the width of the target SVG element(s).
 *  treeRenderer.height (int): the height of the target SVG element(s).
 *  treeRenderer.svg (string): the CSS selector of the target SVG element(s).
 *  treeRenderer.treeSeq (TreeSeq): the TreeSeq object on which this
 *      TreeRenderer's data is based.
 *  treeRenderer.stages (array[ForestRenderData]): the actual per-stage data
 *      used by this TreeRenderer to draw the growing tree.
 *  treeRenderer.curStage (int): the index of the currently displayed stage in
 *      the stages array.
 *  treeRenderer.length (int, readonly): the number of stages in the current
 *      TreeSeq.
 *  treeRenderer.transitionDuration (int): the duration, in miliseconds, of
 *      each transition between stages of the tree. Defaults to 1000.
 *
 * TreeRenderer constructor properties:
 *  TreeRenderer.hoveredNode (DOM element): the <g> element representing the
 *      node that the user has hovered over with the mouse. Null if no such 
 *      node exists.
 * 
 * Direct assignment to member fields of TreeRenderer should be avoided.
 * Instead, use the methods defined below.
 * */
function TreeRenderer(width, height, svgId, treeSeq) {
  this.width = width;
  this.height = height;
  this.svg = svgId;
  this.stages = [];
  this.curStage = 0;
  this.transitionDuration = 1000;

  Object.defineProperty(this, "length", {
    __proto__: null,
    get: function() { return this.stages.length; }
  });

  this.setTreeSeq(treeSeq);
}
TreeRenderer.hoveredNode = null;

/**
 * Set the currently hovered node, raising it to the top of the z-order and
 * animating its scale-up, and also animating any previous hovered node's scale
 * down.
 *
 * Parameters:
 *  node (DOM element): the <g> element to set as the newly hovered node. If
 *      null, remove all hovering effects from all nodes.
 * */
TreeRenderer.setHovered = function(node) {
  if (this.hoveredNode && this.hoveredNode.isSameNode(node)) return;

  if (this.hoveredNode) {
    var hoveredNode = d3.select(this.hoveredNode);
    hoveredNode.transition("hoverScale")
        .duration(250)
        .ease(d3.easeSinInOut)
        .attr("transform", function() {
          return setScale(1, hoveredNode.attr("transform"));
        });
  }

  if (node) {
    var hoveredNode = d3.select(node);
    hoveredNode.raise()
      .transition("hoverScale")
        .duration(250)
        .ease(d3.easeSinInOut)
        .attr("transform", function() {
          return setScale(1.5, hoveredNode.attr("transform"));
        });
  }

  this.hoveredNode = node;
};

TreeRenderer.prototype = {

  /**
   * Change the TreeSeq rendered by this TreeRenderer. This will cause the
   * tree to be redrawn.
   *
   * Parameters:
   *  treeSeq (TreeSeq): the new TreeSeq object.
   * */
  setTreeSeq: function(treeSeq) {
    if (!treeSeq instanceof TreeSeq)
      throw typeError("passed object is not an instance of TreeSeq");
    this.treeSeq = treeSeq;
    this.recalculateStages();
  },

  /**
   * Set the CSS selector used to identify the SVG element in which to render
   * this tree.
   *
   * Paramters:
   *  selector (string): the new CSS selector.
   * */
  setSvg: function(selector) {
    var curSelection = d3.select(this.svg).selectAll("*");
    var nodes = curSelection.nodes();
    var newSelection = d3.select(selector).node();
    
    nodes.forEach(function(n) {
      newSelection.appendChild(n);
    });
    /*
    d3.selectAll(this.svg)
      .selectAll("*")
        .remove();
    */

    this.svg = selector;
    d3.select(this.svg).attr("width", this.width).attr("height", this.height);
  },

  /**
   * Reconstructs all ForestRenderData objects in this TreeRenderer from the
   * data in the current TreeSeq object. This will cause the tree to be
   * redrawn. Otherwise, this will have no observable effect unless the
   * TreeRenderer's TreeSeq object has changed.
   * */
  recalculateStages: function() {
    this.stages = [];
    this.treeSeq.stages.forEach(function(forest) {
      this.stages.push(new ForestRenderData(forest, this.width, this.height, 1.15));
    }, this);
    this.redraw();
  },

  /**
   * Redraws the current stage, without any animated transition.
   * */
  redraw: function() {
    var linkGen = this.linkGen;
    var svg = d3.selectAll(this.svg)
        .attr("width", this.width)
        .attr("height", this.height);

    var curStage = this.stages[this.curStage];
    if (curStage === null) {
      var nodes = [];
      var links = [];
    }
    else {
      var nodes = curStage.descendants();
      var links = curStage.links();
    }

    var node = svg.selectAll("g.node")
        .data(nodes, function(d) { return d.data.renderId; });

    var nodeEnter = node.enter().append("g")
        .attr("class", "node");

    nodeEnter.append("text");
    nodeEnter.append("rect");

    nodeEnter.on("pointerenter", function() { TreeRenderer.setHovered(this); })
        .on("pointerleave", function() { TreeRenderer.setHovered(null); });

    var nodeUpdate = node.merge(nodeEnter);
      
    nodeUpdate
        .classed("questioned", function (d) { return d.data.questioned; })
        .attr("transform", function(d) {
          return "translate(" + d.x + "," + d.y + ")";
        });

    nodeUpdate.select("text")
        .attr("dy", "0.35em")
        .attr("text-anchor", "middle")
        .text(function(d) { return d.data.name === "" ? "?" : d.data.name; });

    nodeUpdate.each(function(d) {
      var text = d3.select(this).select("text").node();
      d.w = text.getBBox().width + 20;
      d.h = text.getBBox().height + 8;
      d.h += d.h * d.h / d.w;
      if (d.h > d.w) d.h = d.w;
    });

    nodeUpdate.select("rect")
        .attr("x", function(d) { return -(d.w / 2); })
        .attr("y", function(d) { return -(d.h / 2); })
        .attr("width", function(d) { return d.w; })
        .attr("height", function(d) { return d.h; })
        .attr("rx", function(d) { return d.h / 2; })
        .attr("ry", function(d) { return d.h / 2; })
        .lower();

    var nodeExit = node.exit().remove();

    var link = svg.selectAll("g.link")
        .data(links, function(d) { return d.target.data.renderId; });

    var linkEnter = link.enter().insert("g", "g.node")
        .attr("class", "link");

    linkEnter.append("path");
    linkEnter.append("text");

    var linkUpdate = link.merge(linkEnter)
        .classed("questioned", function(d) {
          return d.target.data.questioned && !d.source.data.questioned;
        })
        .classed("q_desc", function(d) { return d.source.data.questioned; });

    linkUpdate.select("text")
        .attr("text-anchor", "middle")
        .attr("dy", "0.35em")
        .text("?")
        .attr("x", function(d) { return (d.source.x + d.target.x) / 2; })
        .attr("y", function(d) { return (d.source.y + d.target.y) / 2; })
        .attr("opacity", function(d) {
          return !d.source.data.questioned && d.target.data.questioned ? 1 : 1e-6;
        });

    linkUpdate.select("path")
        .attr("d", linkGen);

    var linkExit = link.exit().remove();
  },

  /**
   * Animates the tree to its new state. Calculates the previous positions of
   * each node in the current stage of the tree, assigning x0 and y0 properties
   * on each D3 node in the TreeRenderer.
   *
   * Parameters:
   *  prev (int): the index of the stage from which the tree is being
   *      transitioned.
   *  next (int): the index of the stage to which the tree is being
   *      transitioned.
   * */
  transition: function(prev, next) {
    var svg = d3.selectAll(this.svg)
        .attr("width", this.width)
        .attr("height", this.height);
    
    if (svg.node())
      d3.interrupt(svg.node());

    var prevForest = this.stages[prev];
    var nextForest = this.stages[next];

    function calcZeroCoords(forestFrom) {
      return function(node) {
        var nodeData = node.data;
        var nodeId = node.data.renderId

        var strNodeId = new String(nodeId).valueOf();
        if (! (strNodeId in forestFrom.nodes)) {
          if (!node.parent) {
            node.x0 = node.x;
            node.y0 = node.y;
          }
          else {
            var parent = node.parent;
            var parentId = parent.data.renderId;
            while (!forestFrom.nodes[parentId]) {
              if (parent.parent) {
                parent = parent.parent;
                parentId = parent.data.renderId;
              }
              else {
                parentId = null;
                break;
              }
            }

            if (parentId !== null) {
              node.x0 = forestFrom.nodes[parentId].x;
              node.y0 = forestFrom.nodes[parentId].y;
            }
            else {
              node.x0 = node.parent.x0;
              node.y0 = node.parent.y0;
            }
          }
        }
      };
    }

    nextForest.trees.forEach(function(root) {
      root.each(calcZeroCoords(prevForest));
    });
    prevForest.trees.forEach(function(root) {
      root.each(calcZeroCoords(nextForest));
    });

    var duration = this.transitionDuration;
    var linkGen = this.linkGen;

    var curStage = this.stages[this.curStage];
    if (curStage === null) {
      var nodes = [];
      var links = [];
    }
    else {
      var nodes = curStage.descendants();
      var links = curStage.links();
    }

    nodes.forEach(function(n) {
      if (n.x0 === undefined) n.x0 = n.x;
      if (n.y0 === undefined) n.y0 = n.y;
    });

    var node = svg.selectAll("g.node")
        .data(nodes, function(d) { return d.data.renderId; });

    var nodeEnter = node.enter().append("g")
        .attr("class", "node");

    var nodeUpdate = node.merge(nodeEnter);
    nodeUpdate.each(function(d) {
      var text = d3.select(this).append("text")
          .attr("class", "REMOVETHIS")
          .attr("opacity", 0)
          .text(function(d) { return d.data.name === "" ? "?" : d.data.name; })
        .node();
      d.w = text.getBBox().width + 20;
      d.h = text.getBBox().height + 8;
      d.h += d.h * d.h / d.w;
      if (d.h > d.w) d.h = d.w;
      d3.select(text).remove();
    });

    nodeEnter.append("text")
        .attr("dy", "0.35em")
        .attr("text-anchor", "middle")
        .text(function(d) { return d.data.name === "" ? "?" : d.data.name; });

    nodeEnter.attr("transform", function(d) {
      return "translate(" + d.x0 + "," + d.y0 + "),scale(" + 1e-6 + ")";
    });

    nodeEnter.append("rect")
        .attr("x", function(d) { return -(d.w / 2); })
        .attr("y", function(d) { return -(d.h / 2); })
        .attr("width", function(d) { return d.w; })
        .attr("height", function(d) { return d.h; })
        .attr("rx", function(d) { return d.h / 2; })
        .attr("ry", function(d) { return d.h / 2; })
        .lower();

    nodeEnter.on("pointerenter", function() { TreeRenderer.setHovered(this); })
        .on("pointerleave", function() { TreeRenderer.setHovered(null); });

    nodeUpdate.transition("position")
        .duration(this.transitionDuration)
        .attr("transform", function(d) {
          return "translate(" + d.x + "," + d.y + "),scale(1)";
        })
      .select("text")
        .attr("x", 0)
        .attr("y", 0);

    nodeUpdate.classed("questioned", function (d) { return d.data.questioned; });

    nodeUpdate.select("text").transition("textFade")
       .duration(this.transitionDuration * 0.2)
        .ease(d3.easeLinear)
        .attr("opacity", function(d) {
          var text = d3.select(this).text();
          return text === d.data.name || text === "?" && d.data.name === "" ? 1 : 1e-6;
        })
      .transition("textFade")
        .duration(this.transitionDuration * 0.4)
        .text(function(d) { return d.data.name === "" ? "?" : d.data.name; })
        .attr("opacity", 1);

    nodeUpdate.select("rect").transition("rectScale")
        .duration(function(d) {
          return duration * 0.45;
          //return d.w < this.getBBox().width ? duration : duration * 0.75;
        })
        .ease(d3.easeQuad)
        .attr("x", function(d) { return -(d.w / 2); })
        .attr("y", function(d) { return -(d.h / 2); })
        .attr("width", function(d) { return d.w; })
        .attr("height", function(d) { return d.h; })
        .attr("rx", function(d) { return d.h / 2; })
        .attr("ry", function(d) { return d.h / 2; });

    var nodeExit = node.exit().transition("position")
        .duration(duration)
        .attr("transform", function(d) {
          return "translate(" + d.x0 + "," + d.y0 + "),scale(" + 1e-6 + ")";
        })
        .remove();

    var link = svg.selectAll("g.link")
        .data(links, function(d) { return d.target.data.renderId; });

    var linkEnter = link.enter().insert("g", "g.node")
        .attr("class", "link");

    linkEnter.append("path")
        .attr("d", function(d) {
          return linkGen({source: [d.target.x0, d.target.y0], target: [d.target.x0, d.target.y0] });
        });

    linkEnter.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", "0.35em")
        .text("?")
        .attr("x", function(d) { return d.target.x0; })
        .attr("y", function(d) { return d.target.y0; })
        .attr("opacity", 1e-6);

    var linkUpdate = link.merge(linkEnter)
        .classed("questioned", function(d) {
          return d.target.data.questioned && !d.source.data.questioned;
        })
        .classed("q_desc", function(d) { return d.source.data.questioned; });

    linkUpdate.select("path").transition("pathMove")
        .duration(duration)
        .attr("d", linkGen);

    linkUpdate.select("text").transition("textMove")
        .duration(duration)
        .attr("x", function(d) { return (d.source.x + d.target.x) / 2; })
        .attr("y", function(d) { return (d.source.y + d.target.y) / 2; });

    linkUpdate.select("text").transition("textFade")
        .duration(duration * 0.75)
        .ease(d3.easeLinear)
        .attr("opacity", function(d) {
          return !d.source.data.questioned && d.target.data.questioned ? 1 : 1e-6;
        });

    var linkExit = link.exit();
    
    linkExit.select("path").transition("pathMove")
        .duration(duration)
        .attr("d", function(d) {
          return linkGen({source: [d.target.x0, d.target.y0], target: [d.target.x0, d.target.y0]});
        });

    linkExit.select("text").transition("textMove")
        .duration(duration)
        .attr("x", function(d) { return d.target.x0; })
        .attr("y", function(d) { return d.target.y0; });

    linkExit.select("text").transition("textFade")
        .duration(duration * 0.75)
        .ease(d3.easeLinear)
        .attr("opacity", 1e-6);

    linkExit.transition()
        .duration(duration)
        .remove();

    var treeRenderer = this;
    svg.transition().duration(duration).on("end", function() { treeRenderer.redraw(); });
  },

  /**
   * Increments the current stage and transitions the tree to the new state.
   * If the current stage cannot be incremented, has no effect.
   * */
  nextStage: function() {
    if (this.curStage >= this.length - 1) return;
    ++this.curStage;
    this.transition(this.curStage - 1, this.curStage);
  },

  /**
   * Decrements the current stage and transitions the tree to the new state.
   * If the current stage cannot be decremented, has no effect.
   * */
  prevStage: function() {
    if (this.curStage <= 0) return;
    --this.curStage;
    this.transition(this.curStage + 1, this.curStage);
  },

  linkGen: d3.linkVertical()
      .x(function(d) {
        if (d instanceof Array)
          return d[0];
        else return d.x;
      })
      .y(function(d) {
        if (d instanceof Array)
          return d[1];
        else return d.y;
      })
};
