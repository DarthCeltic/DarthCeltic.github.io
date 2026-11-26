(() => {
  "use strict";
  const controls = document.getElementById("step-options");
  const path = document.getElementById("example-path");
  const meaning = document.getElementById("example-meaning");
  const examples = {
    ordinary: ["5 → 16 → 8 → 4", "Three ordinary steps. The first value below 5 is 4."],
    shortcut: ["5 → 8 → 4", "Two shortcuts. The first folds 5 → 16 → 8 into one move. The first value below 5 is 4."],
    odd: ["5 → 1", "One odd-to-odd move. After 5 → 16, halve through 8, 4 and 2 until you reach the next odd number, 1."]
  };

  controls.addEventListener("change", event => {
    const [sequence, explanation] = examples[event.target.value];
    path.textContent = sequence;
    meaning.textContent = explanation;
  });
  document.getElementById("step-fallback").hidden = true;
  controls.hidden = false;
})();
