"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
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

const visitorIndex = fs.readFileSync(path.join(__dirname, "mathcase", "visitor", "index.html"), "utf8");
const workbench = fs.readFileSync(path.join(__dirname, "mathcase", "visitor", "workbench.js"), "utf8");
assert.match(visitorIndex, /the hosted service did not check your proof/);
assert.match(visitorIndex, /MathCase cannot reconnect that remote worker/);
assert.match(visitorIndex, /href="#local-check"/);
assert.match(visitorIndex, /Reload hosted editor from draft/);
assert.match(workbench, /MathCase cannot see whether the remote worker connected/);
assert.match(workbench, /Edits made only inside the editor must be copied back first/);

console.log("PASS plain-language Lean draft prompt: preserves the claim, surfaces assumptions, and labels output unverified.");
