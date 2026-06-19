import apiCalls from "../apicalls/apiCalls";
import     {createSlice} from "@reduxjs/toolkit"

const slice = createSlice({
    name: "redux",
    initialState:{
        isLoading : false,
        result :{},
        isError: false

        
    },
    extraReducers:(builder)=>{
        builder.addCase(apiCalls.pending,(state, action)=>{
            state.isLoading= false;
            state.result={};
            state.isError= false;
        })

        builder.addCase(apiCalls.fulfilled,(state, action)=>{
            state.isLoading= false;
            state.result=action.payload;
            state.isError= false;
        })

        builder.addCase(apiCalls.rejected,(state, action)=>{
            state.isLoading= true;
            state.result={};
            state.isError= true;
        })
    }
    
});
export default slice.reducer;