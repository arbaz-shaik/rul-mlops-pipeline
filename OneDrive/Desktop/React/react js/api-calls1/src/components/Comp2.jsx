import axios from "axios";
import { useRef, useState } from "react";


const Comp2=()=>{
    const ref1 = useRef(null);
    const ref2 = useRef(null);
    
    const [msg, setMsg]= useState({});
    const demo_func = async ()=>{
        const res = await axios.post("https://reqres.in/api/register",{
            "email":ref1.current.value,"password":ref1.current.value
        });
        const {data}= res;
        setMsg (data);
    
    }
    
    
    const post_ex =()=>{
        demo_func();
    }
    



    return(
        <>
        <fieldset>
            <legend>
              post request example
            </legend>
            <input type="email" ref={ref1} placeholder="enter email"></input>
            <br></br><br></br>
            <input type="password" ref={ref2} placeholder="enter email"></input>
            <br></br><br></br>
            <button onClick={post_ex}>Send</button>
            <br></br><br></br>
            <p>{JSON.stringify(msg)}</p>
        </fieldset>
        </>
    )
}
export default Comp2;