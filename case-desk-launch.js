/* Public homepage links into the saved, read-only Case Desk. */
(() => {
  "use strict";
  const allowed = new Set(["hero-composite-counterexample-r1", "hero-prime-divisibility-r1"]);
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
