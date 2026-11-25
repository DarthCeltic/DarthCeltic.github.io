"use strict";

const assert = require("node:assert/strict");
const { buildFormalizationPrompt } = require("./visitor/lean-draft.js");

const claim = "For every natural number n, adding zero leaves n unchanged.";
const prompt = buildFormalizationPrompt({
  title: "Add zero",
  statement: claim,
  source: ""
});

assert.match(prompt, /proposal, not a verified translation/);
assert.match(prompt, /ask a clarification instead of guessing/);
assert.match(prompt, /List every assumption/);
assert.match(prompt, /plain-English restatement/);
assert.match(prompt, /exact Lean proposition/);
assert.match(prompt, /For every natural number n, adding zero leaves n unchanged/);
assert.match(prompt, /do not use sorry, admit, or new axioms/);
assert.throws(() => buildFormalizationPrompt({ statement: " " }), /claim-required/);

console.log("PASS plain-language Lean draft prompt: preserves the claim, surfaces assumptions, and labels output unverified.");
