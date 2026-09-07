
const loginForm =document.querySelector("#loginForm");

const emailInput=document.querySelector("#email");
const passwordInput=document.querySelector("#password");

const loginError= document.querySelector("#loginError");

const togglePasswordBtn = document.querySelector("#togglePasswordBtn");
const eyeIcon = document.querySelector("#eyeIcon");


loginForm.addEventListener("submit", async (event) => {
  //submit button click
  //-> page reloads
  //-> form data browser apne way se submit karta 

  //But we want this instead so we use prevent
  //   submit button click
  // → page reload na ho
  // → JavaScript runs
  // → fetch() se FastAPI /login/ call ho
  // → response handle karein
  event.preventDefault();

  const email=emailInput.value.trim();
  const password=passwordInput.value;

  //URLSearchParams() is a built-in JavaScript object used to make form-style data like: username=abc@gamil.com&password=1234. As our backend login function take input like this
  const formData=new URLSearchParams();

  formData.append("username",email);
  formData.append("password",password);
  
  const response= await fetch("http://127.0.0.1:8000/login/",{
    method:"POST",
    headers:{
      "Content-Type":"application/x-www-form-urlencoded",
    },
    body:formData.toString()
  });
  const data=await response.json();
  if (!response.ok) {
  loginError.style.display = "block";
  loginError.textContent = data.detail || "Login failed";
  return;
}
  localStorage.setItem("access_token",data.access_token);
  localStorage.setItem("refresh_token",data.refresh_token);

  window.location.href = "./expense_tracker.html";
});

if (togglePasswordBtn) {
  togglePasswordBtn.addEventListener("click", () => {
    const isPassword = passwordInput.type === "password";
    passwordInput.type = isPassword ? "text" : "password";
    if (isPassword) {
      eyeIcon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>';
    } else {
      eyeIcon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>';
    }
  });
}