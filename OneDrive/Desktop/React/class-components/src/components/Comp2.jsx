import { Component } from "react";
import Comp3 from "./Comp3";
class Comp2 extends Component{
    render(){
        return(
            <>
            <Comp3

            msg ={"exelr"}
            arr = {[1,2,3,4,5]}
            obj={{"key1":"gelloe", "key2" : "bye bye react"}}
            
            ></Comp3>
            </>
        )
    }
}
export default Comp2;