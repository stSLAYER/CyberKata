"use strict";

const levels = {
  1: {
    title: "PASSWORD HUNT",
    eyebrow: "LEVEL 01 // KNOWN USER",
    mission:
      "The account name is known, but the password is not. Use the supplied password list to find the one value that opens this gate.",
    endpoint: "/api/login/1",
    wordlists: "wordlists/passwords.txt",
    knownUsername: "kata",
    knownPassword: "",
    intel: [
      ["USERNAME", "kata"],
      ["PASSWORD", "UNKNOWN"],
      ["FAILURE TEXT", "ACCESS_DENIED"],
      ["HYDRA INPUTS", "-l + -P"],
    ],
    hints: [
      "Use lowercase -l when you already know one username.",
      "Use uppercase -P to load many candidate passwords from a file.",
      "The form module needs the path, the username/password fields, and F=ACCESS_DENIED as its failure condition.",
    ],
  },
  2: {
    title: "FIND THE USER",
    eyebrow: "LEVEL 02 // KNOWN PASSWORD",
    mission:
      "A password has leaked, but nobody knows which account owns it. Test the username list while keeping the known password fixed.",
    endpoint: "/api/login/2",
    wordlists: "wordlists/usernames.txt",
    knownUsername: "",
    knownPassword: "dojo-pass",
    intel: [
      ["USERNAME", "UNKNOWN"],
      ["PASSWORD", "dojo-pass"],
      ["FAILURE TEXT", "UNKNOWN_OPERATOR"],
      ["HYDRA INPUTS", "-L + -p"],
    ],
    hints: [
      "Uppercase -L tells Hydra to read usernames from a file.",
      "Lowercase -p supplies one known password directly on the command line.",
      "The POST body still uses username=^USER^&password=^PASS^ even when one value is fixed.",
    ],
  },
  3: {
    title: "CREDENTIAL STORM",
    eyebrow: "LEVEL 03 // TWO WORDLISTS",
    mission:
      "Neither side of the credential pair is known. Combine both supplied lists, control concurrency, and stop after the first valid pair.",
    endpoint: "/api/login/3",
    wordlists: "wordlists/usernames.txt + wordlists/passwords.txt",
    knownUsername: "",
    knownPassword: "",
    intel: [
      ["USERNAME", "UNKNOWN"],
      ["PASSWORD", "UNKNOWN"],
      ["FAILURE TEXT", "INVALID_CREDENTIAL_PAIR"],
      ["EXTRA FLAGS", "-t 4 + -f"],
    ],
    hints: [
      "Combine uppercase -L and uppercase -P to test two files.",
      "Use -t 4 for a controlled beginner-friendly task count, and -f to stop after a valid pair is found.",
      "Your failure condition is F=INVALID_CREDENTIAL_PAIR. Keep the condition at the end of the module string.",
    ],
  },
  4: {
    title: "READ THE RESPONSE",
    eyebrow: "LEVEL 04 // RESPONSE LOGIC",
    mission:
      "Failures return HTTP 200, but success returns HTTP 302 and redirects into a protected vault. Define what success looks like instead of trusting the page design.",
    endpoint: "/api/login/4",
    wordlists: "wordlists/usernames.txt + wordlists/passwords.txt",
    knownUsername: "",
    knownPassword: "",
    intel: [
      ["FAILURE STATUS", "200 OK"],
      ["SUCCESS STATUS", "302 REDIRECT"],
      ["SUCCESS TEXT", "HYDRA_DOJO_COMPLETE"],
      ["CONDITION", "S= SUCCESS MATCH"],
    ],
    hints: [
      "Use your browser developer tools or curl -i to compare a failed response with a successful one.",
      "Hydra can classify a login by searching the response for a success string with S=.",
      "After the redirect, the vault contains HYDRA_DOJO_COMPLETE. Use S=HYDRA_DOJO_COMPLETE as the final condition.",
    ],
  },
};

const storageKey = "cyberkata-hydra-dojo-progress-v1";
const dialog = document.querySelector("#levelDialog");
const dialogClose = document.querySelector("#dialogClose");
const missionText = document.querySelector("#missionText");
const intelGrid = document.querySelector("#intelGrid");
const endpointText = document.querySelector("#endpointText");
const wordlistText = document.querySelector("#wordlistText");
const manualLoginForm = document.querySelector("#manualLoginForm");
const usernameInput = document.querySelector("#usernameInput");
const passwordInput = document.querySelector("#passwordInput");
const responseConsole = document.querySelector("#responseConsole");
const copyEndpoint = document.querySelector("#copyEndpoint");

let activeLevel = 1;
let completed = loadProgress();

function loadProgress() {
  try {
    const parsed = JSON.parse(localStorage.getItem(storageKey) || "[]");
    return new Set(parsed.filter((value) => ["1", "2", "3", "4"].includes(String(value))).map(String));
  } catch {
    return new Set();
  }
}

function saveProgress() {
  localStorage.setItem(storageKey, JSON.stringify([...completed]));
}

function markComplete(levelId) {
  completed.add(String(levelId));
  saveProgress();
  renderProgress();
}

function renderProgress() {
  const count = completed.size;
  const percent = Math.round((count / 4) * 100);
  document.querySelector("#progressHeader").textContent = `${count} / 4 CLEARED`;
  document.querySelector("#progressPercent").textContent = `${percent}%`;
  document.querySelector("#progressBar").style.width = `${percent}%`;

  document.querySelectorAll("[data-card-level]").forEach((card) => {
    const isComplete = completed.has(card.dataset.cardLevel);
    card.classList.toggle("is-complete", isComplete);
    card.querySelector(".level-status").textContent = isComplete ? "CLEARED ✓" : "AVAILABLE";
  });
}

function openLevel(levelId) {
  const level = levels[levelId];
  activeLevel = Number(levelId);
  document.querySelector("#dialogEyebrow").textContent = level.eyebrow;
  document.querySelector("#dialogTitle").textContent = level.title;
  document.querySelector("#levelBadge").textContent = `NODE_0${levelId}`;
  missionText.textContent = level.mission;
  endpointText.textContent = level.endpoint;
  wordlistText.textContent = level.wordlists;
  document.querySelector("#hint1").textContent = level.hints[0];
  document.querySelector("#hint2").textContent = level.hints[1];
  document.querySelector("#hint3").textContent = level.hints[2];

  intelGrid.replaceChildren(
    ...level.intel.map(([label, value]) => {
      const item = document.createElement("div");
      item.className = "intel-item";
      const name = document.createElement("span");
      name.textContent = label;
      const detail = document.createElement("strong");
      detail.textContent = value;
      item.append(name, detail);
      return item;
    }),
  );

  usernameInput.value = level.knownUsername;
  passwordInput.value = level.knownPassword;
  responseConsole.className = "";
  responseConsole.textContent = "> waiting for credentials_";
  dialog.querySelectorAll("details").forEach((details) => {
    details.open = false;
  });
  dialog.showModal();
  (level.knownUsername ? passwordInput : usernameInput).focus();
}

async function submitManualLogin(event) {
  event.preventDefault();
  const level = levels[activeLevel];
  const body = new URLSearchParams({
    username: usernameInput.value,
    password: passwordInput.value,
  });

  responseConsole.className = "";
  responseConsole.textContent = "> sending credentials...";

  try {
    const response = await fetch(level.endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    const text = await response.text();
    const success = text.includes("ACCESS_GRANTED") || text.includes("HYDRA_DOJO_COMPLETE");
    responseConsole.className = success ? "success" : "failure";
    responseConsole.textContent = `> HTTP ${response.status}\n${text.trim()}`;
    if (success) {
      markComplete(activeLevel);
    }
  } catch (error) {
    responseConsole.className = "failure";
    responseConsole.textContent = `> connection error\n${error.message}`;
  }
}

async function syncServerProgress() {
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    if (!response.ok) return;
    const status = await response.json();
    let changed = false;
    for (const levelId of status.completed || []) {
      if (!completed.has(String(levelId))) {
        completed.add(String(levelId));
        changed = true;
      }
    }
    if (changed) {
      saveProgress();
      renderProgress();
    }
  } catch {
    // The status indicator is optional; the lab still works without polling.
  }
}

document.querySelectorAll("[data-open-level]").forEach((button) => {
  button.addEventListener("click", () => openLevel(button.dataset.openLevel));
});

dialogClose.addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});
manualLoginForm.addEventListener("submit", submitManualLogin);

copyEndpoint.addEventListener("click", async () => {
  const value = endpointText.textContent;
  try {
    await navigator.clipboard.writeText(value);
    copyEndpoint.textContent = "COPIED";
    setTimeout(() => {
      copyEndpoint.textContent = "COPY";
    }, 1100);
  } catch {
    copyEndpoint.textContent = "SELECT";
  }
});

const displayedTarget = window.location.host || "127.0.0.1:8080";
const commandHost = window.location.hostname || "127.0.0.1";
const commandPort = window.location.port || "8080";
document.querySelectorAll(".target-value").forEach((element) => {
  element.textContent = displayedTarget;
});

document.querySelectorAll("[data-command-template]").forEach((element) => {
  element.textContent = element.dataset.commandTemplate
    .replaceAll("{HOST}", commandHost)
    .replaceAll("{PORT}", commandPort);
});

document.querySelectorAll("[data-copy-command]").forEach((button) => {
  button.addEventListener("click", async () => {
    const command = button.closest(".recipe-card")?.querySelector("[data-command-template]")?.textContent;
    if (!command) return;

    try {
      await navigator.clipboard.writeText(command);
      button.textContent = "COPIED ✓";
      setTimeout(() => {
        button.textContent = "COPY";
      }, 1200);
    } catch {
      button.textContent = "SELECT";
    }
  });
});

renderProgress();
syncServerProgress();
setInterval(syncServerProgress, 1800);
