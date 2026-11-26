const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "../mathcase");
const html = fs.readFileSync(path.join(root, "visitor/index.html"), "utf8");
const js = fs.readFileSync(path.join(root, "visitor/workbench.js"), "utf8");
const css = fs.readFileSync(path.join(root, "visitor/workbench.css"), "utf8");

test("the proof editor stays embedded and offers a same-draft recovery tab", () => {
  assert.match(html, /<section id="live-panel"[^>]*hidden/);
  assert.match(html, /id="run-lean"[^>]*>Open Lean editor below/);
  assert.match(html, /id="retry-lean"[^>]*>Reload from this draft/);
  assert.match(html, /id="open-lean-tab"[^>]*>Open this draft in a new tab/);
  assert.match(html, /id="live-connection-status"[^>]*aria-live="polite"/);
  assert.match(html, /The online editor’s output is not saved here/);
  assert.match(html, /import a receipt from the local check to record the result/);
  assert.match(js, /frame\.src = editorUrl\(\)/);
  assert.match(js, /elements\["retry-lean"\][\s\S]*?loadEditor\("Reloading the online editor from the code currently in this workbench…"\)/);
  assert.match(js, /elements\["open-lean-tab"\]\.addEventListener\("click", \(\) => \{\s*window\.open\(editorUrl\(\), "_blank", "noopener,noreferrer"\);\s*\}\)/);
  assert.match(css, /\.live-head \.run-actions\s*\{[^}]*width:\s*100%;[^}]*max-width:\s*100%;[^}]*\}/);
});

test("the error advice offers recovery without claiming to read the hosted editor state", () => {
  assert.match(html, /“No connection to Lean”/);
  assert.match(html, /“Updating…” does not finish/);
  assert.match(html, /Lean has not checked your proof/);
  assert.match(html, /try the pinned local check below/);
  assert.doesNotMatch(js, /contentWindow\.document/);
});
