"use strict";
const assert = require("node:assert/strict");
const { firstMonochromaticTriangle, unitFractionIdentity } = require("./activities-core.js");

function completeColors(colorFor) {
  const colors = new Map();
  for (let a = 0; a < 6; a += 1) for (let b = a + 1; b < 6; b += 1) colors.set(`${a},${b}`, colorFor(a, b));
  return colors;
}

const sample = completeColors((a, b) => (a + b) % 2 === 0 ? "red" : "blue");
assert.deepEqual(firstMonochromaticTriangle(6, sample), { vertices: [0, 2, 4], color: "red" });

const noTriangleOnFive = new Map();
for (let a = 0; a < 5; a += 1) for (let b = a + 1; b < 5; b += 1) noTriangleOnFive.set(`${a},${b}`, ((b - a) % 5 === 1 || (b - a) % 5 === 4) ? "red" : "blue");
assert.equal(firstMonochromaticTriangle(5, noTriangleOnFive), null);

assert.deepEqual(unitFractionIdentity("7", "22", "462"), { valid: true, x: "7", y: "22", z: "462" });
assert.deepEqual(unitFractionIdentity("6", "63", "126"), { valid: true, x: "6", y: "63", z: "126" });
assert.equal(unitFractionIdentity("7", "22", "461").valid, false);
assert.equal(unitFractionIdentity("22", "7", "462").valid, false);
assert.equal(unitFractionIdentity("0", "22", "462").valid, false);
process.stdout.write("PASS activity core: K6 triangle detection and exact 4/21 identities\n");
