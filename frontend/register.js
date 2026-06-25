const email_input=document.querySelector("#email-ip");
const password_input=document.querySelector("#password-ip");
const registerError=document.querySelector(".register-error");
const submit_btn=document.querySelector(".submit-btn");

submit_btn.addEventListener("click",async (event)=>{
    event.preventDefault();

    const email=email_input.value.trim();
    const password=password_input.value;
    if(!email||!password){
        registerError.style.display="block";
        registerError.textContent="Please fill the fields first";
        return;
    }
    try{
        const response=await fetch("http://127.0.0.1:8000/users/",{
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({email,password})
        }); 

        const data=await response.json();

        if(!response.ok){
            registerError.style.display="block";
            registerError.textContent=data.detail||"Registration failed";
            return ;
        }
        window.location.href = "./expense_login.html";
    }
    catch(error){
        alert("Network Issue Occured");    
    }
});