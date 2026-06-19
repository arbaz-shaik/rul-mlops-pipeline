import { useState } from "react";



const Cond1=()=>{

   const [flag, setFlag]= useState (true);
const [msg1,setMsg1]= useState(`hello`);
const [msg2,setMsg2]=useState(`hell no`);

   const clickMe=()=>{

      setFlag (flag=>!flag)

   }

 return(

    <>
    {
      flag? <h1>{msg2}</h1> : <h1>{msg1}</h1>
    }

    <br></br>

    <button onClick={clickMe}>click me</button>
    </>
 )


}
export default Cond1;