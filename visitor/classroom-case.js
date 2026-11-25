(function (root) {
  "use strict";

  const isText = (value) => typeof value === "string";
  const supportedVersions = new Set(["mathcase-visitor-case-v1", "mathcase-visitor-case-v2"]);

  function normalizeTeacherCase(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("not-case-object");
    if (!supportedVersions.has(value.schema_version)) throw new Error("unsupported-case-version");
    if (![value.title, value.statement, value.formal_target, value.source].every(isText)) throw new Error("case-fields");
    if (!value.title.trim() || !value.statement.trim() || !value.formal_target.trim()) throw new Error("case-fields");
    if (value.title.length > 400 || value.statement.length > 40000 || value.formal_target.length > 40000 ||
        value.source.length > 2 * 1024 * 1024) throw new Error("case-field-too-large");
    return {
      schema_version: value.schema_version,
      id: isText(value.id) ? value.id : "",
      title: value.title,
      statement: value.statement,
      formal_target: value.formal_target,
      theorem_name: isText(value.theorem_name) ? value.theorem_name : "",
      source: value.source
    };
  }

  function teacherCaseImportError(error) {
    if (error?.message === "file-too-large") return "This file is over the 4 MiB limit. Export a smaller case packet.";
    if (error?.message === "unsupported-case-version") return "This is not a saved case packet. Choose a file exported with “Save the whole claim” (v1 or v2).";
    if (error?.message === "case-fields") return "This case is missing its plain statement or exact Lean target. Re-export the full claim from the workbench.";
    if (error?.message === "case-field-too-large") return "A case field is too large to import. Shorten it in the workbench and export again.";
    if (error instanceof SyntaxError || error?.name === "TypeError") return "This file is not valid UTF-8 JSON. Export the case again from the workbench.";
    return "Could not read this case file. Choose a MathCase “Save the whole claim” JSON export.";
  }

  function packetImportError(error, expectedLabel, expectedSchema, nextAction) {
    if (error?.message === "file-too-large") return "This file is over the 4 MiB limit. Choose a smaller classroom packet.";
    if (error instanceof SyntaxError || error?.name === "TypeError") return "This file is not valid JSON. Re-download the classroom packet and try again.";
    if (error?.message === "hash") return "The assignment’s target hash does not match its Lean statement. Ask the teacher to export the assignment again.";
    if (error?.message === "wrong-schema") {
      const actual = typeof error.actualSchema === "string" && error.actualSchema ? ` It is labeled “${error.actualSchema}”.` : " It has no recognized MathCase packet label.";
      return `Wrong file type for this step.${actual} This step needs a ${expectedLabel} (${expectedSchema}). ${nextAction}`;
    }
    if (error?.message === "shape") return `This file is labeled as a ${expectedLabel}, but required fields are missing or invalid. ${nextAction}`;
    return `Could not read a valid ${expectedLabel} file (${expectedSchema}). ${nextAction}`;
  }

  function learnerFeedbackMatches(submission, review, submissionSha256) {
    return !!submission && !!review &&
      review.schema_version === "mathcase-class-review-v1" &&
      submission.schema_version === "mathcase-class-submission-v1" &&
      review.submission_id === submission.submission_id &&
      review.assignment_id === submission.assignment_id &&
      review.lean_statement_sha256 === submission.lean_statement_sha256 &&
      review.submission_file_sha256 === submissionSha256;
  }

  const api = { normalizeTeacherCase, teacherCaseImportError, packetImportError, learnerFeedbackMatches };
  root.MathCaseClassroomCase = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window === "undefined" ? globalThis : window);
