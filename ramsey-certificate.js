(() => {
  const button = document.getElementById("ramsey-verify");
  const status = document.getElementById("ramsey-status");
  const result = document.getElementById("ramsey-result");
  if (!button || !status || !result) return;

  const certificateUrl = "evidence/finite-graphs/ramsey-r55/exoo42-derived.graph6";
  const expectedSha256 = "0d855016014ce4c2fbfcdba270683086a351b4a1e59afd611cc53e9b15109da7";
  const expectedVertices = 42;
  const expectedSubsets = 850668;

  function setStatus(message, state) {
    status.textContent = message;
    status.dataset.state = state;
  }

  function binomial(n, k) {
    let value = 1;
    for (let i = 1; i <= k; i += 1) value = (value * (n - i + 1)) / i;
    return value;
  }

  async function sha256Hex(bytes) {
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, "0")).join("");
  }

  function decodeGraph6(bytes) {
    if (bytes.length < 2 || bytes[bytes.length - 1] !== 10) {
      throw new Error("The certificate is not the pinned single-line graph6 file.");
    }
    const lineLength = bytes.length - 1;
    const n = bytes[0] - 63;
    if (n !== expectedVertices) throw new Error(`Expected 42 vertices; graph6 encodes ${n}.`);
    const bitCount = (n * (n - 1)) / 2;
    const payloadLength = Math.ceil(bitCount / 6);
    if (lineLength !== 1 + payloadLength) {
      throw new Error(`Unexpected graph6 length: expected ${1 + payloadLength} data bytes, got ${lineLength}.`);
    }

    const values = new Uint8Array(payloadLength);
    for (let i = 0; i < payloadLength; i += 1) {
      const code = bytes[i + 1] - 63;
      if (code < 0 || code > 63) throw new Error("The graph6 payload contains a byte outside its alphabet.");
      values[i] = code;
    }
    const paddingBits = payloadLength * 6 - bitCount;
    if (paddingBits > 0 && (values[payloadLength - 1] & ((1 << paddingBits) - 1)) !== 0) {
      throw new Error("The graph6 payload has nonzero padding bits.");
    }

    const adjacency = new Uint8Array(n * n);
    for (let bit = 0; bit < bitCount; bit += 1) {
      const edge = (values[Math.floor(bit / 6)] >> (5 - (bit % 6))) & 1;
      let left = 0;
      let remaining = bit;
      while (remaining >= n - left - 1) {
        remaining -= n - left - 1;
        left += 1;
      }
      const right = left + 1 + remaining;
      adjacency[left * n + right] = edge;
      adjacency[right * n + left] = edge;
    }
    return { n, adjacency };
  }

  function countMonochromaticFiveCliques(n, adjacency) {
    let subsets = 0;
    let redCliques = 0;
    let blueCliques = 0;
    for (let a = 0; a < n - 4; a += 1) {
      for (let b = a + 1; b < n - 3; b += 1) {
        for (let c = b + 1; c < n - 2; c += 1) {
          for (let d = c + 1; d < n - 1; d += 1) {
            for (let e = d + 1; e < n; e += 1) {
              subsets += 1;
              const vertices = [a, b, c, d, e];
              let allRed = true;
              let allBlue = true;
              for (let i = 0; i < 5; i += 1) {
                for (let j = i + 1; j < 5; j += 1) {
                  const edge = adjacency[vertices[i] * n + vertices[j]];
                  if (edge === 0) allRed = false;
                  else allBlue = false;
                }
              }
              if (allRed) redCliques += 1;
              if (allBlue) blueCliques += 1;
            }
          }
        }
      }
    }
    return { subsets, redCliques, blueCliques };
  }

  function renderResult(details, elapsedMs) {
    const card = document.createElement("section");
    card.className = "coefficient-result-card";
    const heading = document.createElement("h3");
    heading.textContent = "Finite certificate check complete";
    const summary = document.createElement("p");
    summary.textContent = `Checked ${details.subsets.toLocaleString()} five-vertex subsets; red K5 count ${details.redCliques}; blue K5 count ${details.blueCliques}. Runtime: ${elapsedMs.toFixed(1)} ms.`;
    const limit = document.createElement("p");
    limit.className = "coefficient-limit";
    limit.textContent = "This verifies one finite graph certificate. It does not prove a general Ramsey theorem, establish novelty, or constitute a Lean proof.";
    card.append(heading, summary, limit);
    result.replaceChildren(card);
  }

  button.addEventListener("click", async () => {
    button.disabled = true;
    result.replaceChildren();
    setStatus("Fetching the same-origin certificate and checking its SHA-256…", "running");
    try {
      const response = await fetch(certificateUrl, { cache: "no-store", credentials: "omit", redirect: "error" });
      if (!response.ok) throw new Error(`Certificate request returned HTTP ${response.status}.`);
      const buffer = await response.arrayBuffer();
      const bytes = new Uint8Array(buffer);
      const actualSha256 = await sha256Hex(buffer);
      if (actualSha256 !== expectedSha256) throw new Error(`SHA-256 mismatch: received ${actualSha256}.`);

      const { n, adjacency } = decodeGraph6(bytes);
      const started = performance.now();
      const counts = countMonochromaticFiveCliques(n, adjacency);
      const elapsedMs = performance.now() - started;
      const expected = binomial(n, 5);
      if (counts.subsets !== expected || counts.subsets !== expectedSubsets) {
        throw new Error(`Subset count mismatch: checked ${counts.subsets}, expected ${expected}.`);
      }
      renderResult(counts, elapsedMs);
      setStatus(`PASS — pinned SHA-256 matches; graph6 encodes ${n} vertices; all ${counts.subsets.toLocaleString()} five-vertex subsets were checked.`, "success");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown verification error.";
      setStatus(`Could not verify the certificate: ${message}`, "error");
    } finally {
      button.disabled = false;
    }
  });
})();
