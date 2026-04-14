
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import ROOT, DATA_DIR, CHROMA_DIR

print("Root path check")
print("=" * 60)
print(f"Current file: {__file__}")
print(f"Path(__file__): {Path(__file__)}")
print(f"Path(__file__).resolve(): {Path(__file__).resolve()}")
print(f"Path(__file__).resolve().parents[0]: {Path(__file__).resolve().parents[0]}")
print(f"Path(__file__).resolve().parents[1]: {Path(__file__).resolve().parents[1]}")
print(f"Path(__file__).resolve().parents[2]: {Path(__file__).resolve().parents[2]}")
print(f"Path(__file__).resolve().parents[3]: {Path(__file__).resolve().parents[3]}")
print("=" * 60)
print(f"ROOT: {ROOT}")
print(f"DATA_DIR: {DATA_DIR}")
print(f"CHROMA_DIR: {CHROMA_DIR}")
print("=" * 60)
print("Path check completed!")
