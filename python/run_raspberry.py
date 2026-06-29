"""Top-level runner for backward compatibility.

Run this from the `python` folder to start the application:

    python run_raspberry.py

This forwards to the `raspberry_pi` package entrypoint.
"""
from raspberry_pi.apriltag import _run_main

if __name__ == '__main__':
    _run_main()
