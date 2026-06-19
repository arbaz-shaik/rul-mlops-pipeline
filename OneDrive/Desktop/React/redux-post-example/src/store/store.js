import { configureStore } from "@reduxjs/toolkit";
import slice from "../slice/slice";

const store = configureStore(
    { reducer : {
        post:slice
    }

    }
);

export default store;