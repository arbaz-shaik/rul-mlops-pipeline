import slice from "../slice/slice";
import { configureStore } from "@reduxjs/toolkit";

const store = configureStore({
  reducer: {
    redux: slice,
  },
});

export default store;
