#!/usr/bin/env python3
"""Generate skill for FAISS (same as other examples)"""
import subprocess, sys
from pathlib import Path

print("=" * 60)
print("Step 1: Generating Skill for FAISS")
print("=" * 60)

# Scrape
subprocess.run([
    "skill-seekers", "scrape",
    "--config", "configs/flask.json",
    "--max-pages", "20"
], check=True)

# Package
subprocess.run([
    "skill-seekers", "package",
    "output/flask",
    "--target", "faiss"
], check=True)

output = Path("output/flask-faiss.json")
print(f"\n✅ Ready: {output} ({output.stat().st_size/1024:.1f} KB)")
print("Next: python 2_build_faiss_index.py (requires OPENAI_API_KEY)")
