#!/usr/bin/env python3

from importlib import import_module
import sys
import uvicorn


def check_dependencies():
    try:
        for module in ("fastapi", "redis", "sqlalchemy"):
            import_module(module)
        print("✅ All dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Dependencies not present: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        return False


def main():
    if not check_dependencies():
        sys.exit(1)

    print("🚀 Start Wish List API...")
    print("📖 Docs available on: http://localhost:8000/docs")
    print("🔄 API endpoints on: http://localhost:8000")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()