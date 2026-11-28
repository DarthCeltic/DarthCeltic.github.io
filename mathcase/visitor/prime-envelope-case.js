"use strict";

const SOURCE_SHA256 = "2143c9c2e25d2657489284036a7c7b677088131bdeddb66478ed1b3752cfedbb";
const SOURCE_URL = "https://github.com/DarthCeltic/MathCase/blob/main/research/number-theory/egyptian-fractions/prime-envelope-v1/lean/PrimeBand.lean";
const TOOLCHAIN = "Lean 4.33.1 (819816b2e0a3bf405af45ae5c7af2491d8f5bee6)";
const CHECKER_VERSION = "mathcase-prime-envelope-case-v1";
const DRAFT_KEY = "mathcase.visitor.prime-envelope.v1.draft";
const elements = Object.fromEntries(Array.from(document.querySelectorAll("[id]"), node => [node.id, node]));
let lastReceipt = null;

function isPrime(value) {
  if (value < 2) return false;
  if (value % 2 === 0) return value === 2;
  for (let divisor = 3; divisor * divisor <= value; divisor += 2) {
    if (value % divisor === 0) return false;
  }
  return true;
}

function D(b) { return 4 * b * b - 6 * b + 1; }

function canonical(value) {
  const copy = JSON.parse(JSON.stringify(value));
  delete copy.receipt_sha256;
  return JSON.stringify(copy);
}

async function sha256(text) {
  if (!window.crypto?.subtle) throw new Error("This browser cannot calculate a receipt fingerprint.");
  const bytes = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, "0")).join("");
}

function saveDraft() {
  try {
    localStorage.setItem(DRAFT_KEY, JSON.stringify({ p: elements["prime-input"].value, s: elements["offset-input"].value }));
    elements["draft-state"].textContent = "Saved in this browser";
    elements["draft-state"].classList.remove("error");
  } catch {
    elements["draft-state"].textContent = "Could not save this draft";
    elements["draft-state"].classList.add("error");
  }
}

function readNumber(id) {
  const raw = elements[id].value.trim();
  if (!raw || !/^\d+$/.test(raw)) return null;
  const number = Number(raw);
  return Number.isSafeInteger(number) ? number : null;
}

function exactIdentity(p, triple) {
  if (!triple) return false;
  const [x, y, z] = triple.map(BigInt);
  const pp = BigInt(p);
  return x > 0n && x < y && y < z && 4n * x * y * z === pp * (x * y + x * z + y * z);
}

function scopeText(p, B, s) {
  return [
    `p = ${p} is prime and B = ${B} is the first index with D(B) ≥ p.`,
    `The cap is z ≤ (B + s)p = ${(B + s) * p}.`,
    `The theorem-side size conditions are B ≥ 16 and (s + 1)² ≤ B (${(s + 1) ** 2} ≤ ${B}).`
  ];
}

function makeCalculation(p, s) {
  const base = { schema_version: "mathcase-prime-envelope-receipt-v1", checker_version: CHECKER_VERSION, theorem: {
    package: "prime-envelope-v1", declarations: ["MathCase.PrimeBand.classification", "MathCase.PrimeBand.unique_under_cap"],
    source_url: SOURCE_URL, source_sha256: SOURCE_SHA256, toolchain: TOOLCHAIN
  }, input: { p, s } };
  if (!Number.isInteger(p) || p < 43 || p > 1000000) {
    return { ...base, status: "UNSUPPORTED_INPUT", message: "Enter a whole number from 43 through 1,000,000." };
  }
  if (!isPrime(p)) {
    return { ...base, status: "OUT_OF_SCOPE_COMPOSITE", message: `${p} is composite. This class starts with prime denominators.` };
  }
  if (!Number.isInteger(s) || s < 0 || s > 1000) {
    return { ...base, status: "UNSUPPORTED_INPUT", message: "The offset s must be a whole number from 0 through 1,000." };
  }
  let B = 2;
  while (D(B) < p) B += 1;
  const difference = D(B) - p;
  const cap = (B + s) * p;
  const sizeOk = B >= 16 && (s + 1) ** 2 <= B;
  const common = { ...base, computed: { B, D_B: D(B), D_previous: D(B - 1), difference, cap, allowed_offsets: Array.from({ length: s + 1 }, (_, t) => 4 * t * (t + 1)), size_condition: `(s + 1)^2 ≤ B`, size_condition_value: (s + 1) ** 2, size_condition_ok: sizeOk }, scope: scopeText(p, B, s) };
  if (!sizeOk) {
    return { ...common, status: "INCONCLUSIVE_SCOPE", message: "The prime is valid, but the pinned near-minimum theorem does not cover this cap. MathCase will not call this a proof of absence." };
  }
  let hit = null;
  for (let t = 0; t <= s; t += 1) {
    if (difference === 4 * t * (t + 1)) {
      const a = B - t - 1;
      const b = B + t;
      const triple = [a * b, a * p, b * p];
      if (a >= 1 && a < b && exactIdentity(p, triple)) hit = { t, a, b, triple };
    }
  }
  if (hit) return { ...common, status: "CHECKED_WITNESS_UNDER_CAP", message: "The pinned criterion gives one triple under this cap, and the integer identity was checked again in the browser.", hit, claim: `For p = ${p}, the pinned criterion gives the unique triple under z ≤ ${cap}.` };
  return { ...common, status: "PROVED_EXCLUSION_UNDER_CAP", message: "The pinned criterion has no allowed offset through s, so it proves that no triple fits under this cap. A larger denominator may still work.", claim: `For p = ${p}, no triple fits under z ≤ ${cap} under the pinned theorem hypotheses.` };
}

function statusClass(status) {
  if (status === "CHECKED_WITNESS_UNDER_CAP") return "status-witness";
  if (status === "PROVED_EXCLUSION_UNDER_CAP") return "status-exclusion";
  return "status-inconclusive";
}

function renderCalculation(calc, imported = false) {
  const panel = elements["prime-result"];
  panel.className = `prime-result ${statusClass(calc.status)}`;
  panel.replaceChildren();
  const heading = document.createElement("h3");
  heading.textContent = calc.status === "CHECKED_WITNESS_UNDER_CAP" ? "A triple fits under the cap" : calc.status === "PROVED_EXCLUSION_UNDER_CAP" ? "No triple fits under this cap" : calc.status === "OUT_OF_SCOPE_COMPOSITE" ? "This input is composite" : calc.status === "UNSUPPORTED_INPUT" ? "Check the input" : "This cap is outside the theorem";
  panel.append(heading);
  const message = document.createElement("p");
  message.textContent = calc.message;
  panel.append(message);
  if (calc.computed) {
    const list = document.createElement("ul");
    for (const line of calc.scope) { const item = document.createElement("li"); item.textContent = line; list.append(item); }
    if (calc.hit) { const item = document.createElement("li"); item.textContent = `4/${calc.input.p} = 1/${calc.hit.triple[0]} + 1/${calc.hit.triple[1]} + 1/${calc.hit.triple[2]} (t = ${calc.hit.t})`; list.append(item); }
    if (calc.status === "PROVED_EXCLUSION_UNDER_CAP") { const item = document.createElement("li"); item.textContent = `D(B) − p = ${calc.computed.difference}; allowed offsets through s are ${calc.computed.allowed_offsets.join(", ")}.`; list.append(item); }
    panel.append(list);
  }
  elements["download-receipt"].disabled = !calc.computed;
  elements["receipt-status"].textContent = imported ? "Receipt loaded and its fingerprint matches the saved content." : "This is a local arithmetic result. Save it if you want to replay or compare it later.";
  elements["receipt-status"].classList.remove("error");
  panel.focus({ preventScroll: false });
}

async function calculate() {
  const p = readNumber("prime-input");
  const s = readNumber("offset-input");
  saveDraft();
  lastReceipt = makeCalculation(p, s);
  if (lastReceipt.computed) lastReceipt.receipt_sha256 = await sha256(canonical(lastReceipt));
  renderCalculation(lastReceipt);
}

async function downloadReceipt() {
  if (!lastReceipt?.receipt_sha256) return;
  const blob = new Blob([JSON.stringify(lastReceipt, null, 2) + "\n"], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = `mathcase-prime-envelope-${lastReceipt.input.p}-s${lastReceipt.input.s}.json`; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  elements["receipt-status"].textContent = "Saved the compact result receipt. It includes the input, theorem scope, arithmetic result, source hash, and replay link.";
}

async function loadReceipt(file) {
  try {
    const text = await file.text();
    const receipt = JSON.parse(text);
    if (receipt.schema_version !== "mathcase-prime-envelope-receipt-v1" || !receipt.receipt_sha256) throw new Error("This is not a MathCase prime-envelope receipt.");
    const expected = await sha256(canonical(receipt));
    if (expected !== String(receipt.receipt_sha256).toLowerCase()) throw new Error("The receipt fingerprint does not match its contents; it may be altered or incomplete.");
    if (receipt.theorem?.source_sha256 !== SOURCE_SHA256 || receipt.checker_version !== CHECKER_VERSION) throw new Error("This receipt was made by a different checker or theorem source.");
    if (!Number.isInteger(receipt.input?.p) || !Number.isInteger(receipt.input?.s) || !receipt.computed) throw new Error("The receipt is missing its structured input or computed scope.");
    elements["prime-input"].value = receipt.input.p;
    elements["offset-input"].value = receipt.input.s;
    lastReceipt = receipt;
    renderCalculation(receipt, true);
  } catch (error) {
    elements["receipt-status"].textContent = error.message || "The receipt could not be loaded.";
    elements["receipt-status"].classList.add("error");
  }
}

function applyExample(p) { elements["prime-input"].value = p; elements["offset-input"].value = 3; calculate(); }

document.getElementById("prime-form").addEventListener("submit", event => { event.preventDefault(); calculate(); });
document.getElementById("download-receipt").addEventListener("click", downloadReceipt);
document.getElementById("load-receipt").addEventListener("click", () => document.getElementById("receipt-file").click());
document.getElementById("receipt-file").addEventListener("change", event => { const file = event.target.files?.[0]; if (file) loadReceipt(file); event.target.value = ""; });
for (const button of document.querySelectorAll("[data-example]")) button.addEventListener("click", () => applyExample(Number(button.dataset.example)));
for (const input of [document.getElementById("prime-input"), document.getElementById("offset-input")]) input.addEventListener("input", saveDraft);

try {
  const draft = JSON.parse(localStorage.getItem(DRAFT_KEY) || "null");
  if (Number.isInteger(Number(draft?.p))) elements["prime-input"].value = draft.p;
  if (Number.isInteger(Number(draft?.s))) elements["offset-input"].value = draft.s;
} catch { /* Use the visible examples when browser storage is unavailable. */ }
calculate();
