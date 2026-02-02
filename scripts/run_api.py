from pathlib import Path

import uvicorn
from dotenv import load_dotenv

ENV_FILE = Path(__file__).parent / ".." / ".env"
load_dotenv(ENV_FILE)


if __name__ == "__main__":
    uvicorn.run("echo.server:app", host="127.0.0.1", port=8080, reload=True)
