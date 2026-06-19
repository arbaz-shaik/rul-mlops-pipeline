import { Component } from "react";
import Comp2 from "./Comp2";


class Comp1 extends Component{

    constructor(){
        
        super();  
        this.state=  {
       num: 100}

    }

    componentDidMount(){
        setInterval(() => {

            this.setState({
                num:100
            })
            
        },1000);

        }

        
    

    render() {
        console.log("parent")
      return (
      <>
        <Comp2 msg={this.state.num}></Comp2>
   
        </>

      )
    }

    shouldComponentUpdate(){
        return false;
    }


    
}

export default Comp1;