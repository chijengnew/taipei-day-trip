const authEntry = document.getElementById("auth-entry");
const authDialog = document.getElementById("auth-dialog");
const signinPanel = document.getElementById("signin-panel");
const signupPanel = document.getElementById("signup-panel");
const toSignup = document.getElementById("to-signup");
const toSignin = document.getElementById("to-signin");

const signinEmail = document.getElementById("signin-email");
const signinPassword = document.getElementById("signin-password");
const signinSubmit = document.getElementById("signin-submit");
const signinMessage = document.getElementById("signin-message");

const signupName = document.getElementById("signup-name");
const signupEmail = document.getElementById("signup-email");
const signupPassword = document.getElementById("signup-password");
const signupSubmit = document.getElementById("signup-submit");
const signupMessage = document.getElementById("signup-message");

function openDialog() {
  showSigninForm();
  authDialog.classList.add("is-open");
}

function closeDialog() {
  authDialog.classList.remove("is-open");
  clearMessages();
}

function clearMessages() {
  hideMessage(signinMessage);
  hideMessage(signupMessage);
}

function showMessage(element, text, type) {
  element.textContent = text;
  element.classList.remove("dialog__message--error", "dialog__message--success");
  element.classList.add(type === "success" ? "dialog__message--success" : "dialog__message--error");
  element.hidden = false;
}

function hideMessage(element) {
  element.textContent = "";
  element.hidden = true;
}

function showSigninForm() {
  signupPanel.hidden = true;
  signinPanel.hidden = false;
  clearMessages();
}

function showSignupForm() {
  signinPanel.hidden = true;
  signupPanel.hidden = false;
  clearMessages();
}

function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function getToken() {
  return localStorage.getItem("token");
}

async function fetchCurrentUser() {
  const token = getToken();
  if (!token) {
    return null;
  }
  try {
    const response = await fetch("/api/user/auth", {
      headers: { "Authorization": "Bearer " + token },
    });
    const result = await response.json();
    return result.data;
  } catch (error) {
    return null;
  }
}

async function renderAuthEntry() {
  const user = await fetchCurrentUser();
  if (user) {
    authEntry.textContent = "登出系統";
    authEntry.dataset.state = "signed-in";
  } else {
    authEntry.textContent = "登入/註冊";
    authEntry.dataset.state = "signed-out";
  }
}

async function handleSignIn() {
  const email = signinEmail.value.trim();
  const password = signinPassword.value;

  if (!email || !password) {
    showMessage(signinMessage, "請填寫電子信箱與密碼", "error");
    return;
  }

  if (!isValidEmail(email)) {
    showMessage(signinMessage, "請輸入有效的電子郵件格式", "error");
    return;
  }

  try {
    const response = await fetch("/api/user/auth", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email, password: password }),
    });
    const result = await response.json();

    if (result.token) {
      localStorage.setItem("token", result.token);
      location.reload();
    } else {
      showMessage(signinMessage, result.message || "登入失敗，請稍後再試", "error");
    }
  } catch (error) {
    showMessage(signinMessage, "系統發生錯誤，請稍後再試", "error");
  }
}

async function handleSignUp() {
  const name = signupName.value.trim();
  const email = signupEmail.value.trim();
  const password = signupPassword.value;

  if (!name || !email || !password) {
    showMessage(signupMessage, "請填寫姓名、電子郵件與密碼", "error");
    return;
  }

  if (!isValidEmail(email)) {
    showMessage(signupMessage, "請輸入有效的電子郵件格式", "error");
    return;
  }

  try {
    const response = await fetch("/api/user", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name, email: email, password: password }),
    });
    const result = await response.json();

    if (result.ok) {
      signupName.value = "";
      signupEmail.value = "";
      signupPassword.value = "";
      showSigninForm();
      showMessage(signinMessage, "註冊成功，請登入", "success");
    } else {
      showMessage(signupMessage, result.message || "註冊失敗，請稍後再試", "error");
    }
  } catch (error) {
    showMessage(signupMessage, "系統發生錯誤，請稍後再試", "error");
  }
}

function handleSignOut() {
  localStorage.removeItem("token");
  location.reload();
}

authEntry.addEventListener("click", function (event) {
  event.preventDefault();
  if (authEntry.dataset.state === "signed-in") {
    handleSignOut();
  } else {
    openDialog();
  }
});

authDialog.querySelectorAll("[data-dialog-close]").forEach(function (element) {
  element.addEventListener("click", closeDialog);
});

toSignup.addEventListener("click", showSignupForm);
toSignin.addEventListener("click", showSigninForm);

signinSubmit.addEventListener("click", handleSignIn);
signupSubmit.addEventListener("click", handleSignUp);

renderAuthEntry();