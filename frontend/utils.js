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
