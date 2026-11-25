"use strict";

const assert = require("node:assert/strict");
const { normalizeTeacherCase, teacherCaseImportError, packetImportError, learnerFeedbackMatches } = require("./visitor/classroom-case.js");

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
const wrongPacket = new Error("wrong-schema");
wrongPacket.actualSchema = "mathcase-class-assignment-v1";
assert.match(packetImportError(wrongPacket, "learner submission", "mathcase-class-submission-v1", "Choose the learner's saved file."), /Wrong file type.*mathcase-class-assignment-v1.*learner submission/);
assert.match(packetImportError(new Error("shape"), "learner submission", "mathcase-class-submission-v1", "Re-export the submission."), /required fields are missing or invalid/);
assert.match(packetImportError(new Error("hash"), "assignment", "mathcase-class-assignment-v1", "Choose the teacher export."), /target hash does not match its Lean statement/);
assert.throws(() => normalizeTeacherCase({ ...base, schema_version: "mathcase-visitor-case-v2", formal_target: " " }), /case-fields/);
assert.match(teacherCaseImportError(new Error("case-fields")), /plain statement or exact Lean target/);
assert.throws(() => normalizeTeacherCase({ ...base, schema_version: "mathcase-visitor-case-v1", source: "x".repeat(2 * 1024 * 1024 + 1) }), /case-field-too-large/);

const submission = {
  schema_version: "mathcase-class-submission-v1",
  submission_id: "submission-1",
  assignment_id: "assignment-1",
  lean_statement_sha256: "a".repeat(64)
};
const review = {
  schema_version: "mathcase-class-review-v1",
  submission_id: "submission-1",
  assignment_id: "assignment-1",
  lean_statement_sha256: "a".repeat(64),
  submission_file_sha256: "b".repeat(64)
};
assert.equal(learnerFeedbackMatches(submission, review, "b".repeat(64)), true, "matching review opens beside its original submission");
assert.equal(learnerFeedbackMatches(submission, { ...review, submission_id: "submission-2" }, "b".repeat(64)), false, "review for another submission is rejected");
assert.equal(learnerFeedbackMatches(submission, review, "c".repeat(64)), false, "changed submission bytes are rejected");
assert.equal(learnerFeedbackMatches(submission, { ...review, assignment_id: "assignment-2" }, "b".repeat(64)), false, "review for another assignment is rejected");

console.log("PASS classroom case packets: v1/v2 accepted; invalid packets rejected; feedback requires the exact submission and assignment.");
