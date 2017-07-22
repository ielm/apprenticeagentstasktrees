var margin = { top: 50, bottom: 50, left: 10, right: 75 };

var totalWidth = 1200;
var totalHeight = 620;

var sidebarScale = 0.2;

var width = totalWidth / (1 + sidebarScale);
var sidebarWidth = width * sidebarScale;

var height = totalHeight;

Object.defineProperty(this, "sidebarY", {
  get: function() {
    var sidebar = d3.select(".sidebar");
    if (sidebar.empty()) return 0;

    else return getTranslate(sidebar.node()).y;
  }
});
var prevScrollTime = 0;

/**
 * primaryTree, displayedTree, and inputTrees contain elements of the following
 * type:
 *  {
 *    svg: <string, CSS selector for this tree's <g> element>,
 *    render: <TreeRenderer for this tree>,
 *    node: <DOM Element, the actual <g> element for this tree>,
 *    inputs: <array[string], the original inputs for that stage, or the number
 *            and file name of the tree that generated that stage for the
 *            primary tree>,
 *    filename: <string, the name of the uploaded file that resulted in this
 *              tree, undefined for primary tree>
 *    TMRdata: <string, the contents of the uploaded file that resulted in
 *             this tree, undefined for primary tree>
 *    treedata: <array[object], the parsed JSON returned by the backend service
 *              for this tree>
 *  }
 * */
var primaryTree = null;
var inputTrees = [];
var displayedTree = null;
var displayedTreeIndex = null;

/**
 * Send an HTTP DELETE request to the server, remove all client-side tree
 * data, and replace the "No data" overlay.
 * */
function resetTree(noOverlay) {
  var remove = d3.select(".canvas").selectAll("*")
      .attr("opacity", function() {
        var opac = this.attributes.getNamedItem("opacity");
        return opac? opac.value : "1";
      })
    .transition("resetFade")
      .duration(500)
      .ease(d3.easeLinear)
      .attr("opacity", 1e-6)
      .remove();

  $.ajax({
    url: $("#url")[0].value + "/alpha/mergetree",
    method: "DELETE",
    error: resetTree,
    success: function() {
      primaryTree = null;
      inputTrees = [];
      displayedTree = null;
      displayedTreeIndex = null;

      /*
      var canvas = d3.select(".canvas");

      canvas.selectAll("*")
      */
      //remove
      if (!noOverlay) {
        var canvas = d3.select(".canvas");
        canvas.append("rect")
            .attr("class", "nodata")
            .attr("width", totalWidth)
            .attr("height", totalHeight)
            .attr("opacity", 1e-6);
        canvas.append("text")
            .attr("class", "nodata")
            .attr("x", totalWidth / 2)
            .attr("y", totalHeight / 2)
            .text("No data")
            .attr("opacity", 1e-6);
        canvas.selectAll(".nodata").transition("resetFade")
            .delay(500)
            .duration(500)
            .ease(d3.easeLinear)
            .attr("opacity", 1);
      }

      $("#current").html("0");
      $(".input").html("");
      $("#back").addClass("disabled");
      $("#forward").addClass("disabled");
    }
  });
}

/**
 * Set the displayed tree to that with the given index in inputTrees. An index
 * of -1 indicates the primary tree. All other indices are an error.
 *
 * If the index argument is omitted, it defaults to the most recently added
 * input tree.
 *
 * This function also sets up all sidebar elements, event listeners, and
 * animations.
 *
 * Removes the "No data" overlay if present.
 * */
function setDisplayedTree(index) {
  var firstTime = false;
  if (displayedTreeIndex === null) {
    d3.selectAll(".nodata").transition("resetFade")
        .duration(500)
        .ease(d3.easeLinear)
        .attr("opacity", 1e-6)
        .remove();
    firstTime = true;

    // Set up sidebar
    d3.select(".canvas").append("g")
        .attr("class", "sidebar")
        .on("wheel", function() {
          var dy = -d3.event.deltaY;
          var now = Date.now();
          if (now - prevScrollTime < 150) dy *= 3;
          prevScrollTime = now;

          var sidebarHeight = inputTrees.length * height * sidebarScale;

          if (sidebarHeight < height) dy = 0;
          else if (sidebarY + dy > 0) dy = -sidebarY;
          else if (sidebarY + dy + sidebarHeight < height)
            dy = height - sidebarY - sidebarHeight;

          d3.select(this).transition("scroll")
              .duration(500)
              .ease(d3.easeCubicOut)
              .attr("transform", "translate(0," + (getTranslate(this).y + dy) + ")")
            .select("rect")
              .attr("y", function() { return +d3.select(this).attr("y") - dy; });
        })
      .append("rect")
        .attr("opacity", 0)
        .attr("width", sidebarWidth)
        .attr("height", totalHeight + margin.top + margin.bottom)
        .attr("y", -margin.top);
  }

  var sidebar = d3.select(".sidebar");

  // default index
  if (index === undefined) var i = inputTrees.length - 1;
  else var i = index;

  // shuffle references between displayedTree, primaryTree, and inputTrees
  if (displayedTreeIndex === -1) primaryTree = displayedTree;
  else if (displayedTreeIndex !== null) inputTrees[displayedTreeIndex] = displayedTree;

  if (i === -1) {
    displayedTree = primaryTree;
    primaryTree = null;
  }
  else {
    displayedTree = inputTrees[i];
    inputTrees[i] = null;
  }

  displayedTreeIndex = i;

  // set up data for the D3.js sidebar data join
  var data = inputTrees.slice();
  if (i >= 0) {
    data.splice(i, 1);
    data.unshift(primaryTree);
  }

  var sidebarTrees = sidebar.selectAll("g.docked")
      .data(data, function(d) { return d && d.svg; });

  // move new sidebar entries into sidebar element
  var sidebarEnter = sidebarTrees.enter()
    .append(function(d) { return d.node; })
      .classed("docked", true)
      .attr("transform", function() {
        var translate = getTranslate(this);
        var newTransform = setTranslate(this, translate.x, translate.y - sidebarY);
        return newTransform;
      });

  // move new displayed tree out of sidebar element
  var sidebarExit = sidebarTrees.exit()
      .classed("docked", false)
      .each(function() {
        var that = this;
        d3.select(".canvas").append(function() { return that; });
      })
      .attr("transform", function() {
        var translate = getTranslate(this);
        var newTransform = setTranslate(this, translate.x, translate.y + sidebarY);
        return newTransform;
      });

  // fancy fancy animations
  sidebarExit.raise().transition("displayPos")
      .duration(750)
      .attr("transform", "translate(" + sidebarWidth + ",0) scale(1)")
    .on("end", function(d) { d.render.redraw(); });

  if (!firstTime) {
    sidebarTrees.merge(sidebarEnter).order()
      .transition("sidebarPos")
        .duration(750)
        .attr("transform", function(d, i) {
          return "translate(0," + (i * height * sidebarScale) + ") scale(" + sidebarScale + ")";
        });
  }
  else {
    sidebarTrees.merge(sidebarEnter).order()
        .attr("transform", function(d, i) {
          return "translate(0," + (i * height * sidebarScale) + ") scale(" + sidebarScale + ")";
        });
  }

  if (d3.select(displayedTree.svg).empty())
    d3.select(".canvas").select(function() { return displayedTree.node; })
        .attr("transform", "translate(" + sidebarWidth + ",0) scale(1)");

  // more sidebar setup - labels, backing elements, hover and click listenrs
  sidebarEnter.insert("rect", "*")
      .attr("class", "sidebarBacking")
      .attr("width", width)
      .attr("height", height)
      .attr("opacity", 1e-6)
      .attr("rx", "25px")
      .attr("ry", "25px")
      .attr("fill", "cyan");
  sidebarEnter.append("text")
      .attr("class", "sidebarText")
      .attr("opacity", 1e-6)
      .attr("style", "font-size: 56pt; text-anchor: start;")
      .attr("dy", "1em")
      .attr("x", "10px")
      .attr("y", "20px")
      .attr("fill", "black")
      .text(function(d) {
        if (d === primaryTree)
          return "Primary Tree";
        else
          return "(" + (inputTrees.indexOf(d) + 1) + ") " + d.filename;
      })
    .transition("textFade")
      .delay(250)
      .duration(500)
      .ease(d3.easeLinear)
      .attr("opacity", 0.5);

  sidebarEnter
      .on("pointerenter", function() {
        d3.select(this)
            .attr("transform", function(d) {
              return setScale(sidebarScale * 1.025,
                this.attributes.getNamedItem("transform").value);
            })
          .selectAll(".sidebarBacking")
            .attr("opacity", 0.5);
      })
      .on("pointerleave", function(d) {
        d3.select(this)
            .attr("transform", function(d) {
              return setScale(sidebarScale,
                this.attributes.getNamedItem("transform").value);
            })
          .selectAll(".sidebarBacking")
            .attr("opacity", 1e-6);
      })
      .on("click", function(d) {
        if (d === primaryTree) var index = -1;
        else var index = inputTrees.indexOf(d);
        setDisplayedTree(index);
      });

  sidebarExit.selectAll(".sidebarBacking").remove();
  sidebarExit.selectAll(".sidebarText").transition("textFade")
      .duration(250)
      .ease(d3.easeLinear)
      .attr("opacity", 1e-6)
      .remove();
  sidebarExit
      .on("pointerenter", null)
      .on("pointerleave", null)
      .on("click", null);

  // update control area buttons and text
  $("#current").html(displayedTree.render.curStage);
  $(".input").html(displayedTree.inputs[displayedTree.render.curStage]);

  if (displayedTree.render.curStage > 0)
    $("#back").removeClass("disabled");
  else
    $("#back").addClass("disabled");

  if (displayedTree.render.curStage < displayedTree.render.length - 1)
    $("#forward").removeClass("disabled");
  else
    $("#forward").addClass("disabled");
}

function addTree(maketreeData, mergetreeData, filename, fileContents) {
  console.log(maketreeData, mergetreeData);
  var newTreeNodes = maketreeData.map(function(d) { return d.tree; });
  var newTreeSeq = treeSeqFromData(newTreeNodes);

  var newTreeData = {};

  newTreeData.inputs = maketreeData.map(function(d) { return d.input; });
  newTreeData.inputs.forEach(function(input, i, inputs) {
    if (input instanceof Array) {
      var newstr = "";
      input.forEach(function(d, i) {
        if (i > 0) newstr += ", ";
        newstr += d;
      });

      inputs[i] = newstr;
    }
    else inputs[i] = '"' + input + '"';
  });
  newTreeData.inputs.unshift("(Before input)");
  newTreeData.filename = filename;
  newTreeData.TMRdata = fileContents;
  newTreeData.treedata = maketreeData;

  newTreeData.node = d3.selectAll(".canvas").append("g").node();
  newTreeData.node.id = "tree" + inputTrees.length;
  newTreeData.svg = "#" + newTreeData.node.id;

  newTreeData.render = new TreeRenderer(width, height, newTreeData.svg, newTreeSeq);
  newTreeData.render.transitionDuration = 750;

  inputTrees.push(newTreeData);

  if (displayedTree === null) {
    var primTreeNodes = [mergetreeData[0].tree];
    var primTreeSeq = treeSeqFromData(primTreeNodes);

    primaryTree = { inputs: [ "(Before input)", "(1) " + newTreeData.filename ] };

    primaryTree.node = d3.selectAll(".canvas").append("g").node();
    primaryTree.node.id = "primaryTree";
    primaryTree.svg = "#" + primaryTree.node.id;
    primaryTree.treedata = mergetreeData;

    primaryTree.render = new TreeRenderer(width, height, primaryTree.svg, primTreeSeq);
    primaryTree.render.transitionDuration = 750;
  }
  else {
    var newTreeForest = treeSeqFromData([mergetreeData[0].tree]).stages[1];

    var primTree = primaryTree? primaryTree : displayedTree;

    primTree.render.treeSeq.append(newTreeForest);
    primTree.render.setTreeSeq(primTree.render.treeSeq);
    primTree.inputs.push("(" + (inputTrees.indexOf(newTreeData) + 1) + ") " + newTreeData.filename);

    primTree.treedata.push(mergetreeData[0]);
  }

  if (primaryTree) {
    setDisplayedTree(inputTrees.length - 1);
    d3.select(displayedTree.svg)
        .attr("transform", "translate(" + sidebarWidth + ",0)");
  }
  else {
    setDisplayedTree(displayedTreeIndex);
  }


  if (primaryTree) primaryTree.render.nextStage();
  else newTreeData.render.nextStage();
  $("#forward").click();
}

function saveData() {
  if (!displayedTree) {
    window.alert("Nothing to save!");
    return;
  }

  function TreeRecord(treedata) {
    this.filename = treedata.filename;
    this.TMRdata = treedata.TMRdata;
    this.treedata = treedata.treedata;
    this.curStage = treedata.render.curStage;
    this.inputs = treedata.inputs;
  }

  var data = { SAVED_DATA: true };
  data.trees = inputTrees.map(function(t, i) {
    if (t === null) var tree = displayedTree;
    else var tree = t;

    return new TreeRecord(tree);
  });
  if (primaryTree) data.trees.unshift(new TreeRecord(primaryTree));
  else data.trees.unshift(new TreeRecord(displayedTree));

  data.displayedIndex = displayedTreeIndex;

  var blob = new Blob([JSON.stringify(data)], { type: "application/json" });
  var url = URL.createObjectURL(blob);
  var a = document.createElement("a");
  a.href = url;
  a.download = "test.json";
  a.click();
  URL.revokeObjectURL(url);
}

function loadSavedData(data) {
  resetTree(true);

  var loadedPrimaryTree = data.trees[0];
  data.trees.shift();

  data.trees.forEach(function(t) {
    var nodes = t.treedata.map(function(d) { return d.tree; });
    var treeSeq = treeSeqFromData(nodes);

    var newTreeData = {};
    newTreeData.inputs = t.inputs;
    newTreeData.filename = t.filename;
    newTreeData.TMRdata = t.TMRdata;
    newTreeData.treedata = t.treedata;

    newTreeData.node = d3.selectAll(".canvas").append("g").node();
    newTreeData.node.id = "tree" + inputTrees.length;
    newTreeData.svg = "#" + newTreeData.node.id;

    newTreeData.render = new TreeRenderer(width, height, newTreeData.svg, treeSeq);
    newTreeData.render.transitionDuration = 750;
    newTreeData.render.curStage = t.curStage;
    inputTrees.push(newTreeData);
  });

  var nodes = loadedPrimaryTree.treedata.map(function(d) { return d.tree; });
  var treeSeq = treeSeqFromData(nodes);

  primaryTree = {};
  primaryTree.inputs = loadedPrimaryTree.inputs;
  primaryTree.treedata = loadedPrimaryTree.treedata;

  primaryTree.node = d3.selectAll(".canvas").append("g").node();
  primaryTree.node.id = "primaryTree";
  primaryTree.svg = "#" + primaryTree.node.id;

  primaryTree.render = new TreeRenderer(width, height, primaryTree.svg, treeSeq);
  primaryTree.render.transitionDuration = 750;
  primaryTree.render.curStage = loadedPrimaryTree.curStage;

  setDisplayedTree(data.displayedIndex);
}

$(function() {
  d3.select(".treeviz")
      .attr("width", totalWidth + margin.left + margin.right)
      .attr("height", totalHeight + margin.top + margin.bottom)
    .append("g")
      .attr("class", "canvas")
      .attr("width", totalWidth)
      .attr("height", totalHeight)
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  resetTree();

  if (document.URL.substr(0,4) === "http")
    $("input[type=text]").val("http://" + document.location.hostname + ":5000");

  var $fileupload = $("input[type=file]");
  $fileupload.change(function() {
    var $span = $("div.input_mask span");
    if ($fileupload[0].files[0]) {
      $span.removeClass("dim");
      $span.html($fileupload[0].files[0].name);
    }
    else {
      $span.addClass("dim");
      $span.html("None");
    }
  });

  $("#apiquery").submit(function(e) {
    e.preventDefault();

    var file = $("#upload")[0].files[0];
    if (file === undefined) throw new Error("No file given");

    function handleErrors(jqXHR) {
      if (jqXHR.status !== 500) {
        window.alert("Response status " + jqXHR.status + ": " + jqXHR.statusText);
        return;
      }

      else {
        var $overlay = $(document.createElement("div"));
        var $textarea = $(document.createElement("textarea"));
        $textarea.css({
          "width": "90%",
          "height": "75%",
        });
        $textarea.text(jqXHR.responseText);

        $overlay.addClass("error-overlay");
        $overlay.append("<h1>Error 500</h1>",
            $textarea,
            "<br/>",
            "<button>Dismiss</button>");
        $overlay.css({
          "position": "absolute",
          "top": "10%",
          "margin-left": "25%",
          "width": "50%",
          "height": "50%",
          "background-color": "lightgrey",
          "border-radius": "10px",
          "padding": "1em"
        });

        $overlay.find("button").click(function() {
          $overlay.remove();
        });

        $(document.documentElement).append($overlay);
      }
    }

    var reader = new FileReader();
    reader.onload = function() {
      var data = JSON.parse(reader.result);
      if (data.SAVED_DATA === true) {
        loadSavedData(data);
        return;
      }

      $.post({
        url: $("#url")[0].value + "/alpha/maketree",
        contentType: "application/json",
        data: reader.result,
        dataType: "text",
        error: handleErrors,
        success: function(maketreeData, status) {
          $.post({
            url: $("#url")[0].value + "/alpha/mergetree",
            contentType: "application/json",
            data: reader.result,
            dataType: "text",
            error: handleErrors,
            success: function(mergetreeData, status) {
              addTree(JSON.parse(maketreeData), JSON.parse(mergetreeData), file.name, reader.result);
            }
          });
        }
      });
    }
    reader.readAsText(file);
  });

  function forward() {
    if (!displayedTree) return;

    displayedTree.render.nextStage();
    if (displayedTree.render.curStage > 0)
      $("#back").removeClass("disabled");
    if (displayedTree.render.curStage >= displayedTree.render.length - 1)
      $("#forward").addClass("disabled");

    $("#current").html(displayedTree.render.curStage);
    $(".input").html(displayedTree.inputs[displayedTree.render.curStage]);
  }
  function back() {
    if (!displayedTree) return;

    displayedTree.render.prevStage();
    if (displayedTree.render.curStage <= 0)
      $("#back").addClass("disabled");
    if (displayedTree.render.curStage < displayedTree.render.length - 1)
      $("#forward").removeClass("disabled");

    $("#current").html(displayedTree.render.curStage);
    $(".input").html(displayedTree.inputs[displayedTree.render.curStage]);
  }

  $("#forward").click(forward);
  $("#back").click(back);
  $(document).keydown(function(e) {
    if (document.activeElement.isSameNode(document.getElementById("url"))) return;
    if (e.key === "ArrowLeft") back();
    else if (e.key === "ArrowRight") forward();
  });

  $("#reset").click(resetTree);
  $("#save").click(saveData);
});
