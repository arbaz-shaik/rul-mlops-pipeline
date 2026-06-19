import axios from "axios";
import {createAsyncThunk} from "@reduxjs/toolkit";

import React from 'react'

const apiCalls = createAsyncThunk ("redux", async () => {
    return await axios.get("https://www.w3schools.com/angular/customers.php")
  }) 

export default apiCalls
