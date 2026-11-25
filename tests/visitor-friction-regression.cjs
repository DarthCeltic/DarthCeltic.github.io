const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const classroomJS = fs.readFileSync(path.join(root, "visitor/classroom.js"), "utf8");
const classroomCSS = fs.readFileSync(path.join(root, "visitor/tools.css"), "utf8");
const triangleJS = fs.readFileSync(path.join(root, "triangle-game.js"), "utf8");

test("populated classroom SHA-256 fingerprints stay inside a 390px layout", () => {
  const digest = "a".repeat(64);
  const viewport = 390;
  const pageGutters = 24;
  const cardPadding = 32;
  const estimatedMonospaceColumns = Math.floor((viewport - pageGutters - cardPadding) / 8);

  assert.equal(digest.length, 64);
  assert.ok(digest.length > estimatedMonospaceColumns);
  assert.match(classroomJS, /function addFingerprintDisclosure\(parent, summaryText, value\)/);
  assert.match(classroomJS, /addFingerprintDisclosure\(brief, "Show the exact statement fingerprint", value\.lean_statement_sha256\)/);
  assert.match(classroomJS, /addFingerprintDisclosure\(panel, "Show the exact statement fingerprint", targetDigest\)/);
  assert.match(classroomCSS, /\.fingerprint-value\s*\{[^}]*overflow-wrap:\s*anywhere;[^}]*\}/s);
  assert.match(classroomCSS, /\.assignment-brief,\s*#review-content\s*\{[^}]*min-width:\s*0;[^}]*\}/s);
});

test("the triangle result stays on the coloring the visitor just checked", () => {
  assert.match(triangleJS, /This checks this coloring only/);
  assert.doesNotMatch(triangleJS, /saved AI proof mistake on a different problem/);
  assert.doesNotMatch(triangleJS, /triangle-case-story|status\.after\(story\)/);
});
