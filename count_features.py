import json

with open('feature_list.json') as f:
    features = json.load(f)

passing = len([x for x in features if x["passes"]])
total = len(features)

print(f"{passing}/{total} features passing ({passing/total*100:.1f}%)")
