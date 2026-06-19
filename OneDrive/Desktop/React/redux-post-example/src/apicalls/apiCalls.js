import axios from "axios";
import { createAsyncThunk } from "@reduxjs/toolkit";

const apiCalls = createAsyncThunk("post-ex", async (data) => {
  const response = await axios.post("https://reqres.in/api/users", data);
  return response.data; 
});

export default apiCalls;
