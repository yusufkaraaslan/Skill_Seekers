#!/usr/bin/env python3
"""Generate skill for Qdrant"""
import subprocess, sys
from pathlib import Path

print("=" * 60)
print("Step 1: Generating Skill for Qdrant")
print("=" * 60)

# Scrape Django docs
subprocess.run([
    "skill-seekers", "scrape",
    "--config", "configs/django.json",
    "--max-pages", "20"
], check=True)

# Package for Qdrant
subprocess.run([
    "skill-seekers", "package",
    "output/django",
    "--target", "qdrant"
], check=True)

output = Path("output/django-qdrant.json")
print(f"\n✅ Ready: {output} ({output.stat().st_size/1024:.1f} KB)")
print("Next: python 2_upload_to_qdrant.py")
