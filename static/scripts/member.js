const memberGreeting = document.getElementById("member-greeting");
const mcpUrlText = document.getElementById("mcp-url");
const mcpTokenText = document.getElementById("mcp-token");
const generateButton = document.getElementById("generate-token");
const memberMessage = document.getElementById("member-message");
const memberSignOut = document.getElementById("member-signout");

function renderMcpToken(token) {
  if (token) {
    mcpTokenText.textContent = token;
    mcpTokenText.classList.remove("member__value--empty");
  } else {
    mcpTokenText.textContent = "尚未產生金鑰";
    mcpTokenText.classList.add("member__value--empty");
  }
}

function showMemberMessage(text, type) {
  memberMessage.textContent = text;
  memberMessage.classList.toggle("member__message--error", type === "error");
  memberMessage.hidden = false;
}

async function loadMcpToken() {
  try {
    const response = await fetch("/api/member/token", {
      headers: { "Authorization": "Bearer " + getToken() },
    });
    const result = await response.json();
    renderMcpToken(result.data ? result.data.token : null);
  } catch (error) {
    showMemberMessage("金鑰載入失敗，請稍後再試", "error");
  }
}

async function handleGenerateToken() {
  generateButton.disabled = true;
  memberMessage.hidden = true;
  try {
    const response = await fetch("/api/member/token", {
      method: "POST",
      headers: { "Authorization": "Bearer " + getToken() },
    });
    const result = await response.json();

    if (result.data && result.data.token) {
      renderMcpToken(result.data.token);
      showMemberMessage("金鑰已更新，舊金鑰即刻失效，請更新 MCP 設定", "success");
    } else {
      showMemberMessage(result.message || "金鑰產生失敗，請稍後再試", "error");
    }
  } catch (error) {
    showMemberMessage("系統發生錯誤，請稍後再試", "error");
  } finally {
    generateButton.disabled = false;
  }
}

function handleMemberSignOut() {
  localStorage.removeItem("token");
  window.location.href = "/";
}

async function initMemberPage() {
  const user = await fetchCurrentUser();

  if (!user) {
    window.location.href = "/";
    return;
  }

  memberGreeting.textContent = "您好，" + user.name + "：";
  mcpUrlText.textContent = window.location.origin + "/mcp/";
  await loadMcpToken();
}

generateButton.addEventListener("click", handleGenerateToken);
memberSignOut.addEventListener("click", handleMemberSignOut);

initMemberPage();