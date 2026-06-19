import global1 from "../global/global";
import Comp2 from "./Comp2.jsx"
const Comp1 =()=>{
    return(
        <>
        <global1.Provider value="coffee"><Comp2></Comp2></global1.Provider>
        </>
    )
}
export default Comp1;