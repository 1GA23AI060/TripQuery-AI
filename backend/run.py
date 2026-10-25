import uvicorn
import os
import sys

if __name__ == "__main__":
    # Ensure backend directory is in sys.path
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    print("=" * 60)
    print(">> Starting TripQuery AI Backend Server...")
    print(">> URL: http://localhost:8000")
    print(">> API Docs: http://localhost:8000/docs")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
