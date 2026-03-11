from fastapi import FastAPI
import pickle
import pandas as pd

app = FastAPI()

model = pickle.load(open("model/model.pkl", "rb"))

@app.get("/")
def home():
    return {"message": "Movie Success Prediction API"}

@app.post("/predict")
def predict(data: dict):

    df = pd.DataFrame([data])

    prediction = model.predict(df)[0]

    result = "Hit" if prediction == 1 else "Flop"

    return {"prediction": result}