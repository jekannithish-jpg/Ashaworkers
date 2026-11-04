import uvicorn
import os
import sys

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(backend_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Starting ASHA Pregnancy Tracking System server on http://localhost:{port}")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, reload=False)

