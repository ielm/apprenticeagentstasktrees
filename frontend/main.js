var margin = { top: 50, bottom: 50, left: 75, right: 75 };
var width = 1500;
var height = 720;

$(function() {

  d3.select(".treeviz")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("class", "canvas")
      .attr("transform", "translate(" + margin.top + "," + margin.left + ")")
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
  
  //d3.json("output.json", function(error, parsedData) {
  function changeTree(error, parsedData) {
    if (error) throw error;
    console.log(JSON.parse(JSON.stringify(parsedData)));
    var treeSeq = treeSeqFromData(parsedData);
    console.log(treeSeq);

    var remove = d3.selectAll(".canvas").selectAll("*");

    var render = new TreeRenderer(width, height, ".canvas", treeSeq);
    render.transitionDuration = 750;

    d3.select("#total").text(render.length - 1);
    d3.select("#forward").classed("disabled", false);

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
    }, 1000);

    d3.select("#forward").on("click", function() {
      render.nextStage();
      d3.select("#back").classed("disabled", false);
      if (render.curStage >= render.length - 1)
        d3.select("#forward").classed("disabled", true);

      d3.select("#current").text(render.curStage);
    });
    d3.select("#back").on("click", function() {
      render.prevStage();
      d3.select("#forward").classed("disabled", false);
      if (render.curStage <= 0)
        d3.select("#back").classed("disabled", true);

      d3.select("#current").text(render.curStage);
    });
  }
});
