(() => {
  const form = document.getElementById("ramsey66-inspect-form");
  const input = document.getElementById("ramsey66-vertex");
  const status = document.getElementById("ramsey66-status");
  const result = document.getElementById("ramsey66-result");
  if (!form || !input || !status || !result) return;
  const url = "evidence/finite-graphs/ramsey-r66-paley101/graph-certificate.json";
  const expectedSha256 = "330196fd61554c66c7a3305a8257ea0a33b1b2722da95750819271438289073e";
  let cached = null;
  async function loadCertificate() {
    if (cached) return cached;
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) throw new Error(`Certificate request failed (${response.status}).`);
    const bytes = await response.arrayBuffer();
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    const actual = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, "0")).join("");
    if (actual !== expectedSha256) throw new Error("The certificate hash does not match the published receipt.");
    const cert = JSON.parse(new TextDecoder().decode(bytes));
    if (cert.schema !== "mathcase-simple-graph-certificate-v1" || cert.vertices !== 101 || !Array.isArray(cert.edges) || cert.edges.length !== 2525) throw new Error("The certificate metadata is inconsistent.");
    const neighbors = Array.from({ length: 101 }, () => []);
    for (const pair of cert.edges) {
      if (!Array.isArray(pair) || pair.length !== 2 || !Number.isInteger(pair[0]) || !Number.isInteger(pair[1]) || pair[0] < 0 || pair[0] >= pair[1] || pair[1] >= 101) throw new Error("The edge list contains an invalid pair.");
      neighbors[pair[0]].push(pair[1]);
      neighbors[pair[1]].push(pair[0]);
    }
    if (neighbors.some((row) => row.length !== 50)) throw new Error("The degree check did not pass.");
    cached = { cert, neighbors };
    return cached;
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    status.textContent = "Checking the certificate hash and degree sequence…";
    status.dataset.state = "working";
    result.replaceChildren();
    try {
      const vertex = Number(input.value);
      if (!Number.isInteger(vertex) || vertex < 0 || vertex >= 101) throw new Error("Enter a whole vertex number from 0 through 100.");
      const { neighbors } = await loadCertificate();
      const list = document.createElement("p");
      list.textContent = `Vertex ${vertex} has degree 50. Its neighbors are ${neighbors[vertex].join(", ")}.`;
      result.append(list);
      status.textContent = `Certificate SHA-256 and all 101 degrees verified. This is an adjacency display, not the exhaustive Ramsey check.`;
      status.dataset.state = "passed";
    } catch (error) {
      status.textContent = error instanceof Error ? error.message : "The certificate could not be checked.";
      status.dataset.state = "failed";
    }
  });
})();
