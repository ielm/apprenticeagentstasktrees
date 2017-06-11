// margin for the SVG
var margin = { top: 50, bottom: 50, left: 75, right: 75 };

// width of the SVG, minus the margins
var width = 1500;
var height = 720;

$(function() {

  // set the default URL to send requests to the service
  if (document.URL.substr(0,4) === "http") 
    $("input[type=text]").val("http://" + document.location.hostname + ":5000/alpha/maketree");

  // set up the link between the file dialog and the masking element
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

  // set up SVG with margins, and add "no tree data" overlay
  d3.select(".treeviz")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("class", "canvas")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
    .append("rect")
      .attr("class", "nodata")
      .attr("fill", "lightgrey")
      .attr("rx", "10px")
      .attr("ry", "10px")
      .attr("width", width)
      .attr("height", height);
  d3.select(".canvas")
    .append("text")
      .attr("class", "nodata")
      .attr("x", width / 2)
      .attr("y", height / 2)
      .attr("text-anchor", "middle")
      .attr("style", "fill: lightcyan; font-size: 18pt; letter-spacing: 0.15em;")
      .text("No tree data");

  d3.selectAll("#current, #total").text("0");
  
  // handle submission of reuests and receipt of responses
  $("#apiquery").submit(function(e) {
    e.preventDefault();

    var file = $("#upload")[0].files[0];
    if (file === undefined) return;

    var reader = new FileReader();
    reader.onload = function() {
      $.post({
        url: $("#url")[0].value, 
        contentType: "application/json",
        data: reader.result,
        dataType: "json",
        success: function(ret, status) {
          var error = status === "success" ? undefined : status;
          changeTree(error, ret);
          d3.selectAll(".control").attr("display", "block");
        }
      });
    };
    reader.readAsText(file);
  });
  
  // Changes the active tree. Fades out any elements currently in the SVG, and
  // sets up the TreeRenderer for the new tree.
  function changeTree(error, parsedData) {
    if (error) throw error;
    console.log(JSON.parse(JSON.stringify(parsedData)));

    var nodes = [];
    parsedData.forEach(function(d) { nodes.push(d.tree); });

    var treeSeq = treeSeqFromData(nodes);
    console.log(treeSeq);

    var remove = d3.selectAll(".canvas").selectAll("*");

    var render = new TreeRenderer(width, height, ".canvas", treeSeq);
    render.transitionDuration = 750;

    d3.select("#total").text(render.length - 1);
    d3.select("#forward").classed("disabled", false);

    var inputs = ["(Before input)"];

    parsedData.forEach(function(stage) {
      if (typeof stage.input === "string")
        inputs.push('"' + stage.input + '"');
      else {
        var append = "";
        stage.input.forEach(function(input, i) {
          if (i > 0)
            append += ", ";
          append += input;
        });
        inputs.push('"' + append + '"');
      }
    });

    console.log(inputs);

    remove
        .attr("opacity", function() {
          return d3.select(this).attr("opacity") || 1;
        })
      .transition()
        .duration(500)
        .ease(d3.easeLinear)
        .attr("opacity", 1e-6)
        .remove();

    d3.timeout(function() {
      render.nextStage();
      d3.select("#current").text(render.curStage);
      d3.select("#back").classed("disabled", false);
      if (render.curStage >= render.length - 1)
        d3.select("#forward").classed("disabled", true);
      d3.select(".control p.input").text(inputs[render.curStage]);
    }, 1000);

    d3.select("#forward").on("click", function() {
      render.nextStage();
      d3.select("#back").classed("disabled", false);
      if (render.curStage >= render.length - 1)
        d3.select("#forward").classed("disabled", true);

      d3.select("#current").text(render.curStage);
      d3.select(".control p.input").text(inputs[render.curStage]);
    });
    d3.select("#back").on("click", function() {
      render.prevStage();
      d3.select("#forward").classed("disabled", false);
      if (render.curStage <= 0)
        d3.select("#back").classed("disabled", true);

      d3.select("#current").text(render.curStage);
      d3.select(".control p.input").text(inputs[render.curStage]);
    });
  }
});
