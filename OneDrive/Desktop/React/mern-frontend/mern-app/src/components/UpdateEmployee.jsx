import { useState } from "react";
import { useParams,useNavigate } from "react-router-dom";
import axios from "axios";

const UpdateEmployee = ()=>{
    const navigate = useNavigate();
    const {e_id,e_name,e_sal,e_image} = useParams();
    const [employee,setEmployee] = useState({"e_id": parseInt(e_id) || '',
                                             "e_name":e_name || '',
                                             "e_sal" : parseInt(e_sal) || '',
                                             "e_image" : e_image || ''});
    const submit_data = async (event)=>{
        event.preventDefault();
        const {data} = await axios.put("http://localhost:8080/update",employee);
        const {msg} = data;
        if(msg == "record updated successfully !!!"){
            navigate("/");
        }else{
            navigate("/update");
        }
    }

    const func_one = (event)=>{
        setEmployee({...employee,[event.target.name]: event.target.value});
    }

    return(
        <>
            <form onSubmit={submit_data}>
                <input type="number" name="e_id" value={employee.e_id} onChange={func_one} readOnly></input>
                <br></br><br></br>
                <input type="text" name="e_name" value={employee.e_name} onChange={func_one}></input>
                <br></br><br></br>
                <input type="number" name="e_sal" value={employee.e_sal} onChange={func_one}></input>
                <br></br><br></br>
                <input type="text" name="e_image" value={employee.e_image} onChange={func_one}></input>
                <br></br><br></br>
                <input type="submit" value={"Update"}></input>
            </form>          
        </>
    )
}
export default UpdateEmployee;