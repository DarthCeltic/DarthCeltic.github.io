(() => {
  "use strict";

  const buttons = document.querySelectorAll("button[data-n]");
  const formula = document.getElementById("formula");
  const verdict = document.getElementById("verdict");

  function showExample(button) {
    const n = Number(button.dataset.n);
    const square = n * n;
    formula.textContent = n + "² = " + square;

    if (square % 4 !== 0) {
      verdict.textContent = "The premise is false for n = " + n + ": 4 does not divide " + square + ".";
    } else if (n % 4 !== 0) {
      verdict.textContent = "Counterexample: 4 divides " + square + ", but 4 does not divide " + n + ".";
    } else {
      verdict.textContent = "The claim holds for this example: 4 divides both " + square + " and " + n + ".";
    }

    for (const choice of buttons) {
      choice.setAttribute("aria-pressed", String(choice === button));
    }
  }

  for (const button of buttons) {
    button.addEventListener("click", () => showExample(button));
  }
})();
