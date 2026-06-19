//import modules
const express = require("express");
const cors = require("cors");
const {MongoClient} = require("mongodb");

//create rest object
const app = express();

//enable cors policy
app.use(cors());

//set JSON as MIME Type
app.use(express.json());

//create client object
const client = new MongoClient("mongodb+srv://admin:admin@mern.cf0bqpc.mongodb.net/?retryWrites=true&w=majority&appName=MERN");

//create get request
app.get("/employees",async (req,res)=>{
    await client.connect();
    const arr = await client.db("mern_db").collection("employees").find().toArray();
    res.json(arr);
});


//create post request
app.post("/insert",async (req,res)=>{
    await client.connect();
    const {acknowledged} = await client.db("mern_db").collection("employees").insertOne({"e_id":req.body.e_id,"e_name":req.body.e_name,"e_sal":req.body.e_sal,"e_image":req.body.e_image});
   
    if(acknowledged){
        res.json({"msg":"record saved successfully !!!"});
    }else{
        res.json({"msg":"record not saved !!!"});
    }

});


//create update request
app.put("/update",async (req,res)=>{
    await client.connect();
    const {acknowledged} = await client.db("mern_db").collection("employees").updateOne({"e_id":req.body.e_id},{$set:{"e_name":req.body.e_name,"e_sal":req.body.e_sal,"e_image":req.body.e_image}});
    if(acknowledged){
        res.json({"msg":"record updated successfully !!!"});
    }else{
        res.json({"msg":"record not updated !!!"});
    }
});

//create delete request
app.delete("/employees", async (req, res) => {
    await client.connect();
    const { e_id } = req.body;
    const { acknowledged } = await client.db("mern_db").collection("employees").deleteOne({ e_id: e_id });
    if (acknowledged) {
      res.json({ msg: "record deleted successfully !!!" });
    } else {
      res.json({ msg: "record not deleted !!!" });
    }
  });



//assign port no
app.listen(8080,()=>{
    console.log("server listening port no.8080");
});