import Comp1 from "./Comp1";
import Comp2 from "./Comp2";
import Comp3 from "./Comp3";
import Mobile from "./Mobile";
import Laptops from "./Laptops";


import {BrowserRouter, Route, Routes, Link} from "react-router-dom";
const Master = ()=>{

    return(
        <>
       
      
        <BrowserRouter>
        <Link to="/Comp1" style={{marginRight:100}}>Comp1</Link>
        <Link to="/Comp2" style={{marginRight:100}}>Comp2</Link>
        <Link to="/Comp2" style={{marginRight:100}}>Comp3</Link>
        <Routes>
            <Route path="/Comp1" element={<Comp1></Comp1>}></Route>
            <Route path="/Comp2" element={<Comp2></Comp2>}></Route>
            <Route path="/Comp3" element={<Comp3></Comp3>}></Route>
            <Route path="Comp1/mobiles" element={<Mobile></Mobile>}></Route>
            <Route path="Comp1/laptops" element={<Laptops></Laptops>}></Route>
        
        </Routes>
        
        
        </BrowserRouter>
        </>
    )


}

export default Master;