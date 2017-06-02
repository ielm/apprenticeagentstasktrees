var width = 1000;
var height = 520;

var numTrees;
var currentTree = 0;

var nodeWidth = 140;
var nodeHeight = 25;

var duration = 750;

/* Utility function for constructing the tree structure. Takes an array of
 * nodes parsed from the input JSON file and updates the given infoObj (used
 * as a map, indexed by node names) with ancillary info about the node. */
function updateNodeInfo(sourceArr, infoObj) {
  sourceArr.forEach(function(node) {
    if (!infoObj[node.name]) {
      infoObj[node.name] = {nextId: 0, prevPos: []};
    }

    var nodeInfo = infoObj[node.name];
    
    Object.assign(nodeInfo, node);

    if (nodeInfo.parents.length === 0)
      infoObj.$root = nodeInfo;
  });
}

/* Utility function for constructing a tree structure from the given infoObj.
 * If the rootName is undefined, the returned tree structure will have
 * infoObj.$root as its root node. Questioned nodes will have the property
 * "questioned" set to true, and their descendents will have the property
 * "q_desc" set to true. */
function createTree(infoObj, rootName, questioned) {
  var rootInfo = rootName ? infoObj[rootName] : infoObj.$root;

  var root = {name: rootInfo.name, id: rootInfo.nextId, children: [] };
  ++rootInfo.nextId;

  if (rootInfo.parents.length > 1) root.questioned = true;
  if (questioned) root.q_desc = true;

  rootInfo.children.forEach(function(child) {
    root.children.push(createTree(infoObj, child, root.questioned || root.q_desc));
  });

  return root;
}

function updateTree(infoObj, oldRoot, questioned) {
  if (!oldRoot) return createTree(infoObj);

  var rootInfo = infoObj[oldRoot.name];

  var root = {}; Object.assign(root, oldRoot);
  root.children = [];
  root.questioned = rootInfo.parents.length > 1;
  root.q_desc = questioned === true;

  var passQuestioned = root.questioned || root.q_desc;

  var oldChildren = oldRoot.children.map(function(c) { return c.name; });
  rootInfo.children.forEach(function(c) {
    var idx = oldChildren.indexOf(c);
    if (idx > -1) {
      root.children.push(updateTree(infoObj, oldRoot.children[idx], passQuestioned));
    }
    else {
      root.children.push(createTree(infoObj, c, passQuestioned));
    }
  });

  return root;
}

function getPrevPos(d3Node, infoObj) {
  var nodeName = d3Node.data.name;
  var nodeId = d3Node.data.id;

  if (infoObj[nodeName].prevPos[nodeId]) {
    return infoObj[nodeName].prevPos[nodeId];
  }
  else if (!d3Node.parent) {
    return {x: d3Node.x, y: d3Node.y};
  }
  else {
    return {x: d3Node.parent.x0, y: d3Node.parent.y0 };
  }
}

$(function() {
  d3.selectAll("svg")
      .attr("width", width)
      .attr("height", height);

  var treeLayout = d3.tree()
      .size([width, height])
      .separation(function(a,b) { return a.parent == b.parent ? 1 : 1.15; } );

  d3.json("sample2.json", function(error, value) {
    if (error) throw error;

    console.log(value);
    numTrees = value.length;
    var treeStructs = [];
    var trees = [];
    var nodeInfo = {};

    value.forEach(function(nodeArr) {
      updateNodeInfo(nodeArr, nodeInfo);
      var treeStruct = updateTree(nodeInfo, treeStructs[treeStructs.length - 1]);

      var d3Tree = d3.hierarchy(treeStruct);
      treeLayout(d3Tree);

      var yStep = height / (d3Tree.height + 2);
      d3Tree.each(function(node) {
        node.y = yStep * (node.depth + 1);
        var prevPos = getPrevPos(node, nodeInfo);
        node.x0 = prevPos.x;
        node.y0 = prevPos.y;

        nodeInfo[node.data.name].prevPos[node.data.id] = {x: node.x, y:node.y};
      });

      console.log(treeStruct);
      console.log(d3Tree);

      treeStructs.push(treeStruct);
      trees.push(d3Tree);
    });

    if (trees[0]) trees.unshift(null);

    d3.selectAll("#total").text(numTrees);

    d3.selectAll("#back").on("click", function() {
      if (currentTree === numTrees) {
        $("#forward").removeClass("disabled");
      }
      if (currentTree > 0) {
        --currentTree;
        update(trees);
      }
      if (currentTree === 0) {
        $("#back").addClass("disabled");
      }
    });

    d3.selectAll("#forward").on("click", function() {
      if (currentTree === 0) {
        $("#back").removeClass("disabled");
      }
      if (currentTree < numTrees) {
        ++currentTree;
        update(trees);
      }
      if (currentTree === numTrees) {
        $("#forward").addClass("disabled");
      }
    });

    update(trees);

  });
});

var linkGen = d3.linkVertical()
    .x(function(d) { return d.x; } )
    .y(function(d) { return d.y; } );

var q_strokeColor = "darkgoldenrod";
var q_backColor = "khaki";

function update(rawData) {
  d3.selectAll("#current").text(currentTree);

  var canvas = d3.selectAll("svg");
  var nodes, links;

  if (rawData[currentTree] === null) { nodes = links = []; }
  else {
    nodes = rawData[currentTree].descendants();
    links = rawData[currentTree].links();
  }

  console.log("links:", links);
  
  var node = canvas.selectAll("g.node")
      .data(nodes, function(d) { return d.data.name + d.data.id; })
      .classed("questioned", function(d) { return d.data.questioned || d.data.q_desc; });

  var nodeEnter = node.enter().append("g")
      .attr("class", function(d) {
        return "node" + (d.data.questioned || d.data.q_desc? " questioned" : "");
      });

  nodeEnter.append("rect")
      .attr("y", -(nodeHeight / 2))
      .attr("height", nodeHeight)
      .attr("rx", nodeHeight / 2)
      .attr("ry", nodeHeight / 2);

  nodeEnter.append("text")
      .attr("dy", "0.35em")
      .attr("text-anchor", "middle")
      .attr("style", "fill: black")
      .text(function(d) { return d.data.name; } );

  nodeEnter.each(function() {
    var text = d3.select(this).select("text");
    var rect = d3.select(this).select("rect");

    var w = text.node().getBBox().width + 30;
    rect.attr("width", w)
        .attr("x", -(w / 2));
  } );

  nodeEnter.attr("transform", function(d) {
        return "translate(" + (d.x0) + "," + (d.y0)  +
          "),scale(" + 1e-6 + ")";
      });

  var nodeUpdate = node.merge(nodeEnter).transition()
      .duration(duration)
      .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + "),scale(1)"; } );

  var nodeExit = node.exit();
  nodeExit.transition()
      .duration(duration)
      .attr("transform", function(d) {
        return "translate(" + (d.x0) + "," + (d.y0) + "),scale(" + 1e-6 + ")";
      } )
      .remove();

  /*
  var link = canvas.selectAll("g.link")
      .data(links, function(d) { return d.source.data.name + d.source.data.id +
                                d.target.data.name + d.target.data.id; });

  link.selectAll("text")
      .text(function(d) { return d.target.data.questioned? "?" : ""; });

  var linkEnter = link.enter().insert("g", ".node")
      .attr("class", "link");
      //.classed("questioned", function(d) { return d.target.data.questioned; })
      //.classed("q_desc", function(d) { return d.target.data.q_desc; });

  linkEnter.append("path")
      .attr("d", function(d) {
        return linkGen({
          source: { x: d.source.x0, y: d.source.y0 },
          target: { x: d.source.x0, y: d.source.y0 }
        });
      } );

  linkEnter.append("text")
      .attr("x", function(d) { return d.source.x0 / 2 + d.target.x0 / 2; })
      .attr("y", function(d) { return d.source.y0 / 2 + d.target.y0 / 2; })
      .attr("dy", "0.35em")
      .text(function(d) { return d.target.data.questioned? "?" : ""; });

  var linkUpdate = link.merge(linkEnter)
      .classed("questioned", function(d) { return d.target.data.questioned; })
      .classed("q_desc", function(d) {
        console.log("link d1:", d);
        return d.target.data.q_desc;
      });
  
  linkUpdate.selectAll("path").transition()
      .duration(duration)
      .attr("d", function(d) { console.log("link d2:", d); return linkGen(d); });

  linkUpdate.selectAll("text").transition()
      .duration(duration)
      .attr("x", function(d) { return d.source.x / 2 + d.target.x / 2; })
      .attr("y", function(d) { return d.source.y / 2 + d.target.y / 2; });

  var linkExit = link.exit().transition()
      .duration(duration)
      .remove();

  linkExit.selectAll("path")
      .attr("d", function(d) {
        return linkGen({
          source: { x: d.source.x0, y: d.source.y0 },
          target: { x: d.source.x0, y: d.source.y0 }
        });
      } );

  linkExit.selectAll("text")
      .attr("x", function(d) { return d.source.x0 / 2 + d.target.x0 / 2; })
      .attr("y", function(d) { return d.source.y0 / 2 + d.target.y0 / 2; });
  */

  var link = canvas.selectAll(".link")
      .data(links, function(d) {
        return d.source.data.name + d.source.data.id +
          d.target.data.name + d.target.data.id;
      });

  var linkEnter = link.enter().insert("g", ".node")
      .attr("class", "link");

  linkEnter.append("path")
      .attr("d", function(d) {
        return linkGen({
          source: { x: d.source.x0, y: d.source.y0 },
          target: { x: d.source.x0, y: d.source.y0 }
        });
      });

  linkEnter.append("text")
      .attr("transform", function(d) {
        return "translate(" + d.source.x0 + "," + d.source.y0 + ")";
      })
      .attr("opacity", 1e-6)
      .attr("dy", "0.35em");

  var linkUpdate = link.merge(linkEnter)
      .classed("questioned", function(d) { return d.target.data.questioned; })
      .classed("q_desc", function(d) { return d.target.data.q_desc; });

  linkUpdate.select("text")
      .text(function(d) { return d.target.data.questioned? "?" : ""; })
    .transition()
      .duration(duration)
      .attr("transform", function(d) {
        return "translate(" + ((d.source.x + d.target.x) / 2) + "," +
          ((d.source.y + d.target.y) / 2) + ")";
      })
      .attr("opacity", "100%");

  linkUpdate.select("path").transition()
      .duration(duration)
      .attr("d", linkGen);

  var linkExit = link.exit().transition()
      .duration(duration)
      .remove();

  linkExit.select("text")
      .attr("transform", function(d) {
        return "translate(" + d.source.x0 + "," + d.source.y0 + ")";
      })
      .attr("opacity", 1e-6);

  linkExit.select("path")
      .attr("d", function(d) {
        return linkGen({
          source: { x: d.source.x0, y: d.source.y0 },
          target: { x: d.source.x0, y: d.source.y0 }
        });
      });
}
