from fastapi import FastAPI

app = FastAPI(title="Power Level Service")

@app.get()