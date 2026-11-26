(() => {
  "use strict";

  const root = "evidence/knowledge-graph/public-slice-v1/";
  const replayRoot = "evidence/collatz/m15-m20-pinned-replay/";
  const pinned = {
    manifest: "3636c16287b6df468616b2cd8c982d1265c0fab0821abddd3746004c952bd400",
    index: "b0b618ab0466f82642fe3f8939ee0757ba42e471d3894d9d87c0dd22b66db45b",
    records: "fc1b7ced1c078f1d719253d9f70efe31da40a81720e69f7cddb496cdb85012ed",
  };
  const loadButton = document.querySelector("#public-graph-load");
  const submitButton = document.querySelector("#public-graph-submit");
  const form = document.querySelector("#public-graph-form");
  const input = document.querySelector("#public-graph-query");
  const status = document.querySelector("#public-graph-status");
  const results = document.querySelector("#public-graph-results");
  if (!loadButton || !submitButton || !form || !input || !status || !results) return;

  let records = [];
  let indexById = new Map();

  const toHex = (bytes) => Array.from(new Uint8Array(bytes), (b) => b.toString(16).padStart(2, "0")).join("");
  const sha256 = async (bytes) => toHex(await globalThis.crypto.subtle.digest("SHA-256", bytes));

  async function fetchBytes(path) {
    const response = await fetch(path, { cache: "no-cache", credentials: "same-origin" });
    if (!response.ok) throw new Error(`Could not load ${path} (HTTP ${response.status}).`);
    return response.arrayBuffer();
  }

  function parseLines(text, label) {
    return text.split(/\r?\n/).filter(Boolean).map((line, i) => {
      try { return JSON.parse(line); }
      catch { throw new Error(`${label} has invalid JSON on line ${i + 1}.`); }
    });
  }

  async function loadIndex() {
    if (!globalThis.crypto?.subtle) throw new Error("This browser does not provide Web Crypto SHA-256; open the site over HTTPS in a current browser.");
    const [manifestBytes, indexBytes, recordBytes] = await Promise.all([
      fetchBytes(`${root}manifest.json`),
      fetchBytes(`${root}index.jsonl`),
      fetchBytes(`${root}records.jsonl`),
    ]);
    const [manifestHash, indexHash, recordHash] = await Promise.all([
      sha256(manifestBytes), sha256(indexBytes), sha256(recordBytes),
    ]);
    if (manifestHash !== pinned.manifest) throw new Error("Manifest SHA-256 did not match the pinned public value.");
    if (indexHash !== pinned.index) throw new Error("Index SHA-256 did not match the pinned public value.");
    if (recordHash !== pinned.records) throw new Error("Records SHA-256 did not match the pinned public value.");

    const decoder = new TextDecoder("utf-8", { fatal: true });
    const manifest = JSON.parse(decoder.decode(manifestBytes));
    const indexRows = parseLines(decoder.decode(indexBytes), "Index");
    const recordRows = parseLines(decoder.decode(recordBytes), "Records");
    if (manifest.record_count !== 4262 || manifest.index_sha256 !== pinned.index || recordRows.length !== 4262 || indexRows.length !== 4262) {
      throw new Error("The verified package counts do not match the pinned manifest.");
    }
    indexById = new Map(indexRows.map((row) => [row.case_id, row.statement_sha256]));
    if (indexById.size !== 4262) throw new Error("The index contains duplicate or missing case identifiers.");
    for (const row of recordRows) {
      if (indexById.get(row.case_id) !== row.statement_sha256 || typeof row.lean_statement_exact !== "string") {
        throw new Error("A record does not match its exact-statement index entry.");
      }
    }
    records = recordRows;
    input.disabled = false;
    submitButton.disabled = false;
    loadButton.disabled = true;
    loadButton.textContent = "Index verified";
    status.textContent = "Verified: 4,262 records, manifest, index, and statement file hashes match. Search by exact text or theorem name.";
  }

  function addText(parent, tag, text, className) {
    const element = document.createElement(tag);
    element.textContent = text;
    if (className) element.className = className;
    parent.append(element);
    return element;
  }

  async function renderMatches() {
    const query = input.value.trim().toLocaleLowerCase();
    results.replaceChildren();
    if (!query) {
      status.textContent = "Type part of a theorem name or exact Lean statement to search.";
      return;
    }
    const matchingRows = records.filter((row) => [
      row.case_id,
      row.lean_statement_exact,
      row.source?.package_path,
      ...(row.dependencies?.imports || []),
      ...(row.dependencies?.module_local_declarations_referenced || []),
    ].filter(Boolean).join(" ").toLocaleLowerCase().includes(query));
    const hits = matchingRows.slice(0, 30);
    if (matchingRows.length === 0) {
      status.textContent = "No literal matches. This index does not do semantic search.";
      return;
    }
    for (const row of hits) {
      const statementHash = await sha256(new TextEncoder().encode(row.lean_statement_exact));
      if (statementHash !== row.statement_sha256 || indexById.get(row.case_id) !== row.statement_sha256) {
        throw new Error(`Statement digest check failed for ${row.case_id}.`);
      }
      const card = document.createElement("article");
      card.className = "graph-result";
      addText(card, "h3", row.case_id);
      addText(card, "p", `${row.kind || "Lean result"} · ${row.lean_status || "status recorded"}`);
      const sorryAx = row.sorryAx === true ? "present" : row.sorryAx === false ? "absent" : "not recorded";
      addText(card, "p", `Axioms: ${(row.axioms || []).join(", ") || "none recorded"} · sorryAx: ${sorryAx}`, "graph-tags");
      const details = document.createElement("details");
      const summary = document.createElement("summary");
      summary.textContent = "Inspect exact statement and evidence binding";
      details.append(summary);
      addText(details, "pre", row.lean_statement_exact);
      addText(details, "p", `M0: ${row.m0_status || "not recorded"} · M4: ${row.m4_status || "not recorded"} · novelty: ${row.novelty_status || "not assessed"}`);
      addText(details, "p", `Source: ${row.source?.package_path || "not recorded"} · SHA-256: ${row.source?.sha256 || "not recorded"}`);
      const receipt = row.receipt || {};
      addText(details, "p", `Receipt row: ${receipt.package_path || "not recorded"}, line ${receipt.line ?? "?"} · row SHA-256: ${receipt.row_sha256 || "not recorded"}`);
      addText(details, "p", `Dependencies listed: ${(row.dependencies?.imports || []).join(", ") || "none listed"}`);
      const sourcePath = row.source?.package_path;
      if (typeof sourcePath === "string" && sourcePath.startsWith("sources/") && !sourcePath.includes("..")) {
        const link = document.createElement("a");
        link.href = `${replayRoot}${sourcePath}`;
        link.textContent = "Open the bound Lean source file";
        details.append(link);
      }
      card.append(details);
      results.append(card);
    }
    status.textContent = `${matchingRows.length} literal match${matchingRows.length === 1 ? "" : "es"}${matchingRows.length > 30 ? " (showing the first 30)" : ""}. Each displayed statement digest was checked.`;
  }

  loadButton.addEventListener("click", async () => {
    loadButton.disabled = true;
    status.textContent = "Loading the public statement files and checking their SHA-256 values…";
    try { await loadIndex(); }
    catch (error) {
      loadButton.disabled = false;
      status.textContent = `Index not loaded: ${error instanceof Error ? error.message : "verification failed"}`;
    }
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    renderMatches().catch((error) => {
      results.replaceChildren();
      status.textContent = `Search stopped: ${error instanceof Error ? error.message : "statement check failed"}`;
    });
  });
})();
