Object.defineProperty(Array.prototype, "back", {
  __proto__: null,
  get: function() { return this[this.length - 1]; }
});

function setScale(scale, originalString) {
  if (scale instanceof Array)
    var newScale = scale[0] + "," + scale[1];
  else
    var newScale = scale;
  var ret = originalString.replace(/(scale\()([0-9\.,\s]*)(\))/, "$1" + newScale + "$3");
  if (ret === originalString) ret += " scale(" + newScale + ")";
  return ret;
}

function getTranslate(node) {
  var transform = node.attributes.getNamedItem("transform");
  if (!transform) return { x: 0, y: 0 };

  var match = /translate\(\s*(-?[0-9\.]+)\s*,\s*(-?[0-9\.]+)\s*\)/.exec(transform.value);
  if (!match) return { x: 0, y: 0 };

  return { x: +match[1], y: +match[2] };
}

function setTranslate(node, x, y) {
  var transform = node.attributes.getNamedItem("transform");
  var originalString = transform ? transform.value : "";

  if (originalString.indexOf("translate") === -1)
    return originalString + " translate(" + (x? x : 0) + "," + (y? y : 0) + ")";

  if (x === null || x === undefined) {
    var ret = originalString.replace(/(translate\(-?[0-9\.\s]+,)-?[0-9\.\s]+(\))/,
              "$1" + y + "$2");
  }
  else if (y === null || y === undefined) {
    var ret = originalString.replace(/(translate\()-?[0-9\.\s]+(,-?[0-9\.\s]+\))/,
              "$1" + x + "$2");
  }
  else {
    var ret = originalString.replace(/(translate\()[0-9\.\s,\-]+(\))/, "$1" + x + "," + y + "$2");
  }

  return ret;
}
