"""Single-command entry point to launch the CodeCraft local web server."""
import sys
import uvicorn

from backend.config import SERVER_HOST, SERVER_PORT


def main():
    print("=" * 70)
    print("  CodeCraft Early Metabolic Risk Detection Platform")
    print("  ML vs DL vs QML Benchmark on NHANES 2017-2018")
    print("=" * 70)
    print(f"  Local Server: http://{SERVER_HOST}:{SERVER_PORT}")
    print("  Binding: 127.0.0.1 (Localhost only, offline-ready, no remote CDNs)")
    print("  Warning: Research/educational use only. Not a diagnosis or medical advice.")
    print("=" * 70)
    print("  Press CTRL+C to terminate the server.\n")

    uvicorn.run(
        "backend.api.app:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
