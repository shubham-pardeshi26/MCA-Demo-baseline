import pandas as pd
import mlflow
import mlflow.sklearn

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

DATA = "data/processed/train.csv"

mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("movie_hit_prediction")

df = pd.read_csv(DATA)

X = df.drop("hit", axis=1)
y = df["hit"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("model", RandomForestClassifier())
])

with mlflow.start_run(run_name="pipeline_model"):

    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)

    acc = accuracy_score(y_test, preds)
    precision = precision_score(y_test, preds)
    recall = recall_score(y_test, preds)
    f1 = f1_score(y_test, preds)

    mlflow.log_param("pipeline", "scaler + randomforest")
    mlflow.log_param("test_size", 0.2)
    mlflow.log_param("random_state", 42)

    mlflow.log_metric("accuracy", acc)
    mlflow.log_metric("precision", precision)
    mlflow.log_metric("recall", recall)
    mlflow.log_metric("f1_score", f1)

    mlflow.set_tag("stage", "pipeline")
    mlflow.set_tag("dataset", "tmdb_5000_movies")

    mlflow.sklearn.log_model(pipeline, "model")

    print("Pipeline Accuracy:", acc)
    print("F1 Score:", f1)