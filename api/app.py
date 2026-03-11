"""
Movie Hit Prediction API
Run with: uvicorn api.app:app --reload
Docs at:  http://127.0.0.1:8000/docs
"""
import pickle
from pathlib import Path
from typing import List

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Movie Hit Prediction API",
    description="""
Predict whether a movie will be a **box office hit or flop** based on its
production metrics from the TMDB 5000 Movies dataset.

## How it works
A **Random Forest** classifier (with StandardScaler) was trained on ~3000 movies.
A movie is labelled a **Hit** when its box office revenue exceeded its production budget.

## Features
| Feature | Description |
|---|---|
| `budget` | Production budget in USD |
| `runtime` | Duration in minutes |
| `vote_average` | TMDB average rating (0–10) |
| `vote_count` | Total votes on TMDB |
| `popularity` | TMDB popularity score |
""",
    version="1.0.0",
)

MODEL_PATH = Path("models/model.pkl")
model = None


@app.on_event("startup")
def load_model():
    global model
    if not MODEL_PATH.exists():
        raise RuntimeError(
            f"Model not found at '{MODEL_PATH}'. Run `python export_model.py` first."
        )
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    print(f"Model loaded from {MODEL_PATH}")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class MovieFeatures(BaseModel):
    budget: float = Field(
        ..., gt=0, description="Production budget in USD", examples=[150_000_000]
    )
    runtime: float = Field(
        ..., gt=0, description="Movie duration in minutes", examples=[120]
    )
    vote_average: float = Field(
        ..., ge=0, le=10, description="TMDB average rating (0–10)", examples=[7.5]
    )
    vote_count: int = Field(
        ..., ge=0, description="Total votes on TMDB", examples=[5000]
    )
    popularity: float = Field(
        ..., ge=0, description="TMDB popularity score", examples=[80.0]
    )


class PredictionResponse(BaseModel):
    prediction: str
    verdict: str
    hit_probability: float
    flop_probability: float
    confidence: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/", tags=["General"], summary="API overview")
def root():
    """Welcome endpoint — lists all available routes."""
    return {
        "api": "Movie Hit Prediction API",
        "version": "1.0.0",
        "endpoints": [
            "GET  /            - This overview",
            "GET  /health      - Health check",
            "GET  /model/info  - Model & feature details",
            "GET  /examples    - Live predictions on 3 sample movies",
            "POST /predict     - Predict a single movie",
            "POST /predict/batch - Predict multiple movies at once",
        ],
        "docs": "http://127.0.0.1:8000/docs",
    }


@app.get("/health", tags=["General"], summary="Health check")
def health():
    """Returns API health status and whether the model is loaded."""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
    }


@app.get("/model/info", tags=["Model"], summary="Model metadata")
def model_info():
    """Returns information about the trained model and the features it uses."""
    return {
        "model_type": "Random Forest Classifier",
        "preprocessing": "StandardScaler",
        "task": "Binary Classification",
        "target": {
            "column": "hit",
            "values": {"1": "Hit (revenue > budget)", "0": "Flop (revenue <= budget)"},
        },
        "features": {
            "budget": "Production budget in USD (e.g. 150000000)",
            "runtime": "Movie duration in minutes (e.g. 120)",
            "vote_average": "TMDB average rating 0–10 (e.g. 7.5)",
            "vote_count": "Number of TMDB votes (e.g. 5000)",
            "popularity": "TMDB popularity score (e.g. 80.0)",
        },
        "training_data": "TMDB 5000 Movies Dataset",
        "confidence_levels": {
            "High": "Hit probability >= 75%",
            "Medium": "Hit probability 55–74%",
            "Low": "Hit probability < 55%",
        },
    }


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"], summary="Predict a single movie")
def predict(movie: MovieFeatures):
    """
    Predict whether a single movie will be a hit or a flop.

    Returns the prediction, probabilities, and a confidence level.
    """
    df = pd.DataFrame([movie.model_dump()])
    prediction = int(model.predict(df)[0])
    proba = model.predict_proba(df)[0]

    hit_prob = round(float(proba[1]), 4)
    flop_prob = round(float(proba[0]), 4)

    if hit_prob >= 0.75:
        confidence = "High"
    elif hit_prob >= 0.55:
        confidence = "Medium"
    else:
        confidence = "Low"

    return PredictionResponse(
        prediction="Hit" if prediction == 1 else "Flop",
        verdict=(
            "This movie is likely to earn more than its production budget."
            if prediction == 1
            else "This movie may struggle to recoup its production budget."
        ),
        hit_probability=hit_prob,
        flop_probability=flop_prob,
        confidence=confidence,
    )


@app.post("/predict/batch", tags=["Prediction"], summary="Predict multiple movies")
def predict_batch(movies: List[MovieFeatures]):
    """
    Predict hit/flop for a list of movies in one request.

    Returns individual predictions plus a summary (total hits, flops, hit rate).
    """
    if not movies:
        raise HTTPException(status_code=400, detail="Movie list cannot be empty.")

    results = []
    for movie in movies:
        df = pd.DataFrame([movie.model_dump()])
        pred = int(model.predict(df)[0])
        proba = model.predict_proba(df)[0]
        results.append({
            "input": movie.model_dump(),
            "prediction": "Hit" if pred == 1 else "Flop",
            "hit_probability": round(float(proba[1]), 4),
        })

    hits = sum(1 for r in results if r["prediction"] == "Hit")
    total = len(results)

    return {
        "summary": {
            "total": total,
            "hits": hits,
            "flops": total - hits,
            "hit_rate": f"{round(hits / total * 100, 1)}%",
        },
        "predictions": results,
    }


@app.get("/examples", tags=["Prediction"], summary="Example predictions")
def examples():
    """
    Returns live predictions on 3 pre-defined sample movies.

    Great for a quick demo — no request body needed.
    """
    sample_movies = [
        {
            "name": "Blockbuster Action Film",
            "description": "Massive budget, critical acclaim, huge social buzz",
            "features": MovieFeatures(
                budget=200_000_000,
                runtime=148,
                vote_average=8.1,
                vote_count=12000,
                popularity=180.5,
            ),
        },
        {
            "name": "Mid-Budget Drama",
            "description": "Moderate budget, decent rating, average popularity",
            "features": MovieFeatures(
                budget=50_000_000,
                runtime=105,
                vote_average=6.8,
                vote_count=2500,
                popularity=35.0,
            ),
        },
        {
            "name": "Low-Budget Indie",
            "description": "Small budget, mixed reviews, low visibility",
            "features": MovieFeatures(
                budget=5_000_000,
                runtime=90,
                vote_average=5.2,
                vote_count=400,
                popularity=8.0,
            ),
        },
    ]

    enriched = []
    for movie in sample_movies:
        df = pd.DataFrame([movie["features"].model_dump()])
        pred = int(model.predict(df)[0])
        proba = model.predict_proba(df)[0]
        enriched.append({
            "name": movie["name"],
            "description": movie["description"],
            "features": movie["features"].model_dump(),
            "prediction": "Hit" if pred == 1 else "Flop",
            "hit_probability": round(float(proba[1]), 4),
        })

    return {"examples": enriched}
