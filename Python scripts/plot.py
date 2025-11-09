import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV (adjust path if your file is elsewhere)
df = pd.read_csv('results.csv')

# Count occurrences
sat_count = (df['status'] == 'sat').sum()
unsat_count = (df['status'] == 'unsat').sum()
crash_count = (df['status'] == 'crash').sum()

# Prepare data, rename 'crash' to 'unsolved'
labels = ['sat', 'unsat', 'unsolved']
values = [sat_count, unsat_count, crash_count]

# Plot bar chart
plt.figure()
plt.bar(labels, values)
plt.xlabel('Status')
plt.ylabel('Count')
plt.title('Solver Outcome Counts')
plt.tight_layout()
plt.show()