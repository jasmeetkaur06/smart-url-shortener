// Session history (stored in memory)
const history = [];

async function shortenURL() {
  const input   = document.getElementById("urlInput");
  const btn     = document.getElementById("shortenBtn");
  const errorBox  = document.getElementById("errorBox");
  const resultBox = document.getElementById("resultBox");

  const url = input.value.trim();

  // Reset UI
  errorBox.classList.add("hidden");
  resultBox.classList.add("hidden");

  if (!url) {
    showError("Please paste a URL first.");
    return;
  }

  // Loading state
  btn.textContent = "Shortening...";
  btn.disabled = true;

  try {
    const res = await fetch("/shorten", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });

    const data = await res.json();

    if (!res.ok) {
      showError(data.error || "Something went wrong.");
      return;
    }

    // Show result
    const shortLink     = document.getElementById("shortLink");
    const analyticsLink = document.getElementById("analyticsLink");

    shortLink.textContent = data.short_url;
    shortLink.href        = data.short_url;
    analyticsLink.href    = `/analytics/${data.code}`;

    resultBox.classList.remove("hidden");

    // Add to session history
    addToHistory(url, data.short_url, data.code);
    input.value = "";

  } catch (err) {
    showError("Network error. Is Flask running?");
  } finally {
    btn.textContent = "Shorten It →";
    btn.disabled = false;
  }
}

function copyURL() {
  const link = document.getElementById("shortLink").textContent;
  navigator.clipboard.writeText(link).then(() => {
    const btn = event.target;
    btn.textContent = "Copied!";
    setTimeout(() => btn.textContent = "Copy", 2000);
  });
}

function showError(msg) {
  const box = document.getElementById("errorBox");
  box.textContent = msg;
  box.classList.remove("hidden");
}

function addToHistory(original, shortURL, code) {
  history.push({ original, shortURL, code });

  const section = document.getElementById("historySection");
  const tbody   = document.getElementById("historyBody");

  section.classList.remove("hidden");

  const row = document.createElement("tr");
  row.innerHTML = `
    <td title="${original}">${original}</td>
    <td><a href="${shortURL}" target="_blank">${shortURL}</a></td>
    <td><a href="/analytics/${code}">📊 View</a></td>
  `;
  tbody.prepend(row);
}

// Allow pressing Enter to shorten
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("urlInput")
    .addEventListener("keydown", e => {
      if (e.key === "Enter") shortenURL();
    });
});