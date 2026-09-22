#train_forecast_model.py
import pandas as pd
import joblib
from pathlib import Path

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error


# ============================================================
# 1. PATHS
# ============================================================

# Project root:
# COMPARATIVE-SALES-PREDICTION-USING-MACHINE-LEARNING-MODELS/
BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = BASE_DIR / "data" / "Superstore.xlsx"

MODEL_PATH = (
    Path(__file__).resolve().parent
    / "sales_forecast_model.pkl"
)


# ============================================================
# 2. LOAD DATA
# ============================================================

df = pd.read_excel(
    DATA_PATH,
    sheet_name="Orders"
)

df["Order Date"] = pd.to_datetime(df["Order Date"])


# ============================================================
# 3. AGGREGATE SALES BY DAY
# ============================================================

daily_sales = (
    df.groupby("Order Date")["Sales"]
      .sum()
      .reset_index()
      .sort_values("Order Date")
)


# ============================================================
# 4. CREATE A CONTINUOUS DAILY DATE RANGE
# ============================================================

full_dates = pd.date_range(
    start=daily_sales["Order Date"].min(),
    end=daily_sales["Order Date"].max(),
    freq="D"
)

daily_sales = (
    daily_sales
    .set_index("Order Date")
    .reindex(full_dates)
)

daily_sales.index.name = "Order Date"

# If there were no transactions on a particular day,
# treat that day's sales as 0.
daily_sales["Sales"] = daily_sales["Sales"].fillna(0)

daily_sales = daily_sales.reset_index()


# ============================================================
# 5. CALENDAR FEATURES
# ============================================================

daily_sales["day_of_week"] = (
    daily_sales["Order Date"].dt.dayofweek
)

daily_sales["month"] = (
    daily_sales["Order Date"].dt.month
)

daily_sales["is_weekend"] = (
    daily_sales["day_of_week"]
    .isin([5, 6])
    .astype(int)
)

daily_sales["is_holiday"] = (
    daily_sales["month"]
    .isin([11, 12])
    .astype(int)
)


# ============================================================
# 6. LAG FEATURES
# ============================================================

# Sales from the previous calendar day
daily_sales["lag_1"] = (
    daily_sales["Sales"].shift(1)
)

# Sales from exactly 7 calendar days ago
daily_sales["lag_7"] = (
    daily_sales["Sales"].shift(7)
)


# ============================================================
# 7. ROLLING 7-DAY AVERAGE
# ============================================================

daily_sales["rolling_7_mean"] = (
    daily_sales["Sales"]
    .shift(1)
    .rolling(7)
    .mean()
)


# ============================================================
# 8. REMOVE ROWS WITHOUT ENOUGH HISTORY
# ============================================================

daily_sales = daily_sales.dropna()


# ============================================================
# 9. FEATURES AND TARGET
# ============================================================

features = [
    "day_of_week",
    "month",
    "is_weekend",
    "is_holiday",
    "lag_1",
    "lag_7",
    "rolling_7_mean"
]

X = daily_sales[features]

y = daily_sales["Sales"]


# ============================================================
# 10. CHRONOLOGICAL 80/20 SPLIT
# ============================================================

split_index = int(len(daily_sales) * 0.8)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]


print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))

print(
    "Training period:",
    daily_sales["Order Date"].iloc[0].date(),
    "to",
    daily_sales["Order Date"].iloc[split_index - 1].date()
)

print(
    "Testing period:",
    daily_sales["Order Date"].iloc[split_index].date(),
    "to",
    daily_sales["Order Date"].iloc[-1].date()
)


# ============================================================
# 11. TRAIN LINEAR REGRESSION
# ============================================================

model = LinearRegression()

model.fit(X_train, y_train)


# ============================================================
# 12. EVALUATE
# ============================================================

predictions = model.predict(X_test)

rmse = mean_squared_error(
    y_test,
    predictions
) ** 0.5

print()
print("Forecast model trained successfully.")
print(f"Test RMSE: {rmse:.2f}")


# ============================================================
# 13. SAVE MODEL
# ============================================================

joblib.dump(
    model,
    MODEL_PATH
)

print()
print(f"Saved: {MODEL_PATH}")

print(
    "Latest historical date:",
    daily_sales["Order Date"].max().date()
)