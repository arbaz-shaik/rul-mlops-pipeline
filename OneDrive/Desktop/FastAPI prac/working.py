from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def home():
    return {"Data": "i love homdan"}

@app.get("/about")
def about():
    return {"Data": "i am a software engineer"}
