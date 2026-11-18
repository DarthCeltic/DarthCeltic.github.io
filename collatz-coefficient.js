(() => {
  "use strict";

  const EXPECTED_SHA256 = "30f06904507a35d180fab9d0d9195759047d13edfd857c04e2ef483eaf75194a";
  const EXPECTED_ROWS = 2652;
  const START_COEFFICIENT = 1048576n;
  const END_COEFFICIENT = 531441n;
  const SLOPE = START_COEFFICIENT - END_COEFFICIENT;
  const TABLE_URL = "evidence/collatz/m20-source-replay-2026-11-18/coefficient-audit/pairs.tsv";

  const form = document.querySelector("#coefficient-form");
  const status = document.querySelector("#coefficient-status");
  const result = document.querySelector("#coefficient-result");
  const run = document.querySelector("#coefficient-run");
  const pairInput = document.querySelector("#coefficient-pair");
  const kInput = document.querySelector("#coefficient-k");
  if (!form || !status || !result || !run || !pairInput || !kInput) return;

  function parseTable(text) {
    const lines = text.replace(/^\uFEFF/, "").replace(/\r\n/g, "\n").trimEnd().split("\n");
    const header = ["pair", "composition_module", "source_line", "r", "q", "intercept_gap", "source_sha256"];
    if (lines.length !== EXPECTED_ROWS + 1 || lines[0] !== header.join("\t")) throw new Error("The table header or row count does not match the pinned audit.");
    const rows = lines.slice(1).map((line, index) => {
      const values = line.split("\t");
      if (values.length !== header.length) throw new Error(`Table row ${index + 1} has the wrong number of fields.`);
      const row = Object.fromEntries(header.map((key, position) => [key, values[position]]));
      if (!/^\d+$/.test(row.pair) || Number(row.pair) !== index + 1 || !/^\d+$/.test(row.source_line)) throw new Error(`Table row ${index + 1} has an invalid row number.`);
      if (!/^M20CompositionShard\d{3}\.lean$/.test(row.composition_module) || !/^[a-f0-9]{64}$/.test(row.source_sha256)) throw new Error(`Table row ${index + 1} has an invalid source binding.`);
      for (const key of ["r", "q", "intercept_gap", "source_line"]) if (!/^\d+$/.test(row[key])) throw new Error(`Table row ${index + 1} has a non-integer ${key}.`);
      row.pairNumber = Number(row.pair);
      row.rBig = BigInt(row.r);
      row.qBig = BigInt(row.q);
      row.gapBig = BigInt(row.intercept_gap);
      if (row.rBig - row.qBig !== row.gapBig || row.gapBig <= 0n) throw new Error(`Table row ${index + 1} has an incorrect or nonpositive intercept.`);
      return row;
    });
    const uniquePairs = new Set(rows.map((row) => `${row.r},${row.q}`));
    const uniqueModules = new Set(rows.map((row) => row.composition_module));
    const minimumGap = rows.reduce((minimum, row) => row.gapBig < minimum ? row.gapBig : minimum, rows[0].gapBig);
    if (uniquePairs.size !== EXPECTED_ROWS || uniqueModules.size !== 133 || minimumGap !== 117n || SLOPE !== 517135n) throw new Error("The pair/module uniqueness, slope, or minimum-gap check failed.");
    return { rows, minimumGap };
  }

  function addText(parent, tag, text, className) {
    const node = document.createElement(tag);
    node.textContent = text;
    if (className) node.className = className;
    parent.append(node);
    return node;
  }

  function formatInteger(value) {
    return value.toLocaleString("en-US");
  }

  function calculate(rows) {
    result.replaceChildren();
    const pairNumberText = pairInput.value.trim();
    const kText = kInput.value.trim();
    if (!/^\d+$/.test(pairNumberText)) {
      addText(result, "p", "Enter a whole-number pair row.", "coefficient-error");
      return;
    }
    if (!/^\d{1,1000}$/.test(kText)) {
      addText(result, "p", "Enter a nonnegative whole number k using 1–1,000 digits.", "coefficient-error");
      return;
    }
    const pairNumber = Number(pairNumberText);
    if (!Number.isSafeInteger(pairNumber) || pairNumber < 1 || pairNumber > rows.length) {
      addText(result, "p", `Choose a pair row from 1 to ${rows.length.toLocaleString("en-US")}.`, "coefficient-error");
      return;
    }

    const row = rows[pairNumber - 1];
    const k = BigInt(kText);
    const start = START_COEFFICIENT * k + row.rBig;
    const endpoint = END_COEFFICIENT * k + row.qBig;
    const difference = start - endpoint;
    const coefficientExpression = SLOPE * k + row.gapBig;
    if (difference !== coefficientExpression) {
      addText(result, "p", "The exact-integer identity check failed.", "coefficient-error");
      return;
    }

    const card = document.createElement("div");
    card.className = "coefficient-result-card";
    addText(card, "h3", `Pair ${row.pairNumber.toLocaleString("en-US")} · ${row.composition_module}, source line ${row.source_line}`);
    addText(card, "p", `Listed coefficients: r = ${formatInteger(row.rBig)}, q = ${formatInteger(row.qBig)}, so r − q = ${formatInteger(row.gapBig)}.`);
    addText(card, "p", `For k = ${formatInteger(k)}: start = ${formatInteger(start)}; recorded endpoint = ${formatInteger(endpoint)}.`);
    addText(card, "p", `start − endpoint = ${formatInteger(difference)}; 517,135k + (r − q) = ${formatInteger(coefficientExpression)}. Exact integer identity: checked.` , "coefficient-identity");
    addText(card, "p", `Across the verified list, every intercept is at least 117. Since k ≥ 0 and 517,135 > 0, this expression stays positive for every natural k in each listed row.`, "coefficient-bound");
    addText(card, "p", "This arithmetic check does not re-run the 32 Collatz steps; the Lean replay is the evidence for that equality.", "coefficient-limit");
    result.append(card);
  }

  async function loadTable() {
    status.textContent = "Loading the listed source pairs and checking the table hash…";
    run.disabled = true;
    try {
      if (!globalThis.crypto?.subtle) throw new Error("Web Crypto SHA-256 is unavailable in this browser.");
      const response = await fetch(TABLE_URL, { credentials: "same-origin", cache: "no-cache" });
      if (!response.ok) throw new Error(`The included pair table returned HTTP ${response.status}.`);
      const bytes = await response.arrayBuffer();
      const digest = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)), (byte) => byte.toString(16).padStart(2, "0")).join("");
      if (digest !== EXPECTED_SHA256) throw new Error("The included pair table does not match its pinned SHA-256.");
      const text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
      const audit = parseTable(text);
      pairInput.max = String(audit.rows.length);
      pairInput.value = "1";
      pairInput.disabled = false;
      kInput.disabled = false;
      run.disabled = false;
      status.textContent = `Verified ${audit.rows.length.toLocaleString("en-US")} distinct source pairs; slope 517,135; minimum intercept 117; table SHA-256 ${digest}.`;
      calculate(audit.rows);
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        calculate(audit.rows);
      });
    } catch (error) {
      status.textContent = `Calculator not loaded: ${error instanceof Error ? error.message : "verification failed"}`;
      addText(result, "p", "No arithmetic result is displayed as verified.", "coefficient-error");
    }
  }

  loadTable();
})();
