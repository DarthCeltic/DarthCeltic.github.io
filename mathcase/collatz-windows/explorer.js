(function () {
  "use strict";

  const DATA_URL = "atlas-12-12.json";
  const FIRST_EXAMPLE = Object.freeze({ first: 9, second: 6 });
  const numberFormat = new Intl.NumberFormat("en-US");
  const byId = (id) => document.getElementById(id);
  const firstSelect = byId("cap-first");
  const secondSelect = byId("cap-second");
  const status = byId("atlas-status");
  const horizonText = byId("horizon-label");
  const horizonText2 = byId("horizon-label-2");
  let atlas = null;

  function asInteger(value, name) {
    if (!Number.isSafeInteger(value) || value < 0) throw new Error(`The atlas has an invalid ${name}.`);
    return value;
  }

  function displayCount(value) {
    return numberFormat.format(asInteger(value, "count"));
  }

  function setStatus(message, state) {
    status.textContent = message;
    status.dataset.state = state || "ready";
  }

  function clearResultPanels() {
    byId("first-drop-panel").hidden = true;
    byId("unresolved-panel").hidden = true;
    byId("empty-result").hidden = true;
    byId("six-ten-note").hidden = true;
    byId("coverage-pill").hidden = true;
    byId("witness-trace").replaceChildren();
    byId("unresolved-trace").replaceChildren();
  }

  function fillSelect(select, capValue) {
    select.replaceChildren();
    for (let value = 0; value <= capValue; value += 1) {
      const option = document.createElement("option");
      option.value = String(value);
      option.textContent = `${value} odd ${value === 1 ? "input" : "inputs"}`;
      select.append(option);
    }
    select.disabled = false;
  }

  function findGate(first, second) {
    return atlas.upper_cap_gates.find((row) => row.cap_first === first && row.cap_second === second) || null;
  }

  function makeTrace(startValue, limit) {
    let current;
    try {
      current = BigInt(startValue);
    } catch {
      return null;
    }
    if (current < 3n) return null;
    const start = current;
    let oddInputs = 0;
    const rows = [];
    for (let step = 1; step <= limit; step += 1) {
      const odd = current % 2n === 1n;
      const next = odd ? (3n * current + 1n) / 2n : current / 2n;
      if (odd) oddInputs += 1;
      rows.push({ step, current, next, odd, ordinaryCount: odd ? 2 : 1 });
      current = next;
      if (current < start) break;
    }
    return { start, oddInputs, rows, dropped: current < start };
  }

  function renderTrace(list, intro, start, maxSteps, expectedDrop) {
    list.replaceChildren();
    const trace = makeTrace(start, maxSteps);
    if (!trace) {
      intro.textContent = "The atlas did not provide a usable integer start for this trace.";
      return;
    }

    const ordinaryCount = trace.rows.reduce((sum, row) => sum + row.ordinaryCount, 0);
    const finalStep = trace.rows.at(-1)?.step || 0;
    const firstDropPhrase = trace.dropped ? `first drops below its start at shortcut step ${finalStep} (${ordinaryCount} ordinary steps)` : `does not drop below its start within ${maxSteps} shortcut steps`;
    intro.textContent = `Start n = ${trace.start.toLocaleString("en-US")}. It ${firstDropPhrase}.`;

    for (const row of trace.rows) {
      const item = document.createElement("li");
      const kind = row.odd ? "odd input; 2 ordinary steps" : "even input; 1 ordinary step";
      item.textContent = `Step ${row.step}: ${row.current.toLocaleString("en-US")} (${kind}) → ${row.next.toLocaleString("en-US")}`;
      list.append(item);
    }

    if (typeof expectedDrop === "boolean" && trace.dropped !== expectedDrop) {
      intro.textContent += " The displayed trajectory does not match the atlas record; please use the linked receipt.";
    }
  }

  function getMemberClassification(gate) {
    return gate.member_classification && typeof gate.member_classification === "object"
      ? gate.member_classification
      : null;
  }

  function getUnresolvedStart(gate) {
    if (Number.isSafeInteger(gate.unresolved_least_representative)) return gate.unresolved_least_representative;
    const cells = atlas.exact_cells.filter((cell) =>
      cell.odd_inputs_first <= gate.cap_first && cell.odd_inputs_second <= gate.cap_second
    );
    const starts = cells
      .filter((cell) => cell.least_representative_no_drop_by_horizon_count > 0 && Number.isSafeInteger(cell.least_unresolved_representative))
      .map((cell) => cell.least_unresolved_representative);
    return starts.length ? Math.min(...starts) : null;
  }

  function renderGate() {
    if (!atlas) return;
    clearResultPanels();
    const first = Number(firstSelect.value);
    const second = Number(secondSelect.value);
    const gate = findGate(first, second);
    const heading = byId("selected-filter-title");
    const summary = byId("result-summary");
    const pill = byId("coverage-pill");

    heading.textContent = `At most ${first} odd inputs, then ${second}`;
    if (!gate) {
      byId("empty-result").hidden = false;
      summary.textContent = "The published atlas has no record for this pair of caps.";
      byId("admitted-count").textContent = "—";
      byId("covered-count").textContent = "—";
      byId("unresolved-count").textContent = "—";
      return;
    }

    const admitted = asInteger(gate.admitted_class_count, "admitted-class count");
    const covered = asInteger(gate.guaranteed_drop_class_count, "covered-class count");
    const noDropLeastReps = asInteger(gate.least_representative_no_drop_class_count, "unresolved-representative count");
    const horizon = asInteger(atlas.horizon, "horizon");
    byId("admitted-count").textContent = displayCount(admitted);
    byId("covered-count").textContent = displayCount(covered);
    byId("unresolved-count").textContent = displayCount(noDropLeastReps);
    horizonText.textContent = String(horizon);
    horizonText2.textContent = String(horizon);

    const member = getMemberClassification(gate);
    let memberMixed = 0;
    let memberNoDrop = 0;
    if (member) {
      const allDrop = asInteger(member.all_member_drop_class_count, "all-member coverage count");
      memberMixed = asInteger(member.mixed_member_class_count, "mixed-member class count");
      memberNoDrop = asInteger(member.no_member_drop_class_count, "no-member-drop class count");
      const combined = allDrop + memberMixed + memberNoDrop;
      if (combined !== admitted) throw new Error("The member classifications do not sum to the admitted parity classes.");
      if (allDrop !== covered || memberMixed + memberNoDrop !== noDropLeastReps) throw new Error("The member audit and representative atlas counts disagree.");
      byId("covered-count").textContent = displayCount(allDrop);
      byId("unresolved-count").textContent = displayCount(memberMixed + memberNoDrop);
      summary.textContent = `${displayCount(admitted)} parity classes meet these caps. In ${displayCount(allDrop)} classes, every start has a first drop by step ${horizon}. ${displayCount(memberNoDrop)} classes have no first drop by that horizon for any start. ${displayCount(memberMixed)} classes have mixed behavior: some starts drop by the horizon and others do not.`;
    } else if (gate.fully_covered) {
      summary.textContent = `${displayCount(admitted)} parity classes meet these caps. Every qualifying start has a first drop by step ${horizon}, with the endpoint slope checked to extend the result to larger starts in each class.`;
    } else {
      summary.textContent = `${displayCount(admitted)} parity classes meet these caps. The atlas does not give a uniform first-drop bound by step ${horizon} for every qualifying class.`;
    }

    pill.hidden = false;
    pill.dataset.state = gate.fully_covered ? "full" : "partial";
    pill.textContent = gate.fully_covered ? `Full ${horizon}-step coverage` : `Not covered by ${horizon}`;

    if (!admitted) {
      byId("empty-result").hidden = false;
      summary.textContent = "No parity classes meet both caps.";
      return;
    }

    if (gate.fully_covered) {
      const accelerated = asInteger(gate.sharp_max_first_drop_accelerated_steps, "sharp shortcut maximum");
      const ordinary = asInteger(gate.sharp_max_first_drop_ordinary_steps, "sharp ordinary maximum");
      const witness = asInteger(gate.least_witness_accelerated, "shortcut witness");
      byId("first-drop-panel").hidden = false;
      byId("first-drop-copy").textContent = `Every n ≥ 3 that meets this condition drops below its start within at most ${accelerated} shortcut steps (${ordinary} ordinary Collatz steps). The atlas marks this maximum as sharp.`;
      byId("witness-copy").textContent = `The smallest start attaining the shortcut maximum is n = ${displayCount(witness)}.`;
      byId("six-ten-note").hidden = !(first === 6 && second === 9);
      byId("witness-trace-details").dataset.start = String(witness);
      renderTrace(byId("witness-trace"), byId("witness-trace-intro"), witness, accelerated, true);
    } else {
      const unresolved = Number.isSafeInteger(member?.least_undropped_representative)
        ? member.least_undropped_representative
        : getUnresolvedStart(gate);
      byId("unresolved-panel").hidden = false;
      if (Number.isSafeInteger(unresolved)) {
        let classification = "The atlas does not claim a uniform bound for this condition.";
        if (member) {
          classification = memberMixed > 0
            ? `${displayCount(memberMixed)} classes have mixed behavior, and ${displayCount(memberNoDrop)} have no drop by the horizon for any start.`
            : `${displayCount(memberNoDrop)} classes have no drop by the horizon for any start.`;
        }
        byId("unresolved-copy").textContent = `The smallest recorded representative that does not drop below its start within ${horizon} shortcut steps is n = ${displayCount(unresolved)}. ${classification}`;
        byId("unresolved-trace-details").dataset.start = String(unresolved);
        renderTrace(byId("unresolved-trace"), byId("unresolved-trace-intro"), unresolved, horizon, false);
      } else {
        byId("unresolved-copy").textContent = `This condition is not marked as fully covered, but the atlas does not include a representative without a first drop by step ${horizon}. See the source record for the reason.`;
      }
    }
  }

  function setPreset(first, second) {
    firstSelect.value = String(first);
    secondSelect.value = String(second);
    renderGate();
  }

  function validateAtlas(data) {
    if (!data || data.schema_version !== 1 || !data.window_lengths || typeof data.window_lengths !== "object") {
      throw new Error("The atlas has an unsupported format.");
    }
    const firstLength = data.window_lengths.first;
    const secondLength = data.window_lengths.second;
    if (firstLength !== 12 || secondLength !== 12 || data.horizon !== 24) {
      throw new Error("The atlas does not describe the expected 12+12 windows and 24-step horizon.");
    }
    if (!Array.isArray(data.upper_cap_gates) || data.upper_cap_gates.length !== 169 || !Array.isArray(data.exact_cells)) {
      throw new Error("The atlas is incomplete. It must include every pair of caps from 0 through 12.");
    }
    const pairs = new Set(data.upper_cap_gates.map((gate) => `${gate.cap_first},${gate.cap_second}`));
    if (pairs.size !== 169) throw new Error("The atlas has duplicate or missing cap pairs.");
    for (const gate of data.upper_cap_gates) {
      if (gate.cap_first < 0 || gate.cap_first > 12 || gate.cap_second < 0 || gate.cap_second > 12) {
        throw new Error("The atlas includes a cap outside the published range.");
      }
      for (const key of ["admitted_class_count", "guaranteed_drop_class_count", "least_representative_no_drop_class_count"]) {
        asInteger(gate[key], key);
      }
      if (typeof gate.fully_covered !== "boolean") throw new Error("The atlas is missing a coverage status.");
    }
    return data;
  }

  async function loadAtlas() {
    try {
      const response = await fetch(DATA_URL, { cache: "no-cache", credentials: "same-origin" });
      if (!response.ok) throw new Error(`The atlas file returned HTTP ${response.status}.`);
      atlas = validateAtlas(await response.json());
      fillSelect(firstSelect, atlas.window_lengths.first);
      fillSelect(secondSelect, atlas.window_lengths.second);
      firstSelect.value = String(FIRST_EXAMPLE.first);
      secondSelect.value = String(FIRST_EXAMPLE.second);
      const total = atlas.upper_cap_gates.length;
      setStatus(`Atlas loaded. ${total} cap pairs are available.`, "ready");
      renderGate();
    } catch (error) {
      firstSelect.disabled = true;
      secondSelect.disabled = true;
      setStatus(error instanceof Error ? error.message : "The atlas could not be loaded.", "error");
      byId("result-summary").textContent = "The interactive data did not load. You can still download the atlas or open the public source record below.";
    }
  }

  firstSelect.addEventListener("change", renderGate);
  secondSelect.addEventListener("change", renderGate);
  document.querySelectorAll(".window-preset").forEach((button) => {
    button.addEventListener("click", () => setPreset(Number(button.dataset.first), Number(button.dataset.second)));
  });

  loadAtlas();
})();
