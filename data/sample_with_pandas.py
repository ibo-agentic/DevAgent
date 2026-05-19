import pandas as pd

# Load the CSV file from the same directory
df = pd.read_csv('data/sample.csv')

# Calculate the sum of the 'amount' column
total_amount = df['amount'].sum()

# Print the total amount
print(total_amount)