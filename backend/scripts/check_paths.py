
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import ROOT, DATA_DIR, CHROMA_DIR, UPLOAD_DIR, CONFIG_PATH
import os

print("Path configuration check")
print("=" * 60)
print(f"ROOT: {ROOT}")
print(f"DATA_DIR: {DATA_DIR}")
print(f"CHROMA_DIR: {CHROMA_DIR}")
print(f"UPLOAD_DIR: {UPLOAD_DIR}")
print(f"CONFIG_PATH: {CONFIG_PATH}")
print("=" * 60)

# Check if these directories exist
print("Directory existence:")
print(f"DATA_DIR exists: {os.path.exists(DATA_DIR)}")
print(f"CHROMA_DIR exists: {os.path.exists(CHROMA_DIR)}")
print(f"UPLOAD_DIR exists: {os.path.exists(UPLOAD_DIR)}")
print("=" * 60)

# Check what's in the root data directory
print("Files in root data directory:")
if os.path.exists(DATA_DIR):
    for file in os.listdir(DATA_DIR):
        print(f"  - {file}")
else:
    print("  Root data directory does not exist")

print("\n" + "=" * 60)

# Check what's in the backend data directory
backend_data = Path(__file__).parent / "data"
print(f"Files in backend data directory ({backend_data}):")
if os.path.exists(backend_data):
    for file in os.listdir(backend_data):
        print(f"  - {file}")
else:
    print("  Backend data directory does not exist")

print("\n" + "=" * 60)
print("Path check completed!")
