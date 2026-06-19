import axios from "axios";
import { useEffect, useState } from "react";

const Comp1 = () => {
  const [emps, setEmps] = useState([]);

  useEffect(() => {
    axios.get("https://reqres.in/api/users?page=2").then(
      (posRes) => {
        const { data: x } = posRes;
        const { data } = x;
        setEmps(data);
      },
      (errRes) => {
        console.log(errRes);
      }
    );
  }, []);

  return (
    <>
      <table border={1} align="center" cellSpacing={10} cellPadding={10}>
        <thead>
          <tr>
            <th>id</th>
            <th>email</th>
            <th>first_name</th>
            <th>last_name</th>
            <th>avatar</th>
          </tr>
        </thead>
        <tbody>
          {emps.map((element, index) => (
            <tr key={index}>
              <td>{element.id}</td>
              <td>{element.email}</td>
              <td>{element.first_name}</td>
              <td>{element.last_name}</td>
              <td>
                <img src={element.avatar} width={100} alt="avatar" />
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot></tfoot>
      </table>
    </>
  );
};

export default Comp1;