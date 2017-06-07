$(function() {
  d3.json("output.json", function(error, parsedData) {
    if (error) throw error;
    var treeSeq = treeSeqFromData(parsedData);
    console.log(treeSeq);

    var render = new TreeRenderer(1200, 720, ".treeviz", treeSeq);

    d3.select("#current").text(render.curStage + 1);
    d3.select("#total").text(render.length);

    d3.select("#forward").on("click", function() {
      render.nextStage();
      d3.select("#back").classed("disabled", false);
      if (render.curStage >= render.length - 1)
        d3.select("#forward").classed("disabled", true);

      d3.select("#current").text(render.curStage + 1);
    });
    d3.select("#back").on("click", function() {
      render.prevStage();
      d3.select("#forward").classed("disabled", false);
      if (render.curStage <= 0)
        d3.select("#back").classed("disabled", true);

      d3.select("#current").text(render.curStage + 1);
    });
  });
});
