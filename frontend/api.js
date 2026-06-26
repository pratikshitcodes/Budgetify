const API_BASE = "http://127.0.0.1:8000";
async function apiFetch(url,options={}) {
    const token=localStorage.getItem("access_token");
    options.headers={
        //...options.headers means take all existing headers already inside 
        // options.headers, then add the Authorization
        ...options.headers,
        Authorization:`Bearer ${token}`
    }
    const response=await fetch(API_BASE+url,options);
    if(response.status===401){
        if(await tryRefresh()){
            const new_token=localStorage.getItem("access_token");
                    options.headers={
                ...options.headers,
                Authorization:`Bearer ${new_token}`
            }
            const response=await fetch(API_BASE+url,options);
            return response;
        }
        else{
            window.location.href="./expense_login.html";
            return ;
        }

    }
    return response;
}
async function tryRefresh(){
    const refresh_token=localStorage.getItem("refresh_token");
    console.log("refresh token:", refresh_token) 
    if(!refresh_token){
        return false;
    }
    try{
        const Response=await fetch(API_BASE+"/login/refresh_token",{
        method:"POST",
        headers:{
            Authorization:`Bearer ${refresh_token}`
        },
    });

    const data=await Response.json();
    localStorage.setItem("access_token",data.new_access_token);
    return true;
    }
    catch(error){
        console.log("refresh error:",error);
        return false;
    }
}