import json

# Read feature list
with open('feature_list.json', 'r') as f:
    features = json.load(f)

# Update all cli_tailwind entries to passes: true
count = 0
for feature in features:
    if feature['category'] == 'cli_tailwind' and not feature['passes']:
        feature['passes'] = True
        count += 1
        print(f"Updated: {feature['description']}")

# Write back
with open('feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print(f"\nTotal updated: {count}")
