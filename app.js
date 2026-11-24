/* A static reader over whitelisted saved evidence; only a pinned same-origin metadata read. */
(() => {
  "use strict";
  const data = window.MathCaseStaticDemo;
  if (!data || data.schema !== "mathcase-static-demo-r7") throw new Error("Saved demo data is missing");
  const byId = id => document.getElementById(id);
  const make = (tag, className = "", text = "") => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  };
  const publicCases = data.cases;
  const caseMap = new Map(publicCases.map(item => [item.id, item]));
  const position = new Map();
  byId("skip-reader")?.addEventListener("click", event => {
    event.preventDefault();
    byId("case-stage").focus();
  });

  function caseSteps(item) {
    return item.steps;
  }

  function resolveRoute() {
    if (!location.hash) return { kind: "case", id: publicCases[0].id };
    let route;
    try { route = decodeURIComponent(location.hash.slice(1)); }
    catch { return { kind: "missing", requested: "invalid case link" }; }
    const match = /^case\/([a-z0-9-]+)(?:\/(.*))?$/i.exec(route);
    if (!match) return { kind: "missing", requested: route };
    const id = match[1].toLowerCase();
    if (id === "hero-sqrt2-parent-reuse-r2") return { kind: "redirect", href: "/cases.html#sqrt2-child" };
    if (caseMap.has(id)) return { kind: "case", id };
    return { kind: "missing", requested: id };
  }

  function caseHref(id) { return "#case/" + encodeURIComponent(id); }

  function renderNav(activeId) {
    const host = byId("case-nav");
    host.replaceChildren();
    publicCases.forEach((item, index) => {
      const link = make("a", "case-tab");
      link.href = caseHref(item.id);
      if (item.id === activeId) link.setAttribute("aria-current", "page");
      link.append(make("span", "case-number", String(index + 1)));
      const label = make("span");
      label.append(make("strong", "", item.short));
      link.append(label);
      host.append(link);
    });
  }

  function renderCase() {
    const route = resolveRoute();
    const host = byId("case-stage");
    if (route.kind === "redirect") {
      location.replace(route.href);
      return;
    }
    host.replaceChildren();
    renderNav(route.kind === "case" ? route.id : null);
    if (route.kind === "missing") {
      const panel = make("section", "case-missing");
      panel.setAttribute("role", "status");
      panel.append(make("h2", "", "This saved case is not available in the public reader."));
      if (route.requested) panel.append(make("p", "", `No public case matches “${route.requested}”.`));
      panel.append(make("p", "", "The reader will not substitute a different proof or calculation."));
      const catalog = make("a", "", "Browse the public case catalog →");
      catalog.href = "/cases.html";
      panel.append(catalog);
      host.append(panel);
      return;
    }
    const id = route.id;
    const item = caseMap.get(id);
    if (!location.hash) history.replaceState(null, "", caseHref(id));
    const stepsForCase = caseSteps(item);
    let step = Math.min(position.get(id) || 0, stepsForCase.length - 1);

    const head = make("div", "stage-head");
    const headText = make("div");
    headText.append(make("h2", "", item.title));
    head.append(headText, make("span", "result", item.result));
    host.append(head);

    const reader = make("div", "reader");
    const paper = make("section", "paper");
    paper.setAttribute("aria-label", "Saved mathematical reading surface");
    const composite = item.id === "hero-composite-counterexample-r1";
    paper.append(make("div", "math", composite ? "4 divides 2 × 2" : "6 × 6 = 36"), make("p", "statement", composite
      ? "Four fits into 4 exactly once. Can it fit into 2 a whole number of times?"
      : "Three divides 36. It also divides 6. Could a prime divide a square and miss the number you squared?"));
    if (item.id === "hero-composite-counterexample-r1") paper.append(renderArithmeticCheck());
    const stepArea = make("div", "step");
    const stepNumber = make("span", "step-kicker");
    const stepTitle = make("h3");
    stepTitle.tabIndex = -1;
    const stepBody = make("p");
    stepArea.append(stepNumber, stepTitle, stepBody);
    if (item.rejected_attempt) {
      const failure = item.rejected_attempt;
      const detail = make("details", "details");
      const summary = make("summary", "", "Read the rejected code and Lean’s error");
      const note = make("p", "", "First attempt by NVIDIA Nemotron on Nebius. The letter h stands for the fact that the divisor divides the square.");
      const errorLabel = make("p", "", "Saved Lean error excerpt");
      errorLabel.style.color = "#334958";
      detail.append(summary, note, make("pre", "", failure.candidate), errorLabel, make("pre", "", failure.lean_error_excerpt));
      stepArea.append(detail);
    }
    const controls = make("div", "step-controls");
    const previous = make("button", "", "← Previous step"); previous.type = "button"; previous.disabled = step === 0;
    const next = make("button", "", "Next step →"); next.type = "button"; next.disabled = step === stepsForCase.length - 1;
    controls.append(previous, next); stepArea.append(controls); paper.append(stepArea); reader.append(paper);

    const side = make("aside", "side");
    const overview = make("section", "side-card");
    overview.append(make("h3", "", "Try the next question"));
    const nextCase = make("a", "next-question", composite ? "What if the divisor must be prime? →" : "How does this help prove that √2 is irrational? →");
    nextCase.href = composite ? caseHref("hero-prime-divisibility-r1") : "/cases.html#sqrt2-child";
    overview.append(nextCase);
    const links = make("div", "case-links");
    if (item.previous_case) {
      const link = make("a", "", "← Checked parent lemma"); link.href = caseHref(item.previous_case); links.append(link);
    }
    if (item.next_case && caseMap.has(item.next_case)) {
      const link = make("a", "", "Open the related saved case →"); link.href = caseHref(item.next_case); links.append(link);
    }
    overview.append(links); side.append(overview);

    const evidence = make("details", "side-card source-notes");
    evidence.append(make("summary", "", "Exact statement and saved evidence"), make("p", "", item.statement), make("p", "", item.math), make("p", "", item.note));
    const evidenceList = make("div", "evidence-list");
    const locations = item.id === "hero-composite-counterexample-r1"
      ? [{ label: "Saved exact-integer check", path: "proofs/first-rung/evidence/composite-counterexample-r1/" }]
      : [
          { label: "Lean theorem source", path: "proofs/first-rung/MathCasePrimeInfiniteDescent.lean" },
        ];
    locations.forEach(record => {
      const itemLocation = make("div", "evidence-location");
      itemLocation.append(make("strong", "", record.label), make("code", "", record.path));
      const isDirectory = record.path.endsWith("/");
      const target = isDirectory ? "tree/main/" + record.path.slice(0, -1) : "blob/main/" + record.path;
      const link = make("a", "", "Open this repository location ↗");
      link.href = "https://github.com/DarthCeltic/MathCase/" + target;
      link.target = "_blank"; link.rel = "noopener noreferrer";
      itemLocation.append(link);
      evidenceList.append(itemLocation);
    });
    evidence.append(evidenceList);
    if (item.proof) {
      const detail = make("details", "details");
      detail.append(make("summary", "", "Exact saved Lean proof"));
      detail.append(make("pre", "", item.proof), make("div", "hash", "Proof SHA-256 " + item.proof_sha256));
      evidence.append(detail);
    }
    side.append(evidence); reader.append(side); host.append(reader);
    function showStep(index, moveFocus) {
      step = index;
      position.set(id, step);
      stepNumber.textContent = `Step ${step + 1} of ${stepsForCase.length}`;
      stepTitle.textContent = stepsForCase[step].title;
      stepBody.textContent = stepsForCase[step].body;
      previous.disabled = step === 0;
      next.disabled = step === stepsForCase.length - 1;
      if (moveFocus) stepTitle.focus();
    }
    previous.addEventListener("click", () => showStep(step - 1, true));
    next.addEventListener("click", () => showStep(step + 1, true));
    showStep(step, false);
  }


  function renderArithmeticCheck() {
    const panel=make("section","arithmetic-check");
    panel.setAttribute("aria-labelledby","arithmetic-title");
    const title=make("h3","","Try an exact integer example"); title.id="arithmetic-title";
    panel.append(title,make("p","arithmetic-note","Choose two numbers to see whether the divisor fits into the square and the original number."));
    const form=make("form","arithmetic-form"); form.noValidate=true;
    const dLabel=make("label","arithmetic-field","Divisor d"), dInput=make("input","arithmetic-input");
    dInput.type="text"; dInput.inputMode="numeric"; dInput.autocomplete="off"; dInput.maxLength=30; dInput.value="4"; dLabel.append(dInput);
    const nLabel=make("label","arithmetic-field","Number n"), nInput=make("input","arithmetic-input");
    nInput.type="text"; nInput.inputMode="numeric"; nInput.autocomplete="off"; nInput.maxLength=30; nInput.value="2"; nLabel.append(nInput);
    const check=make("button","arithmetic-button","Check example"); check.type="submit";
    form.append(dLabel,nLabel,check);
    const output=make("div","arithmetic-output"); output.setAttribute("aria-live","polite"); output.setAttribute("role","status");
    panel.append(form,output);
    function evaluate() {
      output.replaceChildren();
      const ds=dInput.value.trim(), ns=nInput.value.trim(), valid=x=>x.length>0 && x.length<=30 && /^[0-9]+$/.test(x);
      if(!valid(ds)||!valid(ns)){output.className="arithmetic-output error";output.textContent="Enter whole numbers using digits only (up to 30 digits).";return;}
      const d=BigInt(ds), n=BigInt(ns);
      if(d===0n){output.className="arithmetic-output error";output.textContent="Divisor d must be positive.";return;}
      const square=n*n, sr=square%d, nr=n%d;
      output.className="arithmetic-output";
      const equation=make("p","arithmetic-equations",n+" × "+n+" = "+square+". Dividing "+square+" by "+d+" leaves "+sr+" over. Dividing "+n+" by "+d+" leaves "+nr+" over.");
      const verdict=make("p","arithmetic-verdict");
      if(sr===0n && nr!==0n){verdict.textContent="Counterexample: "+d+" divides "+n+"², but "+d+" does not divide "+n+".";output.classList.add("counterexample");}
      else if(sr===0n) verdict.textContent="This example fits the claim; one example does not prove it.";
      else verdict.textContent="The premise is false for this example, so it is not a counterexample.";
      output.append(equation,verdict);
    }
    form.addEventListener("submit",event=>{event.preventDefault();evaluate();});
    evaluate(); return panel;
  }

  async function renderTavily() {
    const host = byId("tavily-body");
    const t = data.tavily;
    host.append(make("p", "", `${t.note} The saved record reports ${t.result_count} results on ${t.completed_at_utc}.`));
    host.append(make("p", "", "Query: " + t.query));
    host.append(make("p", "", "Saved file location: " + t.path + " and saved-demo/tavily-sources.json. This was a separate related-work search, not an input to the proof."));
    const status = make("p", "", "Reading six saved source locators…");
    host.append(status);
    try {
      const response = await fetch("/saved-demo/tavily-sources.json", { credentials: "omit", cache: "no-store" });
      if (!response.ok) throw new Error("Saved source locators unavailable");
      const bytes = await response.arrayBuffer();
      const digest = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)), value => value.toString(16).padStart(2, "0")).join("");
      if (digest !== "0149da99e1d6f7c7e09019f731d582173d47e52fef5bc5fbf71225846df8ff81") throw new Error("Saved source locator digest mismatch");
      const record = JSON.parse(new TextDecoder().decode(bytes));
      if (record.schema_version !== "mathcase-tavily-source-locators-v1" || record.case_id !== t.case_id ||
          record.completed_at_utc !== t.completed_at_utc || record.result_count !== 6 ||
          record.original_redacted_receipt_sha256 !== "20903a9efd69bd3c02a527be254f2a2a27d11fbe176a9287ca0fe903e0ae6bb9" ||
          record.source_content_included !== false || record.proof_input !== false ||
          !Array.isArray(record.sources) || record.sources.length !== 6) throw new Error("Saved source locator binding mismatch");
      const cards = make("div", "tavily-sources");
      record.sources.forEach((source, index) => {
        const url = new URL(source.url);
        if (source.rank !== index + 1 || typeof source.title !== "string" || !source.title ||
            url.protocol !== "https:" || url.username || url.password) throw new Error("Invalid saved source locator");
        const card = make("article", "tavily-source");
        const anchor = make("a", "", source.title);
        anchor.href = url.href; anchor.target = "_blank"; anchor.rel = "noopener noreferrer";
        card.append(make("span", "", `Saved result ${index + 1} · ${url.hostname}`), anchor);
        cards.append(card);
      });
      status.textContent = "Six saved result titles and URLs from the separate addition search. No excerpts or page text are included; these were not proof inputs.";
      host.append(cards);
    } catch {
      status.textContent = "Saved source links could not be verified. The source-free receipt summary remains available.";
    }
  }

  void renderTavily();
  renderCase();
  addEventListener("hashchange", renderCase);
})();
