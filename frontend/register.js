const registerForm = document.querySelector("#registerForm");
const name_input = document.querySelector("#name-ip");
const email_input = document.querySelector("#email-ip");
const password_input = document.querySelector("#password-ip");
const confirm_password_input = document.querySelector("#confirm-password-ip");
const registerError = document.querySelector("#registerError");
const togglePasswordBtn = document.querySelector("#togglePasswordBtn");
const eyeIcon = document.querySelector("#eyeIcon");

if (togglePasswordBtn) {
  togglePasswordBtn.addEventListener("click", () => {
    const isPassword = password_input.type === "password";
    password_input.type = isPassword ? "text" : "password";
    if (isPassword) {
      eyeIcon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>';
    } else {
      eyeIcon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>';
    }
  });
}

registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = email_input.value.trim();
    const password = password_input.value;
    const confirmPassword = confirm_password_input.value;

    if (!email || !password || !confirmPassword) {
        registerError.style.display = "block";
        registerError.textContent = "Please fill all fields.";
        return;
    }

    if (password !== confirmPassword) {
        registerError.style.display = "block";
        registerError.textContent = "Passwords do not match!";
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/users/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        }); 

        const data = await response.json();

        if (!response.ok) {
            registerError.style.display = "block";
            registerError.textContent = data.detail || "Registration failed";
            return;
        }

        // According to instructions: Log them in immediately after successful registration
        // (For Google users we handle it backend. For email/password we can fetch login)
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);
        
        const loginResponse = await fetch("http://127.0.0.1:8000/login/", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: formData.toString()
        });

        if (loginResponse.ok) {
            const loginData = await loginResponse.json();
            localStorage.setItem("access_token", loginData.access_token);
            localStorage.setItem("refresh_token", loginData.refresh_token);
            window.location.href = "./expense_tracker.html";
        } else {
            window.location.href = "./expense_login.html";
        }
    } catch(error) {
        registerError.style.display = "block";
        registerError.textContent = "Network Issue Occurred";    
    }
});
