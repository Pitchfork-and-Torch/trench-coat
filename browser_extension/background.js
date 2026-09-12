// Minimal service worker — future: poll /api/identity for toolbar badge.
chrome.runtime.onInstalled.addListener(() => {
  console.log("Trench Coat companion installed");
});
