import pandas as pd
import plotly.graph_objects as go
import os
import argparse
from plotly.subplots import make_subplots


def plot_interactive_current_data(df, title):
    # Filter out rows where all currents are zero or NaN
    filtered_df = df[(df != 0).all(1) & ~df.isna().any(1)]
    if not filtered_df.empty:
        # Create a figure with subplots
        fig = make_subplots(rows=1, cols=1)

        # Add a trace for each current measurement
        for column in filtered_df.columns:
            fig.add_trace(
                go.Scatter(x=filtered_df.index, y=filtered_df[column], name=column),
                row=1,
                col=1,
            )

        # Update layout information
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Current (A)",
            legend_title="Measurements",
            hovermode="x",
        )

        # Show the figure
        fig.show()
    else:
        print(f"No non-zero current values to plot for {title}")


# Set up argument parser
parser = argparse.ArgumentParser(description="Plot Current Data from a CSV File")
parser.add_argument("csv_file_path", help="Path to the CSV file")

# Parse arguments
args = parser.parse_args()

# Extract title from the file name
file_name = os.path.basename(args.csv_file_path)
title = file_name.replace("_", " ").replace(".csv", "").title()

# Read the data
csv_df = pd.read_csv(args.csv_file_path, parse_dates=["Time"], index_col="Time")

# Plot the data
plot_interactive_current_data(csv_df, title)
