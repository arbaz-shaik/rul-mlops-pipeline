from fastapi import FastAPI
import redis
import os

app = FastAPI()
redis_host = os.getenv("REDIS_HOST", "localhost")
client = redis.Redis(host=redis_host, port=6379, db=0)

@app.get("/")
def health():
    return {"status":"ok"}

@app.post("/count")
def increment_count():
    value = client.incr("count")
    return {"count": value}
