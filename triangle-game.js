(() => {
  "use strict";

  const graph = document.getElementById("triangle-graph");
  if (!graph) return;

  const lines = document.getElementById("triangle-lines");
  const vertices = document.getElementById("triangle-vertices");
  const highlight = document.getElementById("triangle-highlight");
  const list = document.getElementById("triangle-edges");
  const status = document.getElementById("triangle-status");
  const points = [[91, 28], [229, 28], [289, 125], [229, 222], [91, 222], [31, 125]];
  const colors = new Map();
  const edges = [];
  const nodes = [];
  const svgNamespace = "http://www.w3.org/2000/svg";

  function svg(tag, attributes = {}) {
    const element = document.createElementNS(svgNamespace, tag);
    for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
    return element;
  }

  function announce(message, state = "ready") {
    status.textContent = message;
    status.dataset.state = state;
  }

  function markTriangle(result) {
    highlight.replaceChildren();
    for (const [i, node] of nodes.entries()) node.classList.toggle("found", Boolean(result?.vertices.includes(i)));
    for (const edge of edges) {
      const found = Boolean(result && result.vertices.includes(edge.a) && result.vertices.includes(edge.b));
      edge.button.classList.toggle("found", found);
      edge.button.textContent = edge.label + (found ? " · triangle" : "");
    }
    if (!result) return;
    const coordinates = result.vertices.map(vertex => points[vertex].join(",")).join(" ");
    highlight.append(
      svg("polygon", { points: coordinates, class: "triangle-halo" }),
      svg("polygon", { points: coordinates, class: "triangle-winner", "data-color": result.color })
    );
  }

  function colorEdge(edge, color) {
    colors.set(edge.key, color);
    edge.control.dataset.color = color;
    edge.button.dataset.color = color;
    edge.label = `${edge.a + 1}–${edge.b + 1} · ${color}`;
    edge.button.textContent = edge.label;
    const accessibleName = `Line ${edge.a + 1} to ${edge.b + 1}, ${color}. Switch color.`;
    edge.control.setAttribute("aria-label", accessibleName);
    edge.title.textContent = accessibleName;
  }

  function flip(edge) {
    const next = colors.get(edge.key) === "red" ? "blue" : "red";
    colorEdge(edge, next);
    markTriangle(null);
    const left = edges.length - colors.size;
    announce(left ? `${edge.label}. ${left} ${left === 1 ? "line still needs" : "lines still need"} a color.` : `${edge.label}. Check this coloring to find a triangle.`);
  }

  for (let a = 0; a < points.length; a++) {
    const [x1, y1] = points[a];
    for (let b = a + 1; b < points.length; b++) {
      const [x2, y2] = points[b];
      const coords = { x1, y1, x2, y2 };
      const name = `Line ${a + 1} to ${b + 1}, uncolored. Choose red.`;
      const control = svg("g", { role: "button", tabindex: "0", class: "graph-edge", "data-color": "empty", "aria-label": name });
      const title = svg("title");
      title.textContent = name;
      control.append(title, svg("line", { ...coords, class: "edge-hit" }), svg("line", { ...coords, class: "edge-ink" }));
      const button = document.createElement("button");
      button.type = "button";
      button.className = "edge-choice";
      const edge = { key: `${a},${b}`, a, b, control, title, button, label: `${a + 1}–${b + 1} · uncolored` };
      button.textContent = edge.label;
      button.addEventListener("click", () => flip(edge));
      control.addEventListener("click", () => flip(edge));
      control.addEventListener("keydown", event => {
        if (event.key !== "Enter" && event.key !== " ") return;
        event.preventDefault();
        if (!event.repeat) flip(edge);
      });
      edges.push(edge);
      lines.append(control);
      list.append(button);
    }
    const node = svg("g", { class: "graph-vertex" });
    const label = svg("text", { x: x1, y: y1, dy: ".35em", "text-anchor": "middle" });
    label.textContent = a + 1;
    node.append(svg("circle", { cx: x1, cy: y1, r: 13 }), label);
    vertices.append(node);
    nodes.push(node);
  }

  function loadSample() {
    for (const edge of edges) colorEdge(edge, (edge.a + edge.b) % 2 === 0 ? "red" : "blue");
    markTriangle(null);
    announce("All 15 lines are colored. Change a line or check this coloring.");
  }
  document.getElementById("triangle-sample").addEventListener("click", loadSample);
  document.getElementById("triangle-check").addEventListener("click", () => {
    if (colors.size !== edges.length) {
      const remaining = edges.length - colors.size;
      announce(`Color ${remaining} more ${remaining === 1 ? "line" : "lines"} before checking, or load a sample.`, "error");
      return;
    }
    const result = window.MathCaseActivities.firstMonochromaticTriangle(points.length, colors);
    markTriangle(result);
    if (!result) {
      announce("The checker could not find a triangle in this coloring.", "error");
      return;
    }
    const labels = result.vertices.map(vertex => vertex + 1).join(", ");
    announce(`Found a ${result.color} triangle on dots ${labels}. Its three lines have a double outline. This check covers this coloring only.`, "success");
  });

  if (graph.closest('[data-start-coloring="sample"]')) loadSample();
})();
