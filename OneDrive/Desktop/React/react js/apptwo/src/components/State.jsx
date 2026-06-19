import { useState } from "react";

const State=()=>{

    const [msg , setMsg] = useState(`idddd`);
    const [num, setNum] = useState(100);
    const [flag, setFlag]= useState(true);
    const [arr, setArr]=useState([10,20,30,50]);
    const [obj, setObj]=useState({"key1":"hello", "key2":"welcome"});
    const [employ, setEmployees]= useState([{"eno":"e1","ename":"reee", "eimage":"https://wallpapers.com/images/high/chatgpt-ec8vm1rk6a8wcx8d.webp"},{"eno":"e1","ename":"reee", "eimage":"https://wallpapers.com/images/high/chatgpt-ec8vm1rk6a8wcx8d.webp"},{"eno":"e1","ename":"reee", "eimage":"https://wallpapers.com/images/high/chatgpt-ec8vm1rk6a8wcx8d.webp"},{"eno":"e1","ename":"reee", "eimage":"https://wallpapers.com/images/high/chatgpt-ec8vm1rk6a8wcx8d.webp"}])

    return(
        <>
        <table
        border={1}
        align="center"
        cellPadding={10}
        cellSpacing={10}>
            <thead>
                <th>eno</th>
                <th>ename</th>
                <th>enimg</th>
            </thead>
            <tbody>
                {
                    employ.map((element,index)=>{
                        return(
                            <tr>
                                <td>{element.eno}</td>
                                <td>{element.ename}</td>
                                <td><img src={element.eimage} 
                                width={50}  height={20}
                                alt="Error" /></td>
                            </tr>

                        )
                    })
                }
            </tbody>
        </table>
        {
            arr.map((element, index)=>{
                return(
                    <h1 key= {index}> {element}</h1>
                )
                
            })
        }
        <h1>{obj.key1}.......{obj.key2}</h1>
        <h1>{num}</h1>
        <h1>{msg}</h1>

       
        </>
    )

}

export default State;