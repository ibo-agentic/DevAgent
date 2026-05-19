import csv

# Load the CSV data
file_path = 'data/sample.csv'

with open(file_path, mode='r') as file:
    reader = csv.DictReader(file)
    highest_score_row = max(reader, key=lambda row: int(row['score']))

# Get the name and score
name = highest_score_row['name']
score = highest_score_row['score']

print(f'The person with the highest score is {name} with a score of {score}')
