import uvicorn

from app.env_loader import load_app_env

load_app_env()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)