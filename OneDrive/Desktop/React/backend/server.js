//import modules

const express= require("express");
const {MongoClient} = require ("mongodb");
const cors = require ("cors");

//create rest object
const app = express();

//enable cors policy
app.use(cors()); 
// json
app.use(express.json())

//create client object

const client = new MongoClient ("mongodb+srv://admin:admin@mern1.jcccqgk.mongodb.net/?retryWrites=true&w=majority&appName=MERN1")


// create a GET request

app.get("/employees",async (req, res)=>{
    await client.connect();
    await client.db("mern_db").collection("employees").find().toArray();
    res.json(arr);
})

app.listen(8080, ()=>{
    console.log("server listenting the port no.8080");
});