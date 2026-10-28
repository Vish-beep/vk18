
import pandas as pd

file_path = "data/matches.csv"

try:
    df = pd.read_csv(file_path)

    print("\nCSV loaded successfully!")
    print("\nFirst five matches:")
    print(df.head())

    print("\nAvailable columns:")
    print(df.columns.tolist())

    print("\nNumber of rows:", len(df))

except FileNotFoundError:
    print("ERROR: data/matches.csv was not found.")
    print("Check that the CSV is inside the data folder.")

except Exception as error:
    print("Could not read CSV:", error)
