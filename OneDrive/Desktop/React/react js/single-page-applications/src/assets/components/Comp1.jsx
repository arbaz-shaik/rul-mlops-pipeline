import Laptops from "./Laptops";
import Mobile from "./Mobile";

const Comp1=()=>{

    return(
        <>
        welcome t Comp2

        <Link to="comp1/laptops" style={{marginRight:100}} >
        Laptops
    </Link>
    <Link to="comp1/mobiles" style={{marginRight:100}} >
        mobiles
    </Link>

    <br></br>
    <Outlet></Outlet>
        </>
    )


}

export default Comp1;