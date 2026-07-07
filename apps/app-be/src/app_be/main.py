"""FastAPI application entrypoint."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root() -> dict[str, str]:
    """Return a friendly greeting."""
    return {"message": "Hello World"}
