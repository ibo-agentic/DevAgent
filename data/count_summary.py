import json
from collections import Counter

# Load data
with open('data/sample.json') as f:
    data = json.load(f)

# Count items per category
category_counts = Counter(item['category'] for item in data)

# Print the summary
for category, count in category_counts.items():
    print(f'{category}: {count}')
