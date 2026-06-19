import { useRef } from "react";
import{ useNavigate } from "react-router-dom";
const Login =()=>{

    const ref1= useRef(null);
    const ref2= useRef(null);
    const navigate= useNavigate();
    const login =()=>{
        ref1.current.value == "ExcelR" && ref2.current.value=="abc@123"?
        navigate("/dashboard"): navigate("/error")
    }


    return(
        <>



        <input type="text" ref={ref1} placeholder="enter username"/>
        <br></br> <br></br> <br></br>
        <input type="password" ref={ref2}  placeholder="password"/>
        <br></br> <br></br> 
        <button onClick={login}>Login</button>
        <br></br> <br></br> <br></br>  


        </>
    )

}
export default Login;