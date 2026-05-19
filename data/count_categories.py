import json
from collections import Counter

# Load the data from the JSON file
with open('data/sample.json', 'r') as file:
    data = json.load(file)

# Count the items per category
category_counts = Counter(item['category'] for item in data)

# Print summary
for category, count in category_counts.items():
    print(f'{category}: {count}')
