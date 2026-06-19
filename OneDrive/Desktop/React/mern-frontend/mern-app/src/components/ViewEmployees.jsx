import axios from "axios";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const ViewEmployees = () => {
  const navigate = useNavigate();
  const [employees, setEmployees] = useState([]);

  const fetchEmployees = async () => {
    try {
      const res = await axios.get("http://localhost:8080/employees");
      const { data } = res;
      setEmployees(data);
    } catch (error) {
      console.error("Error fetching employees:", error);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  const delete_func = async (e_id) => {
    try {
      const res = await axios.delete("http://localhost:8080/employees", {
        data: { e_id: e_id }
      });
      if (res.data.msg === "record deleted successfully !!!") {
        // Refresh the employees list after successful deletion
        fetchEmployees();
      } else {
        console.error("Error deleting record:", res.data.msg);
      }
    } catch (error) {
      console.error("Error deleting employee:", error);
    }
  };

  const add = () => {
    navigate("/add");
  };

  const edit = (e_id, e_name, e_sal, e_image) => {
    navigate(`/update/${e_id}/${e_name}/${e_sal}/${encodeImageUrl}`);
  };

  return (
    <>
      <button onClick={add} style={{ marginLeft: 350 }}>add</button>
      <table border={1} align="center" cellPadding={10} cellSpacing={10}>
        <thead>
          <tr>
            <th>e_id</th>
            <th>e_name</th>
            <th>e_sal</th>
            <th>e_img</th>
            <th>edit</th>
            <th>delete</th>
          </tr>
        </thead>
        <tbody>
          {employees.map((element, index) => (
            <tr key={index}>
              <td>{element.e_id}</td>
              <td>{element.e_name}</td>
              <td>{element.e_sal}</td>
              <td><img src={element.e_image} width={50} alt="" /></td>
              <td>
                <i className="fa fa-edit" onClick={() => edit(element.e_id, element.e_name, element.e_sal, element.e_image)}></i>
              </td>
              <td>
                <i className="fa fa-trash" onClick={() => delete_func(element.e_id)}></i>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
};

export default ViewEmployees;
