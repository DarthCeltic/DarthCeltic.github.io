/* Keep the legacy /saved-demo/ alias and forward its query and case fragment. */
(() => {
  "use strict";
  const target = new URL("../reader.html", window.location.href);
  target.search = window.location.search;
  target.hash = window.location.hash;
  window.location.replace(target.href);
})();
