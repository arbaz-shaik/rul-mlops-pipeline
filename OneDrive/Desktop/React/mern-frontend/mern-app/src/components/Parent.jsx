import ViewEmployees from "./ViewEmployees";
import Add_e from "./Add_e";
import {BrowserRouter, Routes, Route} from "react-router-dom"
import UpdateEmployee from "./UpdateEmployee"

const Parent=()=>{

    return(
        <>
        <BrowserRouter>
        <Routes>
            <Route path="/" element={<ViewEmployees></ViewEmployees>}></Route>
            <Route path="/add" element={<Add_e></Add_e>}></Route>
            <Route path="/update/:e_id/:e_sal/:e_name/:e_image"></Route>
        </Routes>
           
            </BrowserRouter>
        </>
    )
}
export default Parent;