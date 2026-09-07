import re

with open('expense_login.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Replace the old showPassword selection
js = re.sub(
    r'const showPasswordBtn\s*=\s*document\.querySelector\(\"#showPassword\"\);',
    'const togglePasswordBtn = document.querySelector("#togglePasswordBtn");\nconst eyeIcon = document.querySelector("#eyeIcon");',
    js
)
js = re.sub(
    r'const showText\s*=\s*document\.querySelector\(\"\.show-class span\"\);',
    '',
    js
)

# Replace the event listener
old_listener = '''showPasswordBtn.addEventListener("change",()=>{
  const isChecked= showPasswordBtn.checked;

  passwordInput.type=isChecked?"text":"password";
  showText.textContent=isChecked?"Hide":"Show";
})'''

new_listener = '''if (togglePasswordBtn) {
  togglePasswordBtn.addEventListener("click", () => {
    const isPassword = passwordInput.type === "password";
    passwordInput.type = isPassword ? "text" : "password";
    if (isPassword) {
      eyeIcon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line>';
    } else {
      eyeIcon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>';
    }
  });
}'''

js = js.replace(old_listener, new_listener)

with open('expense_login.js', 'w', encoding='utf-8') as f:
    f.write(js)
