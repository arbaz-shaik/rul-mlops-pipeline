import React from 'react';
import { useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import apiCalls from './apicalls/apiCalls';




const Comp1 = () => {

    const res = useSelector(state=> state);
    const dispatch = useDispatch();
    const ref1 = useRef(null);
    const ref2 = useRef(null);
    const send =()=>{
        dispatch(apiCalls ({name: ref1.current.value, job: ref2.current.value}))
    }

  return (
    <>
    <input type="text" ref={ref1} placeholder='entername'></input>
    <input type="text" ref={ref2} placeholder='enterjob'></input>
    <button onClick={send}>send</button>
    <h1>{JSON.stringify(res)}</h1>
    </>
 
  )
}

export default Comp1
