(() => {
  "use strict";
  const core = window.MathCaseActivities;
  const board = document.getElementById("triangle-edges");
  const status = document.getElementById("triangle-status");
  const sample = document.getElementById("triangle-sample");
  const check = document.getElementById("triangle-check");
  if (!core || !board || !status || !sample || !check) return;

  const colors = new Map();
  const buttons = [];
  for (let a = 0; a < 6; a += 1) {
    for (let b = a + 1; b < 6; b += 1) {
      const edge = `${a},${b}`;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "edge-choice";
      button.dataset.a = String(a);
      button.dataset.b = String(b);
      button.dataset.color = "empty";
      button.textContent = `${a + 1}–${b + 1}: choose color`;
      button.setAttribute("aria-pressed", "false");
      button.addEventListener("click", () => {
        const next = button.dataset.color === "empty" ? "red" : button.dataset.color === "red" ? "blue" : "empty";
        setEdge(edge, button, next);
        status.textContent = "Color all 15 edges, then check this one coloring.";
        status.dataset.state = "ready";
      });
      buttons.push({ edge, button, a, b });
      board.append(button);
    }
  }

  function setEdge(edge, button, color) {
    if (color === "empty") colors.delete(edge);
    else colors.set(edge, color);
    button.dataset.color = color;
    button.setAttribute("aria-pressed", color === "empty" ? "false" : "true");
    const a = Number(button.dataset.a) + 1;
    const b = Number(button.dataset.b) + 1;
    button.textContent = `${a}–${b}: ${color === "empty" ? "choose color" : color}`;
    button.setAttribute("aria-label", `Edge ${a} to ${b}: ${color === "empty" ? "not colored" : color}. Click to change color.`);
  }

  sample.addEventListener("click", () => {
    for (const { edge, button, a, b } of buttons) setEdge(edge, button, (a + b) % 2 === 0 ? "red" : "blue");
    status.textContent = "Sample loaded. Now check it or change any edge.";
    status.dataset.state = "ready";
  });

  check.addEventListener("click", () => {
    if (colors.size !== 15) {
      status.textContent = `Color all 15 edges first; ${15 - colors.size} remain.`;
      status.dataset.state = "error";
      return;
    }
    const triangle = core.firstMonochromaticTriangle(6, colors);
    if (!triangle) {
      status.textContent = "No single-color triangle found in this coloring. Recheck the board; every two-coloring of six vertices must contain one.";
      status.dataset.state = "error";
      return;
    }
    const labels = triangle.vertices.map((vertex) => vertex + 1).join(", ");
    status.textContent = `Found a ${triangle.color} triangle on vertices ${labels}. This checks your coloring only.`;
    status.dataset.state = "success";
  });
})();
