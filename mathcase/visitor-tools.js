(() => {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const enc = new TextEncoder();
  const savedKey = "mathcase.visitorReceipts.v1";
  let latestCollatz = null;
  let latestEgypt = null;
  let cancelEgypt = false;

  async function digest(value) {
    if (!globalThis.crypto?.subtle) throw new Error("SHA-256 is unavailable in this browser's secure context.");
    const bytes = enc.encode(value);
    const hash = await crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(hash), (byte) => byte.toString(16).padStart(2, "0")).join("");
  }

  function readNatural(text, label, maxDigits) {
    const value = text.trim();
    if (!new RegExp("^\\d{1," + maxDigits + "}$").test(value)) throw new Error(label + " must be a nonnegative whole number with at most " + maxDigits + " digits.");
    return BigInt(value);
  }

  function readBound(text, label, minimum, maximum) {
    if (!/^\d+$/.test(text.trim())) throw new Error(label + " must be a whole number.");
    const value = Number(text.trim());
    if (!Number.isSafeInteger(value) || value < minimum || value > maximum) throw new Error(label + " must be between " + minimum + " and " + maximum + ".");
    return value;
  }

  function setStatus(node, message, state) {
    node.textContent = message;
    node.dataset.state = state || "ready";
  }

  function showReceipt(container, receipt) {
    container.replaceChildren();
    const details = document.createElement("details");
    details.className = "receipt-details";
    const detailsSummary = document.createElement("summary");
    detailsSummary.textContent = "Inspect the calculation record";
    const digestLine = document.createElement("p");
    digestLine.textContent = "Receipt SHA-256: " + receipt.receipt_sha256;
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(receipt, null, 2);
    details.append(detailsSummary, digestLine, pre);
    container.append(details);
  }

  function attachReceiptButtons(prefix, getReceipt) {
    const download = $("#" + prefix + "-download");
    const save = $("#" + prefix + "-save");
    download.addEventListener("click", () => {
      const receipt = getReceipt();
      if (!receipt) return;
      const blob = new Blob([JSON.stringify(receipt, null, 2) + "\n"], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "mathcase-" + prefix + "-receipt-" + receipt.receipt_sha256.slice(0, 12) + ".json";
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 0);
    });
    save.addEventListener("click", () => {
      const receipt = getReceipt();
      if (!receipt) return;
      try {
        const current = JSON.parse(localStorage.getItem(savedKey) || "[]");
        const records = Array.isArray(current) ? current.filter((item) => item?.receipt_sha256 !== receipt.receipt_sha256) : [];
        records.unshift(receipt);
        localStorage.setItem(savedKey, JSON.stringify(records.slice(0, 20)));
        setStatus($("#" + prefix + "-status"), "Receipt saved in this browser only. It was not uploaded.", "success");
      } catch {
        setStatus($("#" + prefix + "-status"), "This browser blocked local storage. Use Download receipt instead.", "error");
      }
    });
  }

  function wireCollatzMode() {
    const mode = $("#collatz-mode");
    const direct = $("#collatz-direct-fields");
    const residue = $("#collatz-residue-fields");
    const directInput = $("#collatz-start");
    const residueInputs = [$("#collatz-exponent"), $("#collatz-residue"), $("#collatz-parameter")];
    const update = () => {
      const useResidue = mode.value === "residue";
      direct.hidden = useResidue;
      residue.hidden = !useResidue;
      directInput.disabled = useResidue;
      directInput.required = !useResidue;
      residueInputs.forEach((input) => {
        input.disabled = !useResidue;
        input.required = useResidue;
      });
    };
    mode.addEventListener("change", update);
    update();
  }

  async function checkCollatz(event) {
    event.preventDefault();
    const form = $("#visitor-collatz-form");
    const status = $("#collatz-status");
    const result = $("#collatz-result");
    const mode = $("#collatz-mode").value;
    const download = $("#collatz-download");
    const save = $("#collatz-save");
    download.disabled = true;
    save.disabled = true;
    latestCollatz = null;
    result.replaceChildren();
    try {
      let start;
      let input;
      if (mode === "direct") {
        start = readNatural($("#collatz-start").value, "Starting number", 300);
        input = { mode: "direct", n: start.toString() };
      } else {
        const m = readBound($("#collatz-exponent").value, "Exponent m", 0, 256);
        const r = readNatural($("#collatz-residue").value, "Residue r", 300);
        const k = readNatural($("#collatz-parameter").value, "Parameter k", 300);
        const modulus = 1n << BigInt(m);
        if (r >= modulus) throw new Error("Residue r must be less than 2^m.");
        start = modulus * k + r;
        input = { mode: "residue_representative", m, r: r.toString(), k: k.toString() };
      }
      const maxSteps = readBound($("#collatz-step-limit").value, "Maximum steps", 1, 10000);
      let value = start;
      let firstDescentStep = null;
      let parityBits = "";
      for (let step = 1; step <= maxSteps; step += 1) {
        if (value % 2n === 0n) {
          parityBits += "0";
          value /= 2n;
        } else {
          parityBits += "1";
          value = 3n * value + 1n;
        }
        if (value < start) {
          firstDescentStep = step;
          break;
        }
      }
      const statement = firstDescentStep === null
        ? "No iterate below the start was observed within the stated finite step bound."
        : "For this exact starting number, a standard Collatz iterate within the stated bound is strictly smaller than the start.";
      const core = {
        schema: "mathcase-collatz-finite-trajectory-v1",
        input,
        starting_value: start.toString(),
        max_steps: maxSteps,
        steps_executed: parityBits.length,
        endpoint: value.toString(),
        first_strict_descent_step: firstDescentStep,
        parity_bits: parityBits,
        statement,
        outcome: firstDescentStep === null ? "NO_DESCENT_WITHIN_BOUND" : "PASS_CONCRETE_DESCENT",
        scope: "one concrete input only; not an all-parameter proof"
      };
      const statementSha = await digest(statement);
      const receiptSha = await digest(JSON.stringify(core));
      latestCollatz = {
        ...core,
        statement_sha256: statementSha,
        receipt_sha256: receiptSha,
        created_at_utc: new Date().toISOString(),
        summary: firstDescentStep === null
          ? "No strict descent was found in " + maxSteps + " steps for this input; this is not a convergence counterexample."
          : "The first value below the start appeared at step " + firstDescentStep + " for this one input."
      };
      showReceipt(result, latestCollatz);
      download.disabled = false;
      save.disabled = false;
      const explanation = firstDescentStep === null
        ? `Starting at ${start}, no smaller value appeared in ${maxSteps} ordinary steps. The last value checked was ${value}.`
        : `Starting at ${start}, the first smaller value was ${value}, after ${firstDescentStep} ordinary ${firstDescentStep === 1 ? "step" : "steps"}.`;
      setStatus(status, explanation, firstDescentStep === null ? "ready" : "success");
    } catch (error) {
      setStatus(status, error instanceof Error ? error.message : "The finite trajectory check failed.", "error");
    }
    return form;
  }

  function gcd(a, b) {
    while (b !== 0n) [a, b] = [b, a % b];
    return a;
  }

  function ceilDiv(a, b) {
    return (a + b - 1n) / b;
  }

  function verifyEgyptIdentity(n, x, y, z) {
    if (!(0n < x && x < y && y < z)) return false;
    return 4n * x * y * z === n * (x * y + x * z + y * z);
  }

  function nextFrame() {
    return new Promise((resolve) => requestAnimationFrame(resolve));
  }

  async function searchEgypt(event) {
    event.preventDefault();
    const status = $("#egypt-status");
    const result = $("#egypt-result");
    const run = $("#egypt-run");
    const cancel = $("#egypt-cancel");
    const download = $("#egypt-download");
    const save = $("#egypt-save");
    run.disabled = true;
    cancel.disabled = false;
    download.disabled = true;
    save.disabled = true;
    cancelEgypt = false;
    latestEgypt = null;
    result.replaceChildren();
    setStatus(status, "Checking the selected finite bounds in this browser…", "working");
    try {
      const d = readNatural($("#egypt-d").value, "Parameter d", 80);
      if (d === 0n) throw new Error("Parameter d must be positive so n=12d+1 is greater than 1.");
      const n = 12n * d + 1n;
      const xLimit = readBound($("#egypt-x-budget").value, "x-value limit", 1, 100000);
      const yLimit = readBound($("#egypt-y-budget").value, "y-values per x", 1, 100000);
      const pairLimit = readBound($("#egypt-total-budget").value, "Total pair-check limit", 1, 1000000);
      const xStart = ceilDiv(n, 4n);
      let xTried = 0;
      let pairsChecked = 0;
      let found = null;
      let stopped = false;
      for (let xOffset = 0; xOffset < xLimit && pairsChecked < pairLimit; xOffset += 1) {
        if (cancelEgypt) { stopped = true; break; }
        const x = xStart + BigInt(xOffset);
        const residualNumerator0 = 4n * x - n;
        if (residualNumerator0 <= 0n) continue;
        const residualDenominator0 = n * x;
        const divisor = gcd(residualNumerator0, residualDenominator0);
        const p = residualNumerator0 / divisor;
        const q = residualDenominator0 / divisor;
        let yStart = x + 1n;
        const positiveRemainderStart = q / p + 1n;
        if (positiveRemainderStart > yStart) yStart = positiveRemainderStart;
        xTried += 1;
        for (let yOffset = 0; yOffset < yLimit && pairsChecked < pairLimit; yOffset += 1) {
          if (cancelEgypt) { stopped = true; break; }
          const y = yStart + BigInt(yOffset);
          pairsChecked += 1;
          const remainderDenominator = p * y - q;
          if (remainderDenominator > 0n) {
            const zNumerator = q * y;
            if (zNumerator % remainderDenominator === 0n) {
              const z = zNumerator / remainderDenominator;
              if (verifyEgyptIdentity(n, x, y, z)) {
                found = { x: x.toString(), y: y.toString(), z: z.toString() };
                break;
              }
            }
          }
          if (pairsChecked % 2048 === 0) {
            setStatus(status, "Checked " + pairsChecked.toLocaleString("en-US") + " bounded (x,y) pairs…", "working");
            await nextFrame();
          }
        }
        if (found || stopped) break;
      }
      const outcome = found ? "WITNESS_FOUND" : stopped ? "CANCELLED" : "NO_WITNESS_WITHIN_BOUNDS";
      const statement = found
        ? "The supplied n has a positive, strictly increasing exact three-unit-fraction representation."
        : "No exact representation was found within the checked denominator bounds.";
      const core = {
        schema: "mathcase-erdos-straus-bounded-search-v1",
        parameter_d: d.toString(),
        n: n.toString(),
        identity: "4/n = 1/x + 1/y + 1/z",
        bounds: {
          x_start: xStart.toString(),
          x_values_limit: xLimit,
          y_values_per_x: yLimit,
          total_pair_check_limit: pairLimit,
          x_values_tested: xTried,
          pairs_checked: pairsChecked
        },
        candidate: found,
        exact_integer_check: found ? "4*x*y*z = n*(x*y + x*z + y*z)" : null,
        denominator_order: found ? "0 < x < y < z" : null,
        statement,
        outcome,
        scope: "one n=12*d+1 and only the finite denominator bounds recorded here"
      };
      const statementSha = await digest(statement);
      const receiptSha = await digest(JSON.stringify(core));
      latestEgypt = {
        ...core,
        statement_sha256: statementSha,
        receipt_sha256: receiptSha,
        created_at_utc: new Date().toISOString(),
        summary: found
          ? "Found an exact witness for n=" + n.toString() + " after " + pairsChecked.toLocaleString("en-US") + " pair checks."
          : stopped
            ? "Search stopped after " + pairsChecked.toLocaleString("en-US") + " pair checks. The receipt records the partial bounds."
            : "No witness found in " + pairsChecked.toLocaleString("en-US") + " checked pairs. This is not a counterexample."
      };
      showReceipt(result, latestEgypt);
      download.disabled = false;
      save.disabled = false;
      setStatus(status, found
        ? `4/${n} = 1/${found.x} + 1/${found.y} + 1/${found.z}. The sum was checked exactly.`
        : latestEgypt.summary, found ? "success" : "ready");
    } catch (error) {
      setStatus(status, error instanceof Error ? error.message : "The bounded search failed.", "error");
    } finally {
      run.disabled = false;
      cancel.disabled = true;
    }
  }

  function wire() {
    wireCollatzMode();
    $("#visitor-collatz-form").addEventListener("submit", checkCollatz);
    $("#visitor-egypt-form").addEventListener("submit", searchEgypt);
    $("#egypt-cancel").addEventListener("click", () => {
      cancelEgypt = true;
      setStatus($("#egypt-status"), "Stopping at the next bounded-check boundary…", "working");
    });
    attachReceiptButtons("collatz", () => latestCollatz);
    attachReceiptButtons("egypt", () => latestEgypt);
  }

  wire();
})();
