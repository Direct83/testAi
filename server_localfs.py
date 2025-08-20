# server_localfs.py
from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "MCP LocalFS Server is running"}

@app.get("/list")
def list_files():
    files = os.listdir("./mcp_data") if os.path.exists("./mcp_data") else []
    return {"files": files}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
