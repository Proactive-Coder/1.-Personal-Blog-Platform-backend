from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return "Hello"


@app.get("/test")
def test():
    return "test"
