"""Top-level runner for backward compatibility.

Run this from the `python` folder to start the application:

    python run_apriltag.py

This forwards to the `fork_lift` package entrypoint.
"""
from fork_lift.apriltag import _run_main

if __name__ == '__main__':
    _run_main()
