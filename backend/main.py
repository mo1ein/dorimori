import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import API_HOST, API_PORT
from src.routers import search

app = FastAPI()

origins = ["*"]

# todo: remove * for security ...
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(search.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Image Search Engine"}


if __name__ == "__main__":
    uvicorn.run(app, host=API_HOST, port=API_PORT)
