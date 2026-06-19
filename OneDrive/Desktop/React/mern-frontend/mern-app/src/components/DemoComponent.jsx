import { useState } from "react";
const DemoComponent=()=>{
    
    const[obj,setObj]= useState({"uname":"", "upwd":""}) 

    const Login=()=>{
         
    }
    const func_one =(event)=>{
        setObj({...obj, [event.target.name]:event.target.value});

        
    }

    return (
        <>
        <input type="text" name="user" value={obj.uname} onChange={func_one} ></input>
        <br></br><br></br><br></br>
        <input type="password" name="pass" value={obj.up} onChange={func_one} ></input>
        <br></br><br></br><br></br>
        <button onClick={Login}>Login</button>
        
        </>
    )


}
export default DemoComponent;