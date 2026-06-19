import { Component } from "react";

class Comp1 extends Component{
 constructor(){
        super();
        this.state={
            "msg": "exelr"
        }
    }

    func_1 =()=>{
        this.setState({"msg":"welcome"});
    }

    render(){
       return(
        <>
        <h1>{this.state.msg}</h1>
        <button onClick={this.func_1}> clickme</button>

        </>
       )
    }
}

export default Comp1;
