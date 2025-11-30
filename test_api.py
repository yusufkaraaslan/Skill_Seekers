#!/usr/bin/env python3
"""Quick test of the config analyzer"""
import sys
sys.path.insert(0, 'api')

from pathlib import Path
from api.config_analyzer import ConfigAnalyzer

# Initialize analyzer
config_dir = Path('configs')
analyzer = ConfigAnalyzer(config_dir, base_url="https://api.skillseekersweb.com")

# Test analyzing all configs
print("Testing config analyzer...")
print("-" * 60)

configs = analyzer.analyze_all_configs()
print(f"\n✅ Found {len(configs)} configs")

# Show first 3 configs
print("\n📋 Sample Configs:")
for config in configs[:3]:
    print(f"\n  Name: {config['name']}")
    print(f"  Type: {config['type']}")
    print(f"  Category: {config['category']}")
    print(f"  Tags: {', '.join(config['tags'])}")
    print(f"  Source: {config['primary_source'][:50]}...")
    print(f"  File Size: {config['file_size']} bytes")

# Test category counts
print("\n\n📊 Categories:")
categories = {}
for config in configs:
    cat = config['category']
    categories[cat] = categories.get(cat, 0) + 1

for cat, count in sorted(categories.items()):
    print(f"  {cat}: {count} configs")

print("\n✅ All tests passed!")
