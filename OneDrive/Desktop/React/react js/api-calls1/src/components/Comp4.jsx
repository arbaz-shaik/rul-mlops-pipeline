import axios from "axios"
import { useRef, useState } from "react";

const Comp4=()=>{

       const ref1 = useRef(null);
       const ref2 = useRef(null);
       const ref3 = useRef(null);
       const [ msg , setMsg] = useState({});

       const demo_func = async()=>{
        const res = await axios.put (`https://reqres.in/api/users/${ref1.current.value}`,{data :{"name": ref2.current.value,"job": ref3.current.value }} )
        const {data} = res;
        setMsg (data);
       }
        
       const func_one = () => {
        demo_func();
    }

       return(
        <>
        <fieldset>
            <legend> Put Example</legend>
            <input type="number" ref={ref1} placeholder="enter number"/>
            <br /> <br /><br />
            <input type="text" ref={ref2} placeholder="enter name"/>
            <br /> <br /><br />
            <input type="text" ref={ref3} placeholder="enter job"/>
            <br /> <br /><br />
            <button onClick={func_one}>send</button>
            <p>{JSON.stringify(msg)}</p>
        </fieldset>
        </>
       )



}
export default Comp4;