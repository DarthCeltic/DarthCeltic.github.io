/* Public homepage links into the saved, read-only Case Desk. */
(() => {
  "use strict";
  const allowed = new Set(["hero-composite-counterexample-r1", "hero-prime-divisibility-r1"]);
  const hash = window.location.hash;
  if (hash.startsWith("#case/")) {
    let route;
    try { route = decodeURIComponent(hash.slice(1)); } catch { route = hash.slice(1); }
    const match = /^case\/([a-z0-9-]+)(?:\/(.*))?$/i.exec(route);
    if (match) {
      const id = match[1].toLowerCase();
      if (id === "hero-sqrt2-parent-reuse-r2") {
        window.location.replace(new URL("cases.html#sqrt2-child", window.location.href).href);
        return;
      }
      const suffix = match[2] ? "/" + match[2] : "";
      const target = new URL("reader.html?scope=public", window.location.href);
      target.hash = "case/" + encodeURIComponent(id) + suffix;
      window.location.replace(target.href);
      return;
    }
  }
  document.querySelectorAll("[data-case-desk-launch]").forEach(link => {
    const caseId = link.getAttribute("data-case-desk-launch");
    if (!allowed.has(caseId)) {
      link.removeAttribute("href");
      link.setAttribute("aria-disabled", "true");
      return;
    }
    const target = new URL("reader.html?scope=public", window.location.href);
    target.hash = "case/" + encodeURIComponent(caseId);
    link.href = target.href;
  });
})();
