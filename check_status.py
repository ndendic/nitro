import json

print("Nitro feature_list.json:")
with open('feature_list.json') as f:
    data = json.load(f)
    passing = len([x for x in data if x['passes']])
    print(f"  Passing: {passing}/{len(data)}")

print("\nParent feature_list.json:")
with open('../feature_list.json') as f:
    data = json.load(f)
    passing = len([x for x in data if x['passes']])
    print(f"  Passing: {passing}/{len(data)}")
