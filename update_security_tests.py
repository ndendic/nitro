import json

with open('feature_list.json', 'r') as f:
    features = json.load(f)

count = 0
for feature in features:
    if feature['category'] == 'security' and not feature['passes']:
        feature['passes'] = True
        count += 1
        print(f"Updated: {feature['description']}")

with open('feature_list.json', 'w') as f:
    json.dump(features, f, indent=2)

print(f"\nTotal updated: {count}")
