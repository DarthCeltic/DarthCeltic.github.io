"use strict";

const legacyMathCaseSections = new Set([
  "#try-math", "#puzzle-title", "#triangle-help", "#triangle-graph",
  "#triangle-lines", "#triangle-highlight", "#triangle-vertices",
  "#triangle-check", "#triangle-sample", "#triangle-status", "#triangle-edges",
  "#case-desk", "#desk-title", "#proof-story", "#proof-title", "#latest-title",
  "#browse-title", "#your-workspace", "#workspace-title", "#hero-title"
]);
const destination = document.getElementById("moved-page");
const isPortfolio = location.pathname === "/" || location.pathname === "/index.html";
const isMathCaseLink = location.hash.startsWith("#case/") ||
  legacyMathCaseSections.has(location.hash) ||
  new URLSearchParams(location.search).get("scope") === "public";

if (destination || (isPortfolio && isMathCaseLink)) {
  const target = new URL(destination ? destination.href : "/mathcase/", location.href);
  target.search = location.search;
  target.hash = location.hash;
  location.replace(target.href);
}
