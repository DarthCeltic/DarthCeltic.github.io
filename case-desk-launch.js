/* Static navigation only; no provider or proof execution. */
(() => {
  "use strict";
  const cases = ["hero-composite-counterexample-r1", "hero-prime-divisibility-r1", "hero-sqrt2-parent-reuse-r2"];
  const parts = location.hash.slice(1).split("/");
  const target = new URL("ui/prototype/index.html", location.href);
  if (["case", "item"].includes(parts[0]) && cases.includes(parts[1])) {
    target.hash = parts.length === 2 ? location.hash + "/understand" : location.hash;
  } else target.hash = "#case/hero-composite-counterexample-r1/understand";
  location.replace(target.href);
})();
