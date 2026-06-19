import { Component, PureComponent } from "react";

class Comp2  extends PureComponent {
   render() {
    console.log("child")
     return (
       
      <>

      <h1>{this.props.msg}</h1>

      </>
     )
   }
}

export default Comp2
