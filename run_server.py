import sys
from pathlib import Path
import uvicorn

# make sure backend is importable
sys.path.append(str(Path(__file__).resolve().parent))

# ✅ Directly import and run the app (no subprocesses)
if __name__ == "__main__":
    from backend.main import app
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
