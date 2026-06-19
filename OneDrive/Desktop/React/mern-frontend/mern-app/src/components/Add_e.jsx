import { useRef } from "react";
import axios from "axios";

const Add_e = () => {
  const ref1 = useRef(null);
  const ref2 = useRef(null);
  const ref3 = useRef(null);
  const ref4 = useRef(null);

  const save = async () => {
    try {
      const { data } = await axios.post("http://localhost:8080/insert", {
        e_id: parseInt(ref1.current.value),
        e_name: ref2.current.value,
        e_sal: parseInt(ref3.current.value),
        e_image: ref4.current.value,
      });
      console.log(data);
    } catch (error) {
      console.error("Error saving employee:", error);
    }
  };

  return (
    <>
      <fieldset>
        <legend>Employee</legend>
        <input type="number" ref={ref1} placeholder="Enter employee number" />
        <br /> <br /> <br />
        <input type="text" ref={ref2} placeholder="Enter employee name" />
        <br /> <br /> <br />
        <input type="number" ref={ref3} placeholder="Enter employee salary" />
        <br /> <br /> <br />
        <input type="text" ref={ref4} placeholder="Enter employee image" />
        <br /> <br /> <br />
        <button onClick={save}>Save</button>
      </fieldset>
    </>
  );
};

export default Add_e;
