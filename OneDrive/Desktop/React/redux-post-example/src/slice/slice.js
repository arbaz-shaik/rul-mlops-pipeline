import apiCalls from "../apicalls/apiCalls";
import { createSlice } from "@reduxjs/toolkit";

const slice = createSlice({
    name: "post",
    initialState: {
        isLoading: false,
        result: {},
        isError: false
    },
    extraReducers: (builder) => {
        builder.addCase(apiCalls.pending, (state, action) => {
           state.result = {};
            state.isError = false;
        });

        builder.addCase(apiCalls.fulfilled, (state, action) => {
            state.result = action.payload; // Store the result from the API call
            state.isError = false;
        });

        builder.addCase(apiCalls.rejected, (state, action) => {
            state.result = {}; // Clear the result on error
            state.isError = true; // Set isError to true since the request failed
        });
    }
});

export default slice.reducer;
