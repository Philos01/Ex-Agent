
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.vector_store import get_collection_info, search
from app.services.ingest import ingest_file
import os

print("Checking vector store...")
print("=" * 60)

# Check collection info
info = get_collection_info()
print(f"Collection info: {info}")
print("=" * 60)

# Test search with the paper title
paper_title = "Unsupervised Spectral Super Resolution Guided by Spectral Sampling Priors tgrs"
print(f"Searching for: {paper_title}")
docs = search(paper_title, top_k=10)
print(f"Found {len(docs)} results:")

for i, doc in enumerate(docs):
    print(f"\nResult {i+1}:")
    print(f"  Text: {doc['text'][:100]}...")
    print(f"  Metadata: {doc['metadata']}")

print("\n" + "=" * 60)

# Check what files are in the uploads directory
from app.core.config import UPLOADS_DIR
print(f"Files in uploads directory:")
if os.path.exists(UPLOADS_DIR):
    for file in os.listdir(UPLOADS_DIR):
        print(f"  - {file}")
else:
    print("  Uploads directory does not exist")

print("\n" + "=" * 60)
print("Vector store check completed!")
