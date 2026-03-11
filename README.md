# Movie Hit Prediction — End-to-End ML Project

A complete Machine Learning pipeline that predicts whether a movie will be a **box office hit or flop** based on production metrics from the TMDB 5000 Movies dataset.

The project covers every stage of a real ML workflow:
**Data Ingestion → Preprocessing → Training → Experiment Tracking → Model Export → REST API Inference**

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Project Structure](#2-project-structure)
3. [Dataset](#3-dataset)
4. [Setup & Installation](#4-setup--installation)
5. [Running the Pipeline](#5-running-the-pipeline)
   - [Step 1 — Data Ingestion](#step-1--data-ingestion)
   - [Step 2 — Preprocessing](#step-2--preprocessing)
   - [Step 3 — Training](#step-3--training)
   - [Step 4 — Export Model](#step-4--export-model)
   - [Step 5 — Start the API](#step-5--start-the-api)
6. [API Reference](#6-api-reference)
7. [MLflow Experiment Tracking](#7-mlflow-experiment-tracking)
8. [Model Performance](#8-model-performance)
9. [Extra — TMDB Live Service](#9-extra--tmdb-live-service)

---

## 1. Problem Statement

> **Can we predict whether a movie will earn more money than it cost to make?**

A movie is labelled a **Hit (1)** if its box office revenue exceeds its production budget, and a **Flop (0)** otherwise.

```
hit = 1  if  revenue > budget
hit = 0  if  revenue <= budget
```

This is a **binary classification** problem. We use five numerical features available before a movie releases to make the prediction.

---

## 2. Project Structure

```
MCA/
│
├── datasets/                      # Raw source files (do not modify)
│   ├── tmdb_5000_movies.csv       # Main movie data (budget, revenue, ratings, etc.)
│   └── tmdb_5000_credits.csv      # Cast & crew data (not used in training)
│
├── data/
│   ├── raw/
│   │   └── movies.csv             # Output of ingestion step
│   └── processed/
│       └── train.csv              # Output of preprocessing step (features + target)
│
├── ingestion/
│   └── ingest_data.py             # Copies raw dataset into data/raw/
│
├── processing/
│   └── preprocess.py              # Filters, creates target column, selects features
│
├── training/
│   ├── train_baseline.py          # Logistic Regression (baseline model)
│   ├── train_multiple_models.py   # Compares LR, Random Forest, Gradient Boosting
│   ├── train_pipeline.py          # StandardScaler + Random Forest in a Pipeline
│   └── train_tuning.py            # Hyperparameter tuning with GridSearchCV
│
├── api/
│   └── app.py                     # FastAPI inference server (6 endpoints)
│
├── models/
│   └── model.pkl                  # Saved model (created by export_model.py)
│
├── services/
│   └── tmdb_service.py            # Fetches live popular movies from TMDB API
│
├── artifacts/                     # MLflow artifact storage
├── mlruns/                        # MLflow run metadata
├── mlflow.db                      # MLflow SQLite tracking database
│
├── export_model.py                # Trains final model and saves to models/model.pkl
└── README.md
```

---

## 3. Dataset

**Source:** [TMDB 5000 Movie Dataset](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata)

| File | Description | Size |
|---|---|---|
| `tmdb_5000_movies.csv` | Budget, revenue, runtime, ratings, popularity | ~5.7 MB |
| `tmdb_5000_credits.csv` | Cast and crew information | ~40 MB |

After filtering out movies with missing budget/revenue data, approximately **3,000 movies** remain for training.

**Features used for prediction:**

| Feature | Type | Description | Example |
|---|---|---|---|
| `budget` | float | Production budget in USD | `150000000` |
| `runtime` | float | Movie duration in minutes | `120` |
| `vote_average` | float | TMDB average rating (0–10) | `7.5` |
| `vote_count` | int | Number of ratings on TMDB | `5000` |
| `popularity` | float | TMDB popularity score | `80.0` |

**Target column:**

| Value | Label | Meaning |
|---|---|---|
| `1` | Hit | Revenue > Budget |
| `0` | Flop | Revenue ≤ Budget |

---

## 4. Setup & Installation

### Prerequisites

- Python 3.9 or higher
- `pip`

### Create and activate virtual environment

```bash
python -m venv env-mca-demo
source env-mca-demo/bin/activate        # macOS / Linux
env-mca-demo\Scripts\activate           # Windows
```

### Install dependencies

```bash
pip install pandas scikit-learn mlflow fastapi uvicorn requests
```

---

## 5. Running the Pipeline

All commands must be run from the **project root** (`MCA/`) with the virtual environment activated.

---

### Step 1 — Data Ingestion

```bash
python ingestion/ingest_data.py
```

**What it does:**
- Reads `datasets/tmdb_5000_movies.csv`
- Copies it as-is to `data/raw/movies.csv`

**Output:** `data/raw/movies.csv`

---

### Step 2 — Preprocessing

```bash
python processing/preprocess.py
```

**What it does:**
1. Loads `data/raw/movies.csv`
2. Removes rows where `budget == 0` or `revenue == 0` (incomplete data)
3. Creates the target column: `hit = (revenue > budget).astype(int)`
4. Keeps only the 5 feature columns + `hit`
5. Saves the cleaned dataset

**Output:** `data/processed/train.csv`

**Resulting columns:** `budget, runtime, vote_average, vote_count, popularity, hit`

---

### Step 3 — Training

Four training scripts are provided, each demonstrating a different stage of the ML workflow. All runs are tracked in MLflow under the experiment **`movie_hit_prediction`**.

---

#### 3a. Baseline Model — Logistic Regression

```bash
python training/train_baseline.py
```

Trains a simple Logistic Regression model. This is the starting point — the minimum acceptable performance that other models must beat.

**Logged to MLflow:** accuracy, precision, recall, f1_score, model artifact

---

#### 3b. Model Comparison — LR vs RF vs Gradient Boosting

```bash
python training/train_multiple_models.py
```

Trains three models in a loop and logs each as a separate MLflow run:
- `LogisticRegression`
- `RandomForestClassifier`
- `GradientBoostingClassifier`

Use this to compare models side-by-side in the MLflow UI.

---

#### 3c. Pipeline Model — Scaler + Random Forest

```bash
python training/train_pipeline.py
```

Wraps `StandardScaler` and `RandomForestClassifier` inside a `sklearn.Pipeline`. This is the production-ready pattern — preprocessing and the model travel together as a single object, preventing data leakage.

**MLflow run name:** `pipeline_model`

---

#### 3d. Hyperparameter Tuning — GridSearchCV

```bash
python training/train_tuning.py
```

Uses `GridSearchCV` with 3-fold cross-validation to find the best Random Forest hyperparameters:

```python
params = {
    "n_estimators": [50, 100, 200],
    "max_depth": [5, 10, None]
}
```

**Logged to MLflow:** best params, best CV score, test accuracy, F1

---

### Step 4 — Export Model

```bash
python export_model.py
```

**What it does:**
- Trains a `StandardScaler + RandomForestClassifier` pipeline (n_estimators=100, max_depth=10)
- Evaluates on the 20% test split and prints metrics
- Saves the trained pipeline to `models/model.pkl`

This is the model that the API will load. **You must run this before starting the API.**

**Sample output:**
```
Loading data...
Training pipeline (StandardScaler + RandomForest)...

--- Evaluation on Test Set ---
  Accuracy : 0.7941
  Precision: 0.8309
  Recall   : 0.9141
  F1 Score : 0.8705

Model saved to models/model.pkl
```

---

### Step 5 — Start the API

```bash
uvicorn api.app:app --reload --port 8000
```

The API will be live at: **http://127.0.0.1:8000**

Interactive documentation (Swagger UI): **http://127.0.0.1:8000/docs**

---

## 6. API Reference

### `GET /`
Returns an overview of the API and all available endpoints.

```bash
curl http://127.0.0.1:8000/
```

---

### `GET /health`
Health check — confirms the API is running and the model is loaded.

```bash
curl http://127.0.0.1:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

---

### `GET /model/info`
Returns details about the trained model, features, and how confidence levels are defined.

```bash
curl http://127.0.0.1:8000/model/info
```

**Response:**
```json
{
  "model_type": "Random Forest Classifier",
  "preprocessing": "StandardScaler",
  "task": "Binary Classification",
  "target": {
    "column": "hit",
    "values": { "1": "Hit (revenue > budget)", "0": "Flop (revenue <= budget)" }
  },
  "features": {
    "budget": "Production budget in USD (e.g. 150000000)",
    "runtime": "Movie duration in minutes (e.g. 120)",
    "vote_average": "TMDB average rating 0–10 (e.g. 7.5)",
    "vote_count": "Number of TMDB votes (e.g. 5000)",
    "popularity": "TMDB popularity score (e.g. 80.0)"
  },
  "confidence_levels": {
    "High": "Hit probability >= 75%",
    "Medium": "Hit probability 55–74%",
    "Low": "Hit probability < 55%"
  }
}
```

---

### `GET /examples`
Returns live predictions on 3 pre-defined sample movies. No request body needed — perfect for a quick demo.

```bash
curl http://127.0.0.1:8000/examples
```

**Response:**
```json
{
  "examples": [
    {
      "name": "Blockbuster Action Film",
      "description": "Massive budget, critical acclaim, huge social buzz",
      "features": { "budget": 200000000, "runtime": 148, "vote_average": 8.1, "vote_count": 12000, "popularity": 180.5 },
      "prediction": "Hit",
      "hit_probability": 1.0
    },
    {
      "name": "Mid-Budget Drama",
      "description": "Moderate budget, decent rating, average popularity",
      "features": { "budget": 50000000, "runtime": 105, "vote_average": 6.8, "vote_count": 2500, "popularity": 35.0 },
      "prediction": "Hit",
      "hit_probability": 0.9875
    },
    {
      "name": "Low-Budget Indie",
      "description": "Small budget, mixed reviews, low visibility",
      "features": { "budget": 5000000, "runtime": 90, "vote_average": 5.2, "vote_count": 400, "popularity": 8.0 },
      "prediction": "Hit",
      "hit_probability": 0.8291
    }
  ]
}
```

---

### `POST /predict`
Predict a single movie. Returns the prediction, both class probabilities, and a confidence level.

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 200000000,
    "runtime": 148,
    "vote_average": 8.1,
    "vote_count": 12000,
    "popularity": 180.5
  }'
```

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `budget` | float | Yes | Production budget in USD (must be > 0) |
| `runtime` | float | Yes | Duration in minutes (must be > 0) |
| `vote_average` | float | Yes | TMDB rating, 0–10 |
| `vote_count` | int | Yes | Total TMDB votes (must be ≥ 0) |
| `popularity` | float | Yes | TMDB popularity score (must be ≥ 0) |

**Response:**
```json
{
  "prediction": "Hit",
  "verdict": "This movie is likely to earn more than its production budget.",
  "hit_probability": 1.0,
  "flop_probability": 0.0,
  "confidence": "High"
}
```

**Confidence levels:**

| Level | Condition |
|---|---|
| High | Hit probability ≥ 75% |
| Medium | Hit probability 55–74% |
| Low | Hit probability < 55% |

---

### `POST /predict/batch`
Predict multiple movies in a single request. Returns individual results plus a summary.

```bash
curl -X POST http://127.0.0.1:8000/predict/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"budget": 200000000, "runtime": 148, "vote_average": 8.1, "vote_count": 12000, "popularity": 180.5},
    {"budget": 50000000,  "runtime": 105, "vote_average": 6.8, "vote_count": 2500,  "popularity": 35.0},
    {"budget": 5000000,   "runtime": 90,  "vote_average": 5.2, "vote_count": 400,   "popularity": 8.0}
  ]'
```

**Response:**
```json
{
  "summary": {
    "total": 3,
    "hits": 3,
    "flops": 0,
    "hit_rate": "100.0%"
  },
  "predictions": [
    {
      "input": { "budget": 200000000, "runtime": 148, "vote_average": 8.1, "vote_count": 12000, "popularity": 180.5 },
      "prediction": "Hit",
      "hit_probability": 1.0
    },
    ...
  ]
}
```

---

## 7. MLflow Experiment Tracking

All training runs are automatically logged to MLflow. To open the MLflow UI:

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Then open **http://127.0.0.1:5000** in your browser.

**What you can see in MLflow:**

- All runs grouped under the experiment `movie_hit_prediction`
- For each run: parameters (model type, test size, hyperparams), metrics (accuracy, precision, recall, F1), and the saved model artifact
- Side-by-side comparison of all runs on a chart

**Runs created by each script:**

| Script | MLflow Run Name | Model |
|---|---|---|
| `train_baseline.py` | `baseline_logistic` | Logistic Regression |
| `train_multiple_models.py` | `LogisticRegression` | Logistic Regression |
| `train_multiple_models.py` | `RandomForest` | Random Forest |
| `train_multiple_models.py` | `GradientBoosting` | Gradient Boosting |
| `train_pipeline.py` | `pipeline_model` | StandardScaler + RF |
| `train_tuning.py` | `rf_tuning` | Tuned RF (GridSearchCV) |

---

## 8. Model Performance

The final model used in the API (`export_model.py`) is a **StandardScaler + Random Forest** pipeline trained on 80% of the data and evaluated on the remaining 20%:

| Metric | Score |
|---|---|
| Accuracy | 79.41% |
| Precision | 83.09% |
| Recall | 91.41% |
| F1 Score | 87.05% |

- **High Recall (91%)** — the model rarely misses actual hits.
- **High Precision (83%)** — when it predicts a hit, it's usually right.

---

## 9. Extra — TMDB Live Service

`services/tmdb_service.py` connects to the real TMDB API and fetches currently popular movies.

```bash
python services/tmdb_service.py
```

This prints the first popular movie's raw JSON from TMDB. It can be extended to feed real-time movie data into the `/predict` endpoint.

> **Note:** The file contains a TMDB Bearer token. Do not commit this to a public repository. Move it to an environment variable before sharing the code.

---

## Quick Reference — Full Pipeline in Order

```bash
# 1. Activate environment
source env-mca-demo/bin/activate

# 2. Ingest raw data
python ingestion/ingest_data.py

# 3. Preprocess
python processing/preprocess.py

# 4. (Optional) Run training experiments — all tracked in MLflow
python training/train_baseline.py
python training/train_multiple_models.py
python training/train_pipeline.py
python training/train_tuning.py

# 5. (Optional) View MLflow UI
mlflow ui --backend-store-uri sqlite:///mlflow.db
# Open http://127.0.0.1:5000

# 6. Export the final model
python export_model.py

# 7. Start the API
uvicorn api.app:app --reload --port 8000
# Open http://127.0.0.1:8000/docs
```
