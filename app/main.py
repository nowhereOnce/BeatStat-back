from fastapi import FastAPI
from app.routes import auth, playlists
from app.middleware.token import RefreshTokenMiddleware

app = FastAPI()

# Middleware configuration
app.add_middleware(RefreshTokenMiddleware)

# Router configuration
app.include_router(auth.router)
app.include_router(playlists.router)

@app.get("/")
def read_root():
    return {"Message": "Welcome to Statify!"}