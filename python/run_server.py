"""Top-level runner for backward compatibility.

Run this from the `python` folder to start the application:

    python run_server.py

This forwards to the `server` package entrypoint.
"""
from server.server import main

if __name__ == '__main__':
    main()
