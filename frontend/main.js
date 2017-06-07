$(function() {

  d3.selectAll(".control").attr("display", "none");

  d3.select(".treeviz")
      .attr("width", 1200)
      .attr("height", 720)
    .append("rect")
      .attr("fill", "lightgrey")
      .attr("rx", "10px")
      .attr("ry", "10px")
      .attr("width", 1200)
      .attr("height", 720);
  d3.select(".treeviz")
    .append("text")
      .attr("x", 600)
      .attr("y", 360)
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
    console.log(parsedData);
    var treeSeq = treeSeqFromData(parsedData);
    console.log(treeSeq);

    d3.selectAll(".treeviz").selectAll("*")
        .attr("opacity", 1)
      .transition()
        .duration(500)
        .ease(d3.easeLinear)
        .attr("opacity", 1e-6)
        .remove();

    var render = new TreeRenderer(1200, 720, ".treeviz", treeSeq);
    render.transitionDuration = 750;

    d3.select("#current").text(render.curStage);
    d3.select("#total").text(render.length - 1);

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
