(function () {
  "use strict";

  const core = window.MathCaseKnowledgeGraphCore;
  const rawRoot = `https://raw.githubusercontent.com/DarthCeltic/MathCase/${core.PIN.commit}/reproduction/m15-m20-r2/evidence/knowledge-graph/public-slice-v1`;
  const expected = {
    "manifest.json": { bytes: 804 },
    "manifest.sha256": { bytes: 80 },
    "index.jsonl": { bytes: 634340 },
    "records.jsonl": { bytes: 7438296 },
    "records.sha256": { bytes: 80 }
  };
  const loadButton = document.getElementById("load-graph");
  const exampleButton = document.getElementById("open-example");
  const search = document.getElementById("graph-search");
  const status = document.getElementById("graph-status");
  const count = document.getElementById("graph-count");
  const resultsNode = document.getElementById("graph-results");
  const detail = document.getElementById("graph-detail");
  const snapshotCommit = document.getElementById("snapshot-commit");
  const replayPackageLink = document.getElementById("replay-package-link");
  snapshotCommit.textContent = core.PIN.commit;
  replayPackageLink.href = `https://github.com/DarthCeltic/MathCase/tree/${core.PIN.commit}/reproduction/m15-m20-r2`;
  let records = [];
  let selected = null;
  let detailGeneration = 0;

  function setStatus(message, error = false) {
    status.textContent = message;
    status.classList.toggle("error", error);
  }

  async function sha256(bytes) {
    const hash = await crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(hash), (value) => value.toString(16).padStart(2, "0")).join("");
  }

  async function fetchPinned(name) {
    const pin = expected[name];
    if (!pin) throw new Error(`The requested proof file was not in the pinned file list.`);
    const response = await fetch(`${rawRoot}/${name}`, { mode: "cors", credentials: "omit", cache: "force-cache", referrerPolicy: "no-referrer" });
    if (!response.ok) throw new Error(`The pinned ${name} file could not be reached (HTTP ${response.status}).`);
    const bytes = new Uint8Array(await response.arrayBuffer());
    if (bytes.byteLength !== pin.bytes) throw new Error(`The pinned ${name} file had an unexpected size.`);
    return bytes;
  }

  function decodeSidecar(bytes, name) {
    try { return new TextDecoder("utf-8", { fatal: true }).decode(bytes); }
    catch { throw new Error(`The committed ${name} checksum file was not valid UTF-8.`); }
  }

  function parseJSON(bytes, name) {
    try { return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)); }
    catch { throw new Error(`The pinned ${name} file was not valid UTF-8 JSON.`); }
  }

  function parseJSONL(bytes, name) {
    try {
      const source = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
      return source.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
    } catch { throw new Error(`The pinned ${name} file contained an unreadable record.`); }
  }

  function addText(parent, tag, value) {
    const node = document.createElement(tag);
    node.textContent = String(value ?? "not recorded");
    parent.append(node);
    return node;
  }

  function addDetailRow(dl, label, value) {
    const row = document.createElement("div");
    addText(row, "dt", label);
    const dd = document.createElement("dd");
    dd.textContent = Array.isArray(value) ? value.join(", ") : String(value ?? "not recorded");
    row.append(dd);
    dl.append(row);
  }

  async function showRecord(record) {
    const generation = ++detailGeneration;
    detail.replaceChildren();
    detail.hidden = true;
    setStatus("Checking this theorem’s exact statement digest…");
    const digest = await sha256(new TextEncoder().encode(record.lean_statement_exact));
    if (generation !== detailGeneration) return;
    if (digest !== record.statement_sha256) {
      setStatus("This row’s statement did not match its digest, so it is hidden. Reload the pinned data later.", true);
      return;
    }
    selected = record.case_id;
    renderResults();
    const parsed = core.parseCollatzStatement(record.lean_statement_exact);
    addText(detail, "h3", parsed ? `${parsed.startText} → ${parsed.endText}` : "Saved theorem details");
    addText(detail, "p", parsed.plainText);
    addText(detail, "h4", "What Lean checked");
    addText(detail, "p", "This exact statement passed an individual module check in the pinned replay record.");
    const dl = document.createElement("dl");
    addDetailRow(dl, "Axiom report", record.axioms);
    addDetailRow(dl, "sorryAx reported", record.sorryAx);
    addDetailRow(dl, "Human wording review", "Not done separately for this individual row");
    addDetailRow(dl, "Promotion", "Not promoted beyond the recorded individual replay");
    addDetailRow(dl, "Novelty", "Not assessed");
    addDetailRow(dl, "What this row proves", record.claim_limit);
    addDetailRow(dl, "Imports", record.dependencies?.imports);
    addDetailRow(dl, "Local declarations referenced", record.dependencies?.module_local_declarations_referenced);
    addDetailRow(dl, "Dependency limit", record.dependencies?.scope_note);
    addDetailRow(dl, "Statement SHA-256", record.statement_sha256);
    addDetailRow(dl, "Source SHA-256", record.source.sha256);
    addDetailRow(dl, "Receipt file SHA-256", record.receipt.file_sha256);
    addDetailRow(dl, "Receipt row SHA-256", record.receipt.row_sha256);
    detail.append(dl);
    const exact = document.createElement("details");
    const summary = addText(exact, "summary", "Show the exact Lean statement");
    summary.className = "detail-summary";
    addText(exact, "pre", record.lean_statement_exact);
    detail.append(exact);
    const technical = document.createElement("details");
    addText(technical, "summary", "Show the internal record ID");
    addText(technical, "p", record.case_id);
    detail.append(technical);
    const links = document.createElement("p");
    links.className = "library-links";
    for (const [label, href] of [
      ["Open the exact Lean source", core.githubFileUrl(record.source.package_path, record.source.declaration_line)],
      ["Open the matching replay receipt row", core.githubFileUrl(record.receipt.package_path, record.receipt.line)]
    ]) {
      const link = document.createElement("a");
      link.href = href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = label;
      links.append(link);
    }
    detail.append(links);
    detail.hidden = false;
    setStatus("The statement digest matches the pinned record.");
  }

  function renderResults() {
    const query = search.value;
    const matches = records.filter((record) => core.matchesSearch(record, query));
    const visible = matches.slice(0, 30);
    resultsNode.replaceChildren();
    for (const record of visible) {
      const parsed = core.parseCollatzStatement(record.lean_statement_exact);
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "library-result";
      button.setAttribute("aria-pressed", record.case_id === selected ? "true" : "false");
      addText(button, "strong", parsed ? `Starting numbers ${parsed.startText}` : "Saved theorem");
      addText(button, "span", parsed?.plainText || "Open this saved formal statement.");
      button.addEventListener("click", () => { showRecord(record).catch((error) => setStatus(error.message, true)); });
      item.append(button);
      resultsNode.append(item);
    }
    count.textContent = matches.length === 0
      ? "No text matched. Try a theorem name or one of the numbers in a formula."
      : `Showing ${visible.length} of ${matches.length} matching saved statements${matches.length > visible.length ? ". Add more words to narrow the list." : "."}`;
  }

  async function loadGraph() {
    loadButton.disabled = true;
    loadButton.setAttribute("aria-busy", "true");
    setStatus("Fetching and checking the pinned public proof files…");
    try {
      const [manifestBytes, manifestSidecarBytes, indexBytes, recordBytes, recordsSidecarBytes] = await Promise.all([
        fetchPinned("manifest.json"), fetchPinned("manifest.sha256"), fetchPinned("index.jsonl"),
        fetchPinned("records.jsonl"), fetchPinned("records.sha256")
      ]);
      const manifestSidecar = decodeSidecar(manifestSidecarBytes, "manifest.json");
      const recordsSidecar = decodeSidecar(recordsSidecarBytes, "records.jsonl");
      const actualHashes = {
        manifest: await sha256(manifestBytes),
        index: await sha256(indexBytes),
        records: await sha256(recordBytes)
      };
      const manifest = parseJSON(manifestBytes, "manifest.json");
      core.verifySnapshotHashes(manifestSidecar, recordsSidecar, manifest, actualHashes);
      const index = parseJSONL(indexBytes, "index.jsonl");
      records = parseJSONL(recordBytes, "records.jsonl");
      core.validateGraph(manifest, index, records, actualHashes);
      search.disabled = false;
      exampleButton.disabled = false;
      loadButton.textContent = "Proof records loaded and checked";
      search.value = "32768k+127";
      search.focus();
      renderResults();
      setStatus("4,262 records loaded. The browser checked the two committed SHA-256 files, the index hash recorded in the manifest, review labels, and statement formats.");
    } catch (error) {
      records = [];
      loadButton.disabled = false;
      loadButton.removeAttribute("aria-busy");
      setStatus(`${error.message} This is a data-connection or integrity problem, not a failed Lean proof.`, true);
    }
  }

  loadButton.addEventListener("click", () => { loadGraph().catch((error) => setStatus(error.message, true)); });
  exampleButton.addEventListener("click", () => {
    const sample = records.find((record) => {
      const parsed = core.parseCollatzStatement(record.lean_statement_exact);
      return parsed?.startSlope === "32768" && parsed?.startOffset === "127";
    });
    if (sample) showRecord(sample).catch((error) => setStatus(error.message, true));
    else setStatus("The example statement was not in the verified snapshot.", true);
  });
  search.addEventListener("input", renderResults);
})();
