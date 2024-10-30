#!/usr/bin/python
# -*- coding: UTF-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
import argparse
import numpy as np
import os

parser = argparse.ArgumentParser(description="Plot Total Memory over Time from a specified data file.")
parser.add_argument(
    'file_path',
    type=str,
    help="Path to the .txt file containing the data."
)
args = parser.parse_args()

data_file = args.file_path

base_name = os.path.splitext(os.path.basename(data_file))[0]
output_file = f"{base_name}_memory_distribution.png"

try:
    df = pd.read_csv(
        data_file,
        sep=',',
        header=0,  # Assumes the first line is the header
        names=['Time (minutes)', 'Total Memory (GB)'],
        na_values=['', ' '],  # Treat empty strings as NaN
        skip_blank_lines=True  # Skip completely blank lines
    )
except FileNotFoundError:
    print("Error: The file '{}' was not found.".format(data_file))
    exit(1)
except pd.errors.ParserError as e:
    print("Error parsing the file: {}".format(e))
    exit(1)

# Replace missing values in 'Total Memory (GB)' with 0
df_clean = df.fillna({'Total Memory (GB)': 0})

# Convert columns to numeric types
df_clean['Time (minutes)'] = pd.to_numeric(df_clean['Time (minutes)'], errors='coerce')
df_clean['Total Memory (GB)'] = pd.to_numeric(df_clean['Total Memory (GB)'], errors='coerce')

# Drop any rows that couldn't be converted to numeric values (only dropping rows where 'Time (minutes)' is NaN)
df_clean = df_clean.dropna(subset=['Time (minutes)'])

# Convert Time to Seconds and Add a New Column to df_clean
time_in_seconds = []
for minute, group in df_clean.groupby('Time (minutes)'):
    num_entries = len(group)
    # Convert minute to seconds and create unique time values for each entry within that minute
    base_time = minute * 60
    adjusted_times = [base_time + i * (60 / num_entries) for i in range(num_entries)]
    time_in_seconds.extend(adjusted_times)

df_clean['Time (seconds)'] = time_in_seconds

p99 = df_clean['Total Memory (GB)'].quantile(0.99)
p95 = df_clean['Total Memory (GB)'].quantile(0.95)
max_value = df_clean['Total Memory (GB)'].max()
avg_value = df_clean['Total Memory (GB)'].mean()

print("Statistics for Total Memory (GB):")
print(f"P99: {p99:.2f} GB")
print(f"P95: {p95:.2f} GB")
print(f"Max: {max_value:.2f} GB")
print(f"Avg: {avg_value:.2f} GB")

plt.figure(figsize=(36, 12))
plt.plot(
    df_clean['Time (seconds)'],
    df_clean['Total Memory (GB)'],
    marker='o',
    linestyle='-',
    color='b',
    label='Total Memory'
)

plt.title('8 core planner build RAM distribution')
plt.xlabel('Time (minutes)')
plt.ylabel('Total Memory (GB)')

plt.grid(True)

plt.legend()

# Adjust the x-axis ticks to show time in minutes
# Define ticks every 60 seconds to label each minute
max_time_in_seconds = df_clean['Time (seconds)'].max()
minute_ticks = np.arange(0, max_time_in_seconds + 60, 60)  # Create ticks at every minute
minute_labels = [int(tick / 60) for tick in minute_ticks]  # Convert seconds to minutes for labeling

plt.xticks(minute_ticks, minute_labels)

plt.tight_layout()

plt.savefig(output_file)

plt.show()
