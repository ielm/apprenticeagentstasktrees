var width = 960;
var height = 480;

var margin = {left: 20, right: 20, top: 20, bottom: 20};

var numTrees;
var currentTree = 0;

var nodeWidth = 140;
var nodeHeight = 25;

$(document).ready(function() {
  d3.selectAll("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("class", "canvas")
      .attr("transform", function() { return "translate(" + margin.left + "," + margin.top + ")" })
      .attr("width", width)
      .attr("height", height);

  var treeLayout = d3.tree()
      .size([width, height])
      //.nodeSize([nodeWidth, nodeHeight])
      .separation(function(a,b) { return a.parent == b.parent ? 1 : 1.15; } );

  d3.json("sample.json", function(error, value) {
    numTrees = value.length;
    value = value.map(function(el) { return d3.hierarchy(el); });
    value.forEach(function(el) {
      treeLayout(el);
      var yStep = height / (el.height + 2)
      el.each(function(d) { d.y = (d.depth + 1) * yStep; } );
    });

    if (value[0]) value.unshift(null);

    d3.selectAll("#total").text(numTrees);

    d3.selectAll("#back").on("click", function() {
      if (currentTree === numTrees) {
        $("#forward").removeClass("disabled");
      }
      if (currentTree > 0) {
        --currentTree;
        update(value);
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
        update(value);
      }
      if (currentTree === numTrees) {
        $("#forward").addClass("disabled");
      }
    });

    update(value);

  });
});

var nodes = undefined;
var links = undefined;

var linkGen = d3.linkVertical()
    //.source(function(d) { return [d.source.x, d.source.y + nodeHeight / 2]; } )
    //.target(function(d) { return [d.target.x, d.target.y - nodeHeight / 2]; } );
    .x(function(d) { return d.x; } )
    .y(function(d) { return d.y; } );

function update(rawData) {
  d3.selectAll("#current").text(currentTree);

  var canvas = d3.selectAll(".canvas");

  if (rawData[currentTree] === null) { nodes = links = []; }
  else {
    nodes = rawData[currentTree].descendants();
    links = rawData[currentTree].links();
  }

  var node = canvas.selectAll("g")
      .data(nodes, function(d) { return d.data.name; });

  node.attr("transform", function(d) {
        return "translate(" + d.x + "," + d.y + ")";
      } );

  var nodeEnter = node.enter().append("g")
      .attr("class", "node")
      .attr("transform", function(d) {
        return "translate(" + (d.x) + "," + d.y + ")";
      });

  nodeEnter.append("rect")
      .attr("y", -(nodeHeight / 2))
      .attr("height", nodeHeight)
      .attr("rx", nodeHeight / 2)
      .attr("ry", nodeHeight / 2);

  nodeEnter.append("text")
      .attr("dy", "0.35em")
      .attr("text-anchor", "middle")
      .text(function(d) { return d.data.name; } );

  nodeEnter.each(function() {
    var text = d3.select(this).select("text");
    var rect = d3.select(this).select("rect");

    var w = text.node().getBBox().width + 30;
    rect.attr("width", w)
        .attr("x", -(w / 2));
  } );

  var nodeExit = node.exit().remove();

  var link = canvas.selectAll("path")
      .data(links, function(d) { return d.source.name + d.target.name; });

  link.attr("d", linkGen);

  var linkEnter = link.enter().insert("path", "g")
      .attr("class", "link")
      .attr("d", linkGen);

  var linkExit = link.exit().remove();
}
