import {useContext} from "react";
import global1 from "../global/global";

const Comp2 =()=>{
    const msg = useContext(global1);
    return(
        <>
        <h1>{msg}</h1>
        </>
    )
}

export default Comp2;