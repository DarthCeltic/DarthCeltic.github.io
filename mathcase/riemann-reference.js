// Compare four small public source records in the visitor's browser.
(() => {
  "use strict";

  const upstream = "https://raw.githubusercontent.com/leanprover-community/";
  const pins = [
    { name: "Mathlib's definition", path: "mathlib4/0df444a360eaa60ab8c11dca51a86af692955474/Mathlib/NumberTheory/LSeries/RiemannZeta.lean", size: 12306, hash: "db9f37f08bcce379c502549f604c0e98bf4a39b3a3440606861bbac847f2a1a9" },
    { name: "Independent challenge", path: "riemann-hypothesis/0df13c6021f92a746687929a26f1b6dc286aef09/src/Challenge.lean", size: 1222, hash: "a3cebbf30be6b9268a0ed413c9bbc256dfa9f4bfa04f1a75f144d135da5e21a5" },
    { name: "Alpöge’s proof entry point", path: "riemann-hypothesis/40e56bab026552e089d7afcfeff08d2defb9c005/src/Main.lean", size: 433, hash: "017645ca448f2fd1f6fd5c4c2cb2c6e96e472725be13f6e180ca6e1574360939" },
    { name: "Comparator configuration", path: "riemann-hypothesis/0df13c6021f92a746687929a26f1b6dc286aef09/comparator.json", size: 460, hash: "8ea890e6ccda9cf3983ada343af18a41d12542036875a3936e7925ed5b1582ff" }
  ];

  async function checkFile(pin, fetcher = fetch) {
    const abort = new AbortController();
    const deadline = setTimeout(() => abort.abort(), 15000);
    try {
      const response = await fetcher(upstream + pin.path, {
        signal: abort.signal, credentials: "omit", redirect: "error",
        referrerPolicy: "no-referrer", cache: "no-store"
      });
      if (!response.ok || !response.body) return "unavailable";
      const reader = response.body.getReader();
      const data = new Uint8Array(pin.size);
      let received = 0;
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        if (received + value.length > data.length) {
          abort.abort();
          return "different";
        }
        data.set(value, received);
        received += value.length;
      }
      if (received !== data.length) return "different";
      const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", data));
      const hex = Array.from(digest, b => b.toString(16).padStart(2, "0")).join("");
      return hex === pin.hash ? "matched" : "different";
    } catch {
      return "unavailable";
    } finally {
      clearTimeout(deadline);
    }
  }

  async function run(button, summary, list) {
    button.disabled = true;
    summary.textContent = "Checking the four pinned files…";
    list.replaceChildren();
    try {
      const results = await Promise.all(pins.map(pin => checkFile(pin)));
      const labels = { matched: "matches", different: "differs", unavailable: "could not be checked" };
      results.forEach((result, i) => {
        const item = document.createElement("li");
        item.textContent = pins[i].name + " — " + labels[result];
        list.append(item);
      });
      const total = results.filter(result => result === "matched").length;
      summary.textContent = total === pins.length
        ? "4 of 4 files match. This checks source identity. The full proof has a separate verification record."
        : total + " of 4 files match. See the individual results below.";
    } finally {
      button.disabled = false;
    }
  }

  if (typeof module === "object" && module.exports) module.exports = { pins, checkFile };
  if (typeof document === "undefined") return;
  const button = document.getElementById("check-riemann-files");
  const summary = document.getElementById("riemann-file-summary");
  const list = document.getElementById("riemann-file-results");
  if (button && summary && list) button.addEventListener("click", () => run(button, summary, list));
})();
