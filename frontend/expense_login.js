
const loginForm =document.querySelector("#loginForm");
const emailInput=document.querySelector("#email");
const passwordInput=document.querySelector("#password");
const loginError= document.querySelector("#loginError");

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