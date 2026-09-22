from datetime import date, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import joblib

from backend.models import Transaction

FEATURE_COLS = ['day_of_week', 'month', 'is_weekend', 'is_holiday', 'lag_1', 'lag_7', 'rolling_7_mean']

MODEL_PATH = Path(__file__).resolve().parents[1] / "ml" / "sales_forecast_model.pkl"
forecast_model = joblib.load(MODEL_PATH)


def _build_features(target_date, buffer):
    return pd.DataFrame([{
        "day_of_week": target_date.weekday(),
        "month": target_date.month,
        "is_weekend": int(target_date.weekday() in [5, 6]),
        "is_holiday": int(target_date.month in [11, 12]),
        "lag_1": buffer[-1],
        "lag_7": buffer[-7],
        "rolling_7_mean": sum(buffer[-7:]) / 7,
    }])[FEATURE_COLS]


def generate_forecast(db: Session, start_date: date, end_date: date):
    rows = (
        db.query(Transaction.order_date, func.sum(Transaction.sales).label("total"))
        .group_by(Transaction.order_date)
        .order_by(Transaction.order_date.asc())
        .all()
    )
    history = {r.order_date: float(r.total) for r in rows}
    last_historical_date = max(history.keys())
    sorted_dates = sorted(history.keys())
    buffer = [history[d] for d in sorted_dates[-7:]]

    results = []
    cursor = start_date
    while cursor <= end_date and cursor in history:
        results.append({"date": str(cursor), "sales": round(history[cursor], 2), "type": "actual"})
        cursor += timedelta(days=1)

    predict_date = max(last_historical_date + timedelta(days=1), start_date)
    while predict_date <= end_date:
        row = _build_features(predict_date, buffer)
        pred = float(forecast_model.predict(row)[0])
        buffer.append(pred)
        if predict_date >= start_date:
            results.append({"date": str(predict_date), "sales": round(pred, 2), "type": "predicted"})
        predict_date += timedelta(days=1)

    return sorted(results, key=lambda r: r["date"])