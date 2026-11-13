"""Launcher script for BinaryReceptor v3.0.0."""
import sys
from pathlib import Path

# Ensure project root is in python path
root = Path(__file__).resolve().parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from src.main import main

if __name__ == "__main__":
    main()
