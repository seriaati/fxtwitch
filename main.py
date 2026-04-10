import uvicorn

from fxtwitch.app import app

if __name__ == "__main__":
    uvicorn.run(app, port=8010)
