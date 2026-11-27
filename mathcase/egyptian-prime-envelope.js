"use strict";

const primeInput = document.getElementById("envelope-prime");
const sInput = document.getElementById("envelope-s");
const status = document.getElementById("envelope-status");
const result = document.getElementById("envelope-result");

function setStatus(message, error = false) { status.textContent = message; status.classList.toggle("envelope-error", error); }
function isPrime(value) {
  if (value < 2 || value % 2 === 0) return value === 2;
  for (let divisor = 3; divisor * divisor <= value; divisor += 2) if (value % divisor === 0) return false;
  return true;
}
function D(b) { return 4 * b * b - 6 * b + 1; }
function maxBand(B) { return B < 16 ? 0 : Math.floor(Math.sqrt(B)) - 1; }
function checkPrime() {
  result.replaceChildren();
  const p = Number(primeInput.value);
  if (!Number.isInteger(p) || p < 43 || p > 1000000) return setStatus("Enter an integer p from 43 through 1,000,000.", true);
  if (!isPrime(p)) return setStatus(`${p} is composite. The pinned criterion is stated for primes p ≥ 43.`, true);
  let B = 2; while (D(B) < p) B += 1;
  const ceiling = maxBand(B);
  const requested = sInput.value.trim() === "" ? ceiling : Number(sInput.value);
  if (!Number.isInteger(requested) || requested < 0 || requested > ceiling) return setStatus(B < 16 ? `For this p, only s = 0 (the floor cap Bp) is supported because B < 16.` : `For this p, choose an integer s from 0 through ${ceiling}; the theorem requires (s+1)² ≤ B.`, true);
  const cap = (B + requested) * p;
  const diff = D(B) - p;
  let found = null;
  for (let t = 0; t <= requested; t += 1) if (diff === 4 * t * (t + 1)) {
    const a = B - t - 1; const b = B + t;
    found = { t, x: a * b, y: a * p, z: b * p };
  }
  const share = `${location.origin}${location.pathname}?prime=${p}&s=${requested}#prime-envelope-checker`;
  const heading = document.createElement("h4");
  heading.textContent = found ? `Found the unique triple with z ≤ ${cap.toLocaleString()}` : `No triple has z ≤ ${cap.toLocaleString()}`;
  result.append(heading);
  const copy = document.createElement("p");
  copy.textContent = found
    ? `B = ${B}; t = ${found.t}; 4/${p} = 1/${found.x} + 1/${found.y} + 1/${found.z}, with z = ${found.z.toLocaleString()}.`
    : `B = ${B}; D(B) − p = ${diff}. The tested offsets require D(B) − p = 4t(t+1) for some 0 ≤ t ≤ ${requested}; this cap was excluded, but a larger denominator may still work.`;
  result.append(copy);
  const link = document.createElement("a"); link.href = share; link.textContent = "Copyable reproducible link"; link.className = "envelope-link"; result.append(link);
  setStatus(`Checked prime ${p}; numeric cap is z ≤ ${cap.toLocaleString()}.`);
  const query = new URLSearchParams(location.search); if (query.get("prime") !== String(p) || query.get("s") !== String(requested)) history.replaceState(null, "", share);
}
document.getElementById("envelope-check").addEventListener("click", checkPrime);
for (const field of [primeInput, sInput]) field.addEventListener("input", () => { result.replaceChildren(); setStatus("Inputs changed; check again to refresh the result."); });
const params = new URLSearchParams(location.search);
if (params.has("prime")) { primeInput.value = params.get("prime"); if (params.has("s")) sInput.value = params.get("s"); checkPrime(); }
