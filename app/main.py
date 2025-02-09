from fastapi import FastAPI
from app.routes import auth, playlists

app = FastAPI()

app.include_router(auth.router)
app.include_router(playlists.router)

@app.get("/")
def read_root():
    return {"Message": "Welcome to Statify!"}