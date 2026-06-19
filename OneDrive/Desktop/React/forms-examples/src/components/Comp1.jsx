import React from 'react'
import { useState } from 'react'



const Comp1 = () => {

    const [data, setData]= useState ({"uname":""})
    const [errors, setErrors]= useState({})
    const func =(event)=>{
        setData({...data,[event.target.name]:event.target.value})
    }
    const register = (event)=>{
        event.preventDefault();
        if (validate()) {

            console.log("errors not found")
            
        }
        else{
            console.log("eroros are here baby")
        }
      
        console.log(data)
    }

    const validate =()=>{
        let formError={};
        if (!data.uname){
            formError.uname="user name cannot left empty"
        }

        setErrors (formError);
        return Object.keys(formError).length ===0;
    }

  return (
  <>
 
 <form onSubmit={register}>
    <input type="text" name='uname' value = {data.uname} onChange={func} ></input>
    {errors.uname&&<span style={{color:"red"}}>{errors.uname}</span>}
    <input type="submit" value={"Register"} ></input>
 </form>
  </>
  )
}

export default Comp1
