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
 *  forestRenderData.forest (Forest): the original Forest from which this
 *      ForestRenderData was constructed.
 * */
function ForestRenderData(forest, width, height, separation) {
  this.trees = [];
  this.forest = forest;
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
    });
  });
}
ForestRenderData.prototype = {
  treeLayout: d3.tree().nodeSize([1,1])
                .separation(function(a,b) { return a.parent === b.parent ? 1 : 1.15; }),

  descendants: function() {
    var ret = [];
    this.trees.forEach(function(tree) {
      ret = ret.concat(tree.descendants());
    });
    return ret;
  },

  links: function() {
    var ret = [];
    this.trees.forEach(function(tree) {
      ret = ret.concat(tree.links());
    });
    return ret;
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
 *      each transition between stages of the tree. Defaults to 1500.
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
  this.transitionDuration = 1500;

  Object.defineProperty(this, "length", {
    __proto__: null,
    get: function() { return this.stages.length; }
  });

  this.setTreeSeq(treeSeq);
}
TreeRenderer.prototype = {

  setTreeSeq: function(treeSeq) {
    if (!treeSeq instanceof TreeSeq)
      throw typeError("passed object is not an instance of TreeSeq");
    this.treeSeq = treeSeq;
    this.recalculateStages();
  },

  setSvg: function(selector) {
    d3.selectAll(this.svg)
      .selectAll("*")
        .remove();

    this.svg = selector;
    this.redraw();
  },

  recalculateStages: function() {
    this.stages = [];
    this.treeSeq.stages.forEach(function(forest) {
      this.stages.push(new ForestRenderData(forest, this.width, this.height, 1.25));
    }, this);
    this.redraw();
  },

  redraw: function() {
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
        .data(nodes, function(d) { return d.data.id; });

    var nodeEnter = node.enter().append("g")
        .attr("class", "node");

    nodeEnter.append("text")
        .attr("dy", "0.35em")
        .attr("text-anchor", "middle");

    nodeEnter.append("rect");

    var nodeUpdate = node.merge(nodeEnter)
        .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });

    nodeUpdate.select("text")
        .text(function(d) { return d.data.name === "" ? "?" : d.data.name; });

    nodeUpdate.each(function() {
      var text = d3.select(this).select("text");
      var w = text.node().getBBox().width + 30;
      var h = text.node().getBBox().height + 10;

      d3.select(this).select("rect")
          .attr("x", -(w / 2))
          .attr("y", -(h / 2))
          .attr("width", w)
          .attr("height", h)
          .attr("rx", h / 2)
          .attr("ry", h / 2)
          .lower();
    });

    var nodeExit = node.exit().remove();

    var link = svg.selectAll("g.link")
        .data(links, function(d) { return d.source.data.id + "-" + d.target.data.id; });

    var linkEnter = link.enter().insert("g", "g.node")
        .attr("class", "link");

    linkEnter.append("path");

    var linkUpdate = link.merge(linkEnter)
      .select("path")
        .attr("d", this.linkGen);

    var linkExit = link.exit().remove();
  },

  nextStage: function() {
    if (this.curStage >= this.length - 1) return;
    ++this.curStage;
    this.redraw();
  },

  prevStage: function() {
    if (this.curStage <= 0) return;
    --this.curStage;
    this.redraw();
  },

  transition: function(prev, next) {
    var prevForestRender = this.stages[prev];
    var nextForestRender = this.stages[next];
    var prevForest = prevForestRender.forest;
    var nextForest = nextForestRender.forest;

    nextForest.trees.forEach(function(root) {
      root.each(function(node) {
        var nodeData = node.data;

        // In progress
      });
    });
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
