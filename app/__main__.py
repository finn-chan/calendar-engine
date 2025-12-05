"""Entry point for running Calendar Engine as a module."""

import sys

from app.sync import main

if __name__ == "__main__":
    sys.exit(main())
