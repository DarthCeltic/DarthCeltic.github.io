(function (root) {
  "use strict";

  function firstMonochromaticTriangle(vertexCount, edgeColors) {
    for (let a = 0; a < vertexCount - 2; a += 1) {
      for (let b = a + 1; b < vertexCount - 1; b += 1) {
        for (let c = b + 1; c < vertexCount; c += 1) {
          const ab = edgeColors.get(`${a},${b}`);
          const ac = edgeColors.get(`${a},${c}`);
          const bc = edgeColors.get(`${b},${c}`);
          if (ab && ab === ac && ac === bc) return { vertices: [a, b, c], color: ab };
        }
      }
    }
    return null;
  }

  function unitFractionIdentity(xText, yText, zText) {
    if (![xText, yText, zText].every((part) => /^\d{1,100}$/.test(part))) {
      return { valid: false, reason: "Enter three positive whole-number denominators." };
    }
    const x = BigInt(xText);
    const y = BigInt(yText);
    const z = BigInt(zText);
    if (!(0n < x && x < y && y < z)) {
      return { valid: false, reason: "Use positive denominators in increasing order." };
    }
    const matches = 4n * x * y * z === 21n * (x * y + x * z + y * z);
    return matches
      ? { valid: true, x: x.toString(), y: y.toString(), z: z.toString() }
      : { valid: false, reason: "These three fractions do not add to 4/21." };
  }

  const api = { firstMonochromaticTriangle, unitFractionIdentity };
  root.MathCaseActivities = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(globalThis);
