import pandas as pd
from backend.database import SessionLocal
from backend.models import Transaction

df = pd.read_excel("Superstore.xlsx", sheet_name="Orders")
df["Order Date"] = pd.to_datetime(df["Order Date"]).dt.date
df["Ship Date"] = pd.to_datetime(df["Ship Date"]).dt.date
df.dropna(subset=["Sales", "Profit"], inplace=True)

session = SessionLocal()

transactions = [
    Transaction(
        order_date=row["Order Date"],
        ship_date=row["Ship Date"],
        ship_mode=row["Ship Mode"],
        segment=row["Segment"],
        country=row["Country"],
        state=row["State"],
        region=row["Region"],
        category=row["Category"],
        sub_category=row["Sub-Category"],
        quantity=row["Quantity"],
        discount=row["Discount"],
        sales=row["Sales"],
        profit=row["Profit"],
    )
    for _, row in df.iterrows()
]

session.bulk_save_objects(transactions)
session.commit()
session.close()

print(f"Loaded {len(transactions)} rows into the transactions table.")