import pandas as pd
import os

RAW_DATA = "data/raw/movies.csv"
PROCESSED_DATA = "data/processed/train.csv"

def preprocess():

    df = pd.read_csv(RAW_DATA)

    df = df[df["budget"] > 0]
    df = df[df["revenue"] > 0]

    df["hit"] = (df["revenue"] > df["budget"]).astype(int)

    features = [
        "budget",
        "runtime",
        "vote_average",
        "vote_count",
        "popularity",
        "hit"
    ]

    df = df[features]

    os.makedirs("data/processed", exist_ok=True)

    df.to_csv(PROCESSED_DATA, index=False)

    print("Processed data saved")

if __name__ == "__main__":
    preprocess()