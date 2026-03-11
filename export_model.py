"""
Run this once before starting the API:
    python export_model.py

Trains a RandomForest pipeline on the processed data and saves it to models/model.pkl
"""
import pickle
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DATA = "data/processed/train.csv"
MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / "model.pkl"

MODEL_DIR.mkdir(exist_ok=True)

print("Loading data...")
df = pd.read_csv(DATA)
X = df.drop("hit", axis=1)
y = df["hit"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training pipeline (StandardScaler + RandomForest)...")
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("model", RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)),
])

pipeline.fit(X_train, y_train)
preds = pipeline.predict(X_test)

print("\n--- Evaluation on Test Set ---")
print(f"  Accuracy : {accuracy_score(y_test, preds):.4f}")
print(f"  Precision: {precision_score(y_test, preds):.4f}")
print(f"  Recall   : {recall_score(y_test, preds):.4f}")
print(f"  F1 Score : {f1_score(y_test, preds):.4f}")

with open(MODEL_PATH, "wb") as f:
    pickle.dump(pipeline, f)

print(f"\nModel saved to {MODEL_PATH}")
print("You can now start the API:  uvicorn api.app:app --reload")
