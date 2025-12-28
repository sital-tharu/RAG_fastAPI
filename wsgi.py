import sys
import os

# Ensure the current directory is in the path
sys.path.append(os.getcwd())

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
