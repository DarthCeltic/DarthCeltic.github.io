"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");
const root = path.resolve(__dirname, "../mathcase");

class NodeStub {
  constructor(tag) { this.tag = tag; this.children = []; this.attributes = {}; this.style = {}; this.classList = { add() {} }; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = []; this.append(...nodes); }
  setAttribute(name, value) { this.attributes[name] = value; }
  addEventListener() {}
}
function descendantsText(node) {
  return [node.textContent || "", ...(node.children || []).map(descendantsText)].join(" ");
}
function findNode(node, predicate) {
  if (predicate(node)) return node;
  for (const child of node.children || []) { const found = findNode(child, predicate); if (found) return found; }
  return null;
}
function loadReader(hash) {
  const nodes = Object.fromEntries(["case-nav", "case-stage", "tavily-panel", "tavily-body"].map(id => [id, new NodeStub(id)]));
  const replaced = [];
  const location = { hash, replace(target) { replaced.push(target); } };
  const window = {};
  const context = {
    window, location, history: { replaceState() {} },
    document: { getElementById(id) { return nodes[id]; }, createElement(tag) { return new NodeStub(tag); } },
    addEventListener() {}, fetch: async () => { throw new Error("offline test"); }, URL, TextDecoder,
    crypto: require("node:crypto").webcrypto,
  };
  vm.runInNewContext(fs.readFileSync(path.join(root, "saved-demo/public-reader-data.js"), "utf8"), context);
  vm.runInNewContext(fs.readFileSync(path.join(root, "app.js"), "utf8"), context);
  return { nodes, replaced };
}
function loadRouteScript(file, href) {
  const replaced = [];
  const url = new URL(href);
  const location = { href, hash: url.hash, search: url.search, replace(target) { replaced.push(target); } };
  const window = { location };
  const context = { window, document: { querySelectorAll() { return []; } }, URL, decodeURIComponent };
  vm.runInNewContext(fs.readFileSync(path.join(root, file), "utf8"), context);
  return replaced;
}

test("prime and composite saved IDs accept understand and historical run suffixes", () => {
  const prime = loadReader("#case/hero-prime-divisibility-r1/understand");
  assert.deepEqual(prime.replaced, []);
  assert.ok(prime.nodes["case-nav"].children.some(node => node.attributes["aria-current"] === "page"));
  const composite = loadReader("#case/hero-composite-counterexample-r1/run/hero-composite-counterexample-r1-exact-arithmetic");
  assert.deepEqual(composite.replaced, []);
  assert.match(descendantsText(composite.nodes["case-stage"]), /Try an exact integer example/);
});

test("legacy square-root child routes to its actual public case", () => {
  const reader = loadReader("#case/hero-sqrt2-parent-reuse-r2/understand");
  assert.deepEqual(reader.replaced, ["/mathcase/cases.html#sqrt2-child"]);
  assert.deepEqual(loadRouteScript("case-desk-launch.js", "https://darthceltic.github.io/mathcase/#case/hero-sqrt2-parent-reuse-r2/understand"), ["https://darthceltic.github.io/mathcase/cases.html#sqrt2-child"]);
});

test("unknown IDs show a missing-case message and catalog link", () => {
  const { nodes } = loadReader("#case/not-a-public-case");
  const text = descendantsText(nodes["case-stage"]);
  assert.match(text, /This saved case is not available/);
  assert.match(text, /No public case matches/);
  assert.ok(findNode(nodes["case-stage"], child => child.href === "/mathcase/cases.html"));
  assert.doesNotMatch(text, /Try an exact integer example/);
});

test("root shared case links and the saved-demo alias preserve the requested route", () => {
  const rootLink = loadRouteScript("case-desk-launch.js", "https://darthceltic.github.io/mathcase/#case/hero-prime-divisibility-r1/run/run-17");
  assert.deepEqual(rootLink, ["https://darthceltic.github.io/mathcase/reader.html?scope=public#case/hero-prime-divisibility-r1/run/run-17"]);
  const alias = loadRouteScript("saved-demo-redirect.js", "https://darthceltic.github.io/mathcase/saved-demo/?scope=public#case/hero-composite-counterexample-r1/understand");
  assert.deepEqual(alias, ["https://darthceltic.github.io/mathcase/reader.html?scope=public#case/hero-composite-counterexample-r1/understand"]);
});

function loadLegacyRoute(href, destination) {
  const replaced = [];
  const location = new URL(href);
  location.replace = target => replaced.push(target);
  const document = {
    getElementById(id) {
      assert.equal(id, "moved-page");
      return destination ? { href: destination } : null;
    }
  };
  const script = fs.readFileSync(path.join(root, "../legacy-route.js"), "utf8");
  vm.runInNewContext(script, { document, location, URL, URLSearchParams });
  return replaced;
}

test("old MathCase links retain their query and fragment on the project site", () => {
  const base = "https://darthceltic.github.io";
  const caseLink = "/?scope=public#case/hero-prime-divisibility-r1/run/run-17";
  assert.deepEqual(loadLegacyRoute(base + caseLink), [base + "/mathcase" + caseLink]);
  assert.deepEqual(loadLegacyRoute(base + "/work.html#collatz-23-of-14", base + "/mathcase/work.html"),
    [base + "/mathcase/work.html#collatz-23-of-14"]);
  assert.deepEqual(loadLegacyRoute(base + "/visitor/?starter=counterexample#case-title", base + "/mathcase/visitor/"),
    [base + "/mathcase/visitor/?starter=counterexample#case-title"]);
});

test("the portfolio root and its section links stay on the portfolio", () => {
  const base = "https://darthceltic.github.io";
  for (const url of ["/", "/#contact", "/index.html#projects"]) {
    assert.deepEqual(loadLegacyRoute(base + url), []);
  }
  assert.deepEqual(loadLegacyRoute(base + "/projects/#contributions", base + "/"),
    [base + "/#contributions"]);
});
