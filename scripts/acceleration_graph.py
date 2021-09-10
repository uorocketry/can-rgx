import argparse
import glob
import os

import pandas as pd
from matplotlib import pyplot as plt

parser = argparse.ArgumentParser(description='Display a graph of acceleration data')
parser.add_argument('path', help='path to the folder containing the csv files')
parser.add_argument('--date', help='if specified, only display the data for this date')

args = parser.parse_args()

all_files = glob.glob(os.path.join(args.path, "*.csv"))

df = pd.concat((pd.read_csv(f) for f in all_files))

# Necessary because of bug in the code
df['timestamp'] = df['timestamp'] * 10

df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

df = df.set_index('timestamp')

df = df.tz_localize('UTC').tz_convert('America/Toronto')
if args.date:
    df = df.loc[args.date]

df = df.dropna()

df = df.resample('1S').mean()

plot = df.plot(title="Acceleration over time")
plot.set_xlabel("Time")
plot.set_ylabel("Acceleration (m/s^2)")

plt.show()
