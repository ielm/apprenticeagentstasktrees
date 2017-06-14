Object.defineProperty(Array.prototype, "back", {
  __proto__: null,
  get: function() { return this[this.length - 1]; }
});

function setScale(scale, originalString) {
  var ret = originalString.replace(/(scale\()([0-9\.,\s]*)(\))/, "$1" + scale + "$3");
  if (ret === originalString) ret += " scale(" + scale + ")";
  return ret;
}
