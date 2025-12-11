#!/usr/bin/env python3
"""Update feature_list.json to mark completed tests as passing"""

import json
from pathlib import Path

# Tests that are now passing (indices in the array)
passing_tests = [0, 1, 2, 3, 4, 6, 7, 8, 9]

# Read the feature list
feature_file = Path("feature_list.json")
with open(feature_file, 'r') as f:
    features = json.load(f)

# Update the passing tests
for i in passing_tests:
    if i < len(features):
        features[i]['passes'] = True
        print(f"✓ Marked test {i} as passing: {features[i]['description']}")

# Write back to file
with open(feature_file, 'w') as f:
    json.dump(features, f, indent=2)

print(f"\n✓ Updated {len(passing_tests)} tests in feature_list.json")

# Count totals
total = len(features)
passing = sum(1 for f in features if f['passes'])
print(f"\nCurrent status: {passing}/{total} tests passing ({passing*100//total}%)")
