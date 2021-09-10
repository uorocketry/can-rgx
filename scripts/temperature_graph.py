import argparse
import glob
import os

import pandas as pd
from matplotlib import pyplot as plt

parser = argparse.ArgumentParser(description='Display a graph of temperature data')
parser.add_argument('path', help='path to the folder containing the csv files')
parser.add_argument('--date', help='if specified, only display the data for this date')

args = parser.parse_args()

all_files = glob.glob(os.path.join(args.path, "*.csv"))

df = pd.concat((pd.read_csv(f) for f in all_files))

df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

df = df.dropna().drop_duplicates(subset=['timestamp']).pivot("timestamp", "id", "value")

df = df.tz_localize('UTC').tz_convert('America/Toronto')
if args.date:
    df = df.loc[args.date]

plot = df.plot(kind='line', marker='o', markersize=1)
plot.set_xlabel("Time")
plot.set_ylabel("Temperature (C)")

plt.show()
