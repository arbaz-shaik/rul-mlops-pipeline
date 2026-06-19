import  {useDispatch, useSelector} from "react-redux";
import apiCalls from "./apiCalls";
import { useEffect } from "react";

const Comp1=()=>{
     const res = useSelector(state=> state);
     const dispatch= useDispatch();

     useEffect(()=>{
        dispatch(apiCalls())

     },[])

     return(
        <>
        <p>{JSON.stringify(res)}</p>
        </>
     )

}
export default Comp1;
