(function (root) {
  "use strict";

  function buildFormalizationPrompt(item) {
    if (!item || typeof item !== "object" || typeof item.statement !== "string" || !item.statement.trim()) {
      throw new Error("claim-required");
    }
    const title = typeof item.title === "string" && item.title.trim() ? item.title : "Untitled claim";
    const source = typeof item.source === "string" && item.source.trim() ? item.source : "[No Lean source supplied yet.]";
    return [
      "Draft a Lean 4 formalization and, if possible, proof from the plain-language claim below. This is a proposal, not a verified translation.",
      "Do not silently change the claim or invent assumptions. If a phrase is ambiguous, first ask a clarification instead of guessing. List every assumption you use.",
      "Return these sections in order: (1) a plain-English restatement of the exact proposition and its assumptions, (2) the exact Lean proposition and suggested theorem name, (3) a complete Lean source file that proves exactly that proposition if you can. If you cannot prove it, say so and do not use sorry, admit, or new axioms.",
      "Explain how each important part of the English claim maps to the Lean proposition. Do not say they are equivalent unless you justify that mapping.",
      "Prefer Lean 4.33.1 syntax for MathCase's pinned local checker. Use Mathlib only when needed and list the imports. A hosted editor may use a different version.",
      "Case title:\n" + title,
      "Plain-language claim:\n" + item.statement,
      "Current Lean source, if any:\n" + source,
      "The returned code is only a draft. A human must compare the English, assumptions, and exact Lean target; then Lean must check the proof."
    ].join("\n\n");
  }

  const api = { buildFormalizationPrompt };
  root.MathCaseLeanDraft = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window === "undefined" ? globalThis : window);
