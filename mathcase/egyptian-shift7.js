(function () {
  "use strict";

  const form = document.getElementById("shift7-form");
  const input = document.getElementById("shift7-parameter");
  const status = document.getElementById("shift7-status");
  const result = document.getElementById("shift7-result");
  if (!form || !input || !status || !result) return;

  function showError(message) {
    status.dataset.state = "error";
    status.textContent = message;
    result.replaceChildren();
  }

  function addLine(card, label, value) {
    const paragraph = document.createElement("p");
    const strong = document.createElement("strong");
    strong.textContent = label + ": ";
    paragraph.append(strong, document.createTextNode(value));
    card.appendChild(paragraph);
  }

  function checkMember(parameterText) {
    if (!/^\d{1,36}$/.test(parameterText)) {
      showError("Enter a nonnegative whole number with at most 36 digits.");
      return;
    }

    const t = BigInt(parameterText);
    const n = 433n + 840n * t;
    const aNumerator = n * (n + 7n);
    const xNumerator = n + 7n;
    if (aNumerator % 4n !== 0n || xNumerator % 4n !== 0n) {
      showError("The displayed progression did not produce integer formulas.");
      return;
    }

    const a = aNumerator / 4n;
    const x = xNumerator / 4n;
    if (a % 5n !== 0n || (a + 5n) % 7n !== 0n || (a * (a + 5n)) % 35n !== 0n) {
      showError("The displayed progression did not produce integer denominators.");
      return;
    }

    const y = (a + 5n) / 7n;
    const z = (a * (a + 5n)) / 35n;
    const ordered = 0n < x && x < y && y < z;
    const left = 4n * x * y * z;
    const right = n * (x * y + x * z + y * z);
    const exact = left === right;
    if (!ordered || !exact) {
      showError("The exact identity or denominator-order check failed for this input.");
      return;
    }

    const card = document.createElement("div");
    card.className = "coefficient-result-card";
    const heading = document.createElement("h3");
    heading.textContent = "This member checks exactly";
    card.appendChild(heading);
    addLine(card, "t", t.toString());
    addLine(card, "n", n.toString());
    addLine(card, "x", x.toString());
    addLine(card, "y", y.toString());
    addLine(card, "z", z.toString());
    addLine(card, "Denominator order", "0 < x < y < z");
    addLine(card, "Integer check", "4xyz = n(xy + xz + yz)");
    addLine(card, "Result", "PASS — 4/n = 1/x + 1/y + 1/z");
    result.replaceChildren(card);
    status.dataset.state = "success";
    status.textContent = "Exact BigInt check passed for t = " + t.toString() + ".";
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    checkMember(input.value.trim());
  });
})();
