"""Kloppy backend entry point."""

import uvicorn

from src.app.application import app as application

app = application


def main() -> None:
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
