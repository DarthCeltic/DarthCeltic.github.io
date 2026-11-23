"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");

const script = fs.readFileSync(path.join(__dirname, "collatz-twelve-of-twenty.js"), "utf8");
function mount(value) {
  const listeners = {};
  const attrs = new Map();
  const form = { addEventListener(name, fn) { listeners[name] = fn; } };
  const field = {
    value,
    addEventListener(name, fn) { listeners[name] = fn; },
    setAttribute(key, val) { attrs.set(key, val); },
    removeAttribute(key) { attrs.delete(key); }
  };
  const result = { textContent: "" };
  const elements = { "twelve-form": form, "twelve-start": field, "twelve-result": result };
  vm.runInNewContext(script, { document: { getElementById(id) { return elements[id]; } } });
  return { field, result, listeners, attrs };
}

// Group ordinary steps into accelerated steps; save the ordinary endpoint mid-walk if necessary.
function reference(start) {
  let value = BigInt(start), odd = 0, updates = 0, endpoint;
  function step() {
    value = value % 2n ? 3n * value + 1n : value / 2n;
    if (++updates === 32) endpoint = value;
  }
  for (let i = 0; i < 20; i++) {
    if (value % 2n) { odd++; step(); }
    step();
  }
  while (updates < 32) step();
  return { odd, endpoint };
}

test("example and keyboard form path give scoped results", () => {
  const {field,result,listeners} = mount("239");
  assert.equal(result.textContent, "12 of the 20 inputs were odd. The rule applies. After 32 ordinary steps the value is 122, below the start (239).");
  field.value = "27";
  listeners.input();
  assert.equal(result.textContent, "");
  let prevented = false;
  listeners.submit({ preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  assert.equal(result.textContent, "15 of the 20 inputs were odd. This start falls outside the rule. After 32 ordinary steps the value is 526, above the start (27).");
  assert.match(mount("1024").result.textContent, /falls outside the rule.*below the start/);
});

test("predictions agree with an independent grouped ordinary-step walk", () => {
  const largeQualifying = (10n ** 110n) * (2n ** 20n) + 239n;
  for (const start of [1n,2n,27n,171n,239n,1024n,9007199254740993n,largeQualifying,10n ** 119n,10n ** 120n - 1n]) {
    const {odd,endpoint} = reference(start);
    const output = mount(start.toString()).result.textContent;
    assert.ok(output.startsWith(`${odd} of the 20 inputs were odd.`));
    assert.ok(output.includes(`value is ${endpoint},`));
    assert.equal(output.includes("The rule applies."), odd === 12);
    if (odd === 12) assert.ok(endpoint < start);
  }
});

test("rejects invalid or overlong input and clears the error when edited", () => {
  for (const bad of ["", "0", "0000", "-1", "+239", "1.5", "0x10", "4e2", "9".repeat(121)]) {
    const { attrs, result, listeners } = mount(bad);
    assert.equal(attrs.get("aria-invalid"), "true");
    assert.match(result.textContent, /Enter a positive whole number/);
    listeners.input();
    assert.equal(attrs.has("aria-invalid"), false);
    assert.equal(result.textContent, "");
  }
});
