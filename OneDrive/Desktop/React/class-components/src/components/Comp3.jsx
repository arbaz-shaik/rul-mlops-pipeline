import { Component } from "react";
class Comp3 extends Component{
    render(){
        return(
            <>
            <h1>{this.props.msg}</h1>
            {
                this.props.arr.map((element,index)=>{
                    return(<h1 key={index}>{element}</h1>)
                }

                )
            }

            <h1>{this.props.obj.key1}....{this.props.obj.key1}</h1>
            </>
        )
    }
}
export default Comp3;