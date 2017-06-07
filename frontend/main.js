var data = undefined;
var xhr;

$(function() {
  
  var form = document.getElementById("apiquery");

  form.onsubmit = function (e) {
	console.log("Submitted");
    // stop the regular form submission
    e.preventDefault();
  
    // construct an HTTP request
    xhr = new XMLHttpRequest();
    xhr.open("POST", document.getElementById("url").value, true);
    xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  
    //send the selected file
    xhr.send(document.getElementById("upload").files[0]);
  
    xhr.onloadend = function () {
  	  data = this.responseXML;
    };
  };
  
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
