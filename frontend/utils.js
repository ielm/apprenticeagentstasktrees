Object.defineProperty(Array.prototype, "back", {
  __proto__: null,
  get: function() { return this[this.length - 1]; }
});
