"use strict";

const primeInput = document.getElementById("envelope-prime");
const slackInput = document.getElementById("envelope-s");
const windowInput = document.getElementById("envelope-window");
const statusLine = document.getElementById("envelope-status");
const result = document.getElementById("envelope-result");

function showStatus(message, error = false) {
  statusLine.textContent = message;
  statusLine.classList.toggle("envelope-error", error);
}

function isPrime(p) {
  for (let divisor = 2; divisor * divisor <= p; divisor += 1) {
    if (p % divisor === 0) return false;
  }
  return true;
}

function upperPolynomial(b) {
  return 4 * b * b - 6 * b + 1;
}

function checkPrime() {
  result.replaceChildren();
  const p = Number(primeInput.value);
  if (!Number.isInteger(p) || p < 43 || p > 1000000) {
    return showStatus("Enter a whole number from 43 through 1,000,000.", true);
  }
  if (!isPrime(p)) return showStatus(`${p} is composite. Choose a prime to use this test.`, true);

  let base = 2;
  while (upperPolynomial(base) < p) base += 1;
  const wide = windowInput.value === "wide";
  let maxSlack = base < 16 ? 0 : Math.floor(Math.sqrt(base)) - 1;
  if (wide && base >= 16) {
    maxSlack = 0;
    while (4 * (base + maxSlack + 1) - 1 < p && upperPolynomial(base + maxSlack + 1) < 2 * p && (maxSlack + 1) * (maxSlack - 2) < 4 * base - 1) maxSlack += 1;
  }
  const slack = slackInput.value === "" ? maxSlack : Number(slackInput.value);
  const slackInvalid = slackInput.validity.badInput || !Number.isInteger(slack) || slack < 0 || (!wide && slack > maxSlack);
  if (slackInvalid) {
    const hint = base < 16
      ? `Here B = ${base}, below 16. Only the lower bound itself (s = 0) can be tested.`
      : `Choose a whole number from 0 through ${maxSlack} so that (s + 1)² ≤ ${base}.`;
    return showStatus(hint, true);
  }
  if (wide) {
    if (base < 16) return showStatus(`The wider window is unavailable because B = ${base}, below 16. Choose the original window with s = 0.`, true);
    const wideChecks = [
      [4 * (base + slack) - 1 < p, `4(B+s) − 1 < p`],
      [upperPolynomial(base + slack) < 2 * p, `D(B+s) < 2p`],
      [slack * (slack - 3) < 4 * base - 1, `s(s−3) < 4B−1`]
    ];
    const failed = wideChecks.find(([ok]) => !ok);
    if (failed) return showStatus(`The wider window is not justified for this input: ${failed[1]} fails at B = ${base}, s = ${slack}.`, true);
  }

  const cap = (base + slack) * p;
  const difference = upperPolynomial(base) - p;
  const t = Math.floor((Math.sqrt(1 + difference) - 1) / 2);
  let found = t <= slack && 4 * t * (t + 1) === difference;
  let triple = null;
  if (found) triple = { t, a: base - t - 1, b: base + t };
  if (wide && !found) {
    for (let candidate = 1; candidate <= slack; candidate += 1) {
      if (4 * candidate * (candidate - 1) - 8 * base + 2 === difference) {
        found = true; triple = { t: candidate, a: base - candidate + 1, b: base + candidate }; break;
      }
    }
  }
  const heading = document.createElement("h4");
  const detail = document.createElement("p");
  if (found) {
    const a = triple.a;
    const b = triple.b;
    heading.textContent = `Exactly one triple has z ≤ ${cap.toLocaleString()}.`;
    detail.textContent = `4/${p} = 1/${a * b} + 1/${a * p} + 1/${b * p}. Its largest denominator is ${(b * p).toLocaleString()} (t = ${triple.t}; ${wide ? "wider criterion" : "original criterion"}).`;
  } else {
    heading.textContent = `No triple has z ≤ ${cap.toLocaleString()}.`;
    detail.textContent = `The difference D(B) − p is ${difference}. None of the allowed offsets 4t(t + 1) equals it for t from 0 through ${slack}. A larger denominator may still work.`;
  }

  const url = new URL(location.pathname, location.origin);
  url.searchParams.set("prime", p);
  url.searchParams.set("s", slack);
  if (wide) url.searchParams.set("window", "wide"); else url.searchParams.delete("window");
  url.hash = "prime-envelope-checker";
  const link = document.createElement("a");
  link.href = url.href;
  link.className = "envelope-link";
  link.textContent = "Link to this calculation";
  result.append(heading, detail, link);
  showStatus(`For p = ${p}, B = ${base} and s = ${slack}. The cap is ${cap.toLocaleString()}.`);
  history.replaceState(null, "", url);
}

function clearCalculation() {
  result.replaceChildren();
  showStatus("Check this prime to see the result for these inputs.");
  const url = new URL(location.href);
  if (url.searchParams.has("prime") || url.searchParams.has("s")) {
    url.searchParams.delete("prime");
    url.searchParams.delete("s");
    url.searchParams.delete("window");
    history.replaceState(null, "", url);
  }
}

document.getElementById("envelope-form").addEventListener("submit", event => {
  event.preventDefault();
  checkPrime();
});
primeInput.addEventListener("input", clearCalculation);
slackInput.addEventListener("input", clearCalculation);
windowInput.addEventListener("change", clearCalculation);

const params = new URLSearchParams(location.search);
if (params.has("prime")) {
  primeInput.value = params.get("prime");
  slackInput.value = params.get("s") ?? "";
  windowInput.value = params.get("window") === "wide" ? "wide" : "original";
  if (params.has("s") && params.get("s") !== "" && slackInput.value === "") {
    showStatus("Enter a whole number for the optional width s.", true);
  } else {
    checkPrime();
  }
}
