$(function() {
  
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
          console.log("Returned data:", ret);
          console.log("Status:", status);
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
