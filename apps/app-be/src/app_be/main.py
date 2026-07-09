"""FastAPI application entrypoint."""

from pathlib import Path

import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

CALLBACK_DATA_PATH = Path(__file__).resolve().parent / "callback_data.yaml"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    # allow_methods=["GET", "POST"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/greetings/{name}")
def read_greetings(name: str):
    return {"message": f"Hello, {name}!"}


@app.get("/callback")
def callback(code: str, state: str):
    with open(CALLBACK_DATA_PATH, "w") as file:
        yaml.dump({"code": code, "state": state}, file)
    return {"message": "Callback received successfully!"}
