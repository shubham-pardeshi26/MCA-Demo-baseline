import pandas as pd
import mlflow
import mlflow.sklearn

from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
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

params = {
    "n_estimators": [50, 100, 200],
    "max_depth": [5, 10, None]
}

grid = GridSearchCV(RandomForestClassifier(), params, cv=3, scoring="accuracy")

with mlflow.start_run(run_name="rf_tuning"):

    grid.fit(X_train, y_train)

    best_model = grid.best_estimator_

    preds = best_model.predict(X_test)

    acc = accuracy_score(y_test, preds)
    precision = precision_score(y_test, preds)
    recall = recall_score(y_test, preds)
    f1 = f1_score(y_test, preds)

    mlflow.log_params(grid.best_params_)
    mlflow.log_param("cv_folds", 3)

    mlflow.log_metric("best_cv_score", grid.best_score_)
    mlflow.log_metric("accuracy", acc)
    mlflow.log_metric("precision", precision)
    mlflow.log_metric("recall", recall)
    mlflow.log_metric("f1_score", f1)

    mlflow.set_tag("stage", "tuning")
    mlflow.set_tag("dataset", "tmdb_5000_movies")

    mlflow.sklearn.log_model(best_model, "model")

    print("Best params:", grid.best_params_)
    print("Best CV Score:", grid.best_score_)
    print("Test Accuracy:", acc)
    print("F1 Score:", f1)