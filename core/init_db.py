
import os
import sys

# Add the project root to the Python path
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
sys.path.append(_PROJECT_ROOT)

from core.db import Base, engine

print("Creating database tables...")
Base.metadata.create_all(engine)
print("Database tables created.")
