(() => {
  "use strict";
  const form = document.getElementById("fraction-form");
  const status = document.getElementById("fraction-status");
  const alternative = document.getElementById("fraction-alternative");
  if (!form || !status || !alternative || !window.MathCaseActivities) return;

  const inputs = ["fraction-x", "fraction-y", "fraction-z"].map((id) => document.getElementById(id));
  function check() {
    const result = window.MathCaseActivities.unitFractionIdentity(...inputs.map((input) => input.value.trim()));
    status.textContent = result.valid
      ? `Exact match: 4/21 = 1/${result.x} + 1/${result.y} + 1/${result.z}. The denominators are positive and increasing.`
      : result.reason;
    status.dataset.state = result.valid ? "success" : "error";
  }
  form.addEventListener("submit", (event) => { event.preventDefault(); check(); });
  alternative.addEventListener("click", () => {
    ["6", "63", "126"].forEach((value, index) => { inputs[index].value = value; });
    check();
  });
})();
