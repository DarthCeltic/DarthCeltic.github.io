"use strict";

const assert = require("node:assert/strict");
const { normalizeTeacherCase, teacherCaseImportError } = require("./visitor/classroom-case.js");

const base = {
  id: "example-prime-case",
  title: "Prime case",
  statement: "If a prime divides a square, it divides the number.",
  formal_target: "theorem target : True := by trivial",
  theorem_name: "target",
  source: "theorem target : True := by trivial"
};

for (const schema_version of ["mathcase-visitor-case-v1", "mathcase-visitor-case-v2"]) {
  const normalized = normalizeTeacherCase({ ...base, schema_version, receipt: { ignored: true } });
  assert.equal(normalized.schema_version, schema_version);
  assert.equal(normalized.title, base.title);
  assert.equal(normalized.formal_target, base.formal_target);
  assert.equal(normalized.source, base.source);
  assert.equal(Object.hasOwn(normalized, "receipt"), false);
}

assert.throws(() => normalizeTeacherCase({ ...base, schema_version: "mathcase-class-assignment-v1" }), /unsupported-case-version/);
assert.match(teacherCaseImportError(new Error("unsupported-case-version")), /Save the whole claim.*v1 or v2/);
assert.throws(() => normalizeTeacherCase({ ...base, schema_version: "mathcase-visitor-case-v2", formal_target: " " }), /case-fields/);
assert.match(teacherCaseImportError(new Error("case-fields")), /plain statement or exact Lean target/);
assert.throws(() => normalizeTeacherCase({ ...base, schema_version: "mathcase-visitor-case-v1", source: "x".repeat(2 * 1024 * 1024 + 1) }), /case-field-too-large/);

console.log("PASS classroom case packets: v1/v2 accepted; incompatible, incomplete, and oversized inputs explained.");
