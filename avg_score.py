import csv
import json

# Load data from CSV
with open('data/sample.csv', mode='r') as file:
    reader = csv.DictReader(file)
    scores = [float(row['score']) for row in reader]
    
# Calculate the average
average_score = sum(scores) / len(scores) if scores else 0

# Write the result to a JSON file
result = {'average_score': average_score}
with open('avg_score.json', 'w') as json_file:
    json.dump(result, json_file)

print(average_score)