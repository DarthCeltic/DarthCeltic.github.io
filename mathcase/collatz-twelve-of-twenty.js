(() => {
  "use strict";

  const form = document.getElementById("twelve-form");
  if (!form) return;
  const field = document.getElementById("twelve-start");
  const result = document.getElementById("twelve-result");

  function calculate() {
    const digits = field.value.trim();
    if (!/^[0-9]{1,120}$/.test(digits) || BigInt(digits) === 0n) {
      field.setAttribute("aria-invalid", "true");
      result.textContent = "Enter a positive whole number of up to 120 digits.";
      return;
    }
    field.removeAttribute("aria-invalid");

    const start = BigInt(digits);
    let accelerated = start;
    let oddInputs = 0;
    for (let step = 0; step < 20; step++) {
      if (accelerated % 2n === 1n) {
        oddInputs++;
        accelerated = (3n * accelerated + 1n) / 2n;
      } else {
        accelerated /= 2n;
      }
    }

    let ordinary = start;
    for (let step = 0; step < 32; step++) {
      ordinary = ordinary % 2n === 0n ? ordinary / 2n : 3n * ordinary + 1n;
    }

    const applies = oddInputs === 12 ? "The rule applies." : "This start falls outside the rule.";
    let comparison = "equal to";
    if (ordinary < start) comparison = "below";
    if (ordinary > start) comparison = "above";
    result.textContent = `${oddInputs} of the 20 inputs were odd. ${applies} After 32 ordinary steps the value is ${ordinary}, ${comparison} the start (${start}).`;
  }

  field.addEventListener("input", () => {
    field.removeAttribute("aria-invalid");
    result.textContent = "";
  });
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    calculate();
  });
  calculate();
})();
