from datetime import date
from pathlib import Path

import joblib
import pandas as pd


# ---------------------------------------------------------
# 1. Locate the trained forecasting model
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    BASE_DIR
    / "backend"
    / "ml"
    / "sales_forecast_model.pkl"
)

model = joblib.load(MODEL_PATH)


# ---------------------------------------------------------
# 2. Forecast future sales
# ---------------------------------------------------------

def forecast_sales(
    start_date: date,
    end_date: date
):
    """
    Forecast sales for every day between start_date
    and end_date.
    """

    # ---------------------------------------------
    # Validate dates
    # ---------------------------------------------

    if end_date < start_date:
        raise ValueError(
            "End date cannot be earlier than start date."
        )


    # ---------------------------------------------
    # Create future dates
    # ---------------------------------------------

    future_dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq="D"
    )


    # ---------------------------------------------
    # Load historical data
    # ---------------------------------------------

    data_path = (
        BASE_DIR
        / "data"
        / "Superstore.xlsx"
    )

    df = pd.read_excel(
        data_path,
        sheet_name="Orders"
    )

    df["Order Date"] = pd.to_datetime(
        df["Order Date"]
    )


    # ---------------------------------------------
    # Create daily historical sales
    # ---------------------------------------------

    daily_sales = (
        df.groupby("Order Date")["Sales"]
          .sum()
          .sort_index()
    )


    # ---------------------------------------------
    # Create continuous daily history
    # ---------------------------------------------

    full_dates = pd.date_range(
        start=daily_sales.index.min(),
        end=daily_sales.index.max(),
        freq="D"
    )

    daily_sales = (
        daily_sales
        .reindex(full_dates)
        .fillna(0)
    )


    # ---------------------------------------------
    # Store predictions here
    # ---------------------------------------------

    predictions = []


    # ---------------------------------------------
    # Recursive forecasting
    # ---------------------------------------------

    for current_date in future_dates:

        # Previous day's sales
        lag_1 = daily_sales.iloc[-1]


        # Sales from 7 days ago
        lag_7 = daily_sales.iloc[-7]


        # Average sales over previous 7 days
        rolling_7_mean = (
            daily_sales
            .iloc[-7:]
            .mean()
        )


        # Calendar features
        day_of_week = current_date.dayofweek

        month = current_date.month

        is_weekend = int(
            day_of_week in [5, 6]
        )

        is_holiday = int(
            month in [11, 12]
        )


        # -----------------------------------------
        # Create model input
        # -----------------------------------------

        X_future = pd.DataFrame([{
            "day_of_week": day_of_week,
            "month": month,
            "is_weekend": is_weekend,
            "is_holiday": is_holiday,
            "lag_1": lag_1,
            "lag_7": lag_7,
            "rolling_7_mean": rolling_7_mean
        }])


        # -----------------------------------------
        # Predict this day
        # -----------------------------------------

        prediction = float(
            model.predict(X_future)[0]
        )


        # Prevent negative sales predictions
        prediction = max(0, prediction)


        # -----------------------------------------
        # Store prediction
        # -----------------------------------------

        predictions.append({
            "date": current_date.date(),
            "predicted_sales": round(
                prediction,
                2
            )
        })


        # -----------------------------------------
        # Add prediction to history
        # -----------------------------------------

        # This allows tomorrow's prediction
        # to use today's prediction as lag_1.
        daily_sales.loc[current_date] = prediction


    # -----------------------------------------------------
    # Create final result
    # -----------------------------------------------------

    total_forecast = sum(
        item["predicted_sales"]
        for item in predictions
    )


    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_forecast": round(
            total_forecast,
            2
        ),
        "daily_forecast": predictions
    }