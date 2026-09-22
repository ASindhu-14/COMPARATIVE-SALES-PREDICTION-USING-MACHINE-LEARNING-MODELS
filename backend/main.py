#main.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import joblib
import pandas as pd
from pydantic import BaseModel, Field, model_validator
from datetime import date
from fastapi.middleware.cors import CORSMiddleware
from backend.database import SessionLocal
from backend.models import Prediction
from backend.schemas.forecast import ForecastRequest
from backend.services.forecasting import generate_forecast
from pathlib import Path

app = FastAPI(title="Order Value Estimator & Sales Forecast API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = Path(__file__).resolve().parent / "ml" / "sales_prediction_pipeline.pkl"
model = joblib.load(MODEL_PATH)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SalesInput(BaseModel):
    order_date: date
    ship_date: date
    ship_mode: str
    segment: str
    country: str
    state: str
    postal_code: float
    region: str
    category: str
    sub_category: str
    quantity: int = Field(gt=0)
    discount: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.ship_date < self.order_date:
            raise ValueError("Ship date cannot be earlier than order date.")
        return self


@app.get("/")
def home():
    return {"message": "Sales Prediction API is running"}


@app.post("/predict")
def predict(data: SalesInput, db: Session = Depends(get_db)):
    df = pd.DataFrame([{
        "Order Date": data.order_date, "Ship Date": data.ship_date,
        "Ship Mode": data.ship_mode, "Segment": data.segment,
        "Country": data.country, "State": data.state,
        "Postal Code": data.postal_code, "Region": data.region,
        "Category": data.category, "Sub-Category": data.sub_category,
        "Quantity": data.quantity, "Discount": data.discount
    }])
    df["Order Date"] = pd.to_datetime(df["Order Date"])
    df["Ship Date"] = pd.to_datetime(df["Ship Date"])
    df["Order Year"] = df["Order Date"].dt.year
    df["Order Month"] = df["Order Date"].dt.month
    df["Order Day"] = df["Order Date"].dt.day
    df["Order Weekday"] = df["Order Date"].dt.dayofweek
    df["Ship Year"] = df["Ship Date"].dt.year
    df["Ship Month"] = df["Ship Date"].dt.month
    df["Ship Day"] = df["Ship Date"].dt.day
    df["Ship Weekday"] = df["Ship Date"].dt.dayofweek
    df["is_holiday"] = ((df["Order Month"] == 11) | (df["Order Month"] == 12))
    df["is_weekend"] = df["Order Weekday"].isin([5, 6])
    expected_columns = model.named_steps['preprocessor'].feature_names_in_
    df = df[expected_columns]

    prediction = model.predict(df)
    predicted_value = round(float(prediction[0]), 2)

    log_entry = Prediction(
        ship_mode=data.ship_mode,
        segment=data.segment,
        category=data.category,
        sub_category=data.sub_category,
        region=data.region,
        quantity=data.quantity,
        discount=data.discount,
        predicted_sales=predicted_value,
        model_used=type(model.named_steps['model']).__name__,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return {
        "predicted_sales": predicted_value,
        "prediction_id": log_entry.id
    }


@app.get("/predictions")
def get_predictions(db: Session = Depends(get_db)):
    results = db.query(Prediction).order_by(Prediction.id.desc()).limit(20).all()
    return [
        {
            "id": p.id, "category": p.category, "region": p.region,
            "predicted_sales": p.predicted_sales, "model_used": p.model_used,
            "created_at": p.created_at
        }
        for p in results
    ]

@app.post("/forecast")
def forecast(request: ForecastRequest, db: Session = Depends(get_db)):
    results = generate_forecast(db, request.start_date, request.end_date)
    return {"forecast": results}