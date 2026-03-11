import pandas as pd
import os

INPUT_FILE = "datasets/tmdb_5000_movies.csv"
OUTPUT_FILE = "data/raw/movies.csv"

def ingest():

    df = pd.read_csv(INPUT_FILE)

    os.makedirs("data/raw", exist_ok=True)

    df.to_csv(OUTPUT_FILE, index=False)

    print("Data saved to raw layer")

if __name__ == "__main__":
    ingest()