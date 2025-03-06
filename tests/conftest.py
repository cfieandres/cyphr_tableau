import pytest
import sys
import os
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set test environment variables
os.environ["TESTING"] = "1"