// Soft fingerprint hygiene (hints only — not a full anti-detect stack).
// Runs at document_start; does not claim perfect anonymity.
(function () {
  try {
    Object.defineProperty(navigator, "webdriver", { get: () => undefined });
  } catch (_) {
    /* page may lock navigator */
  }
})();
