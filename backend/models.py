from sqlalchemy import Column, Integer, Float, String, Boolean, Date, DateTime, func
from backend.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    order_date = Column(Date)
    ship_date = Column(Date)
    ship_mode = Column(String)
    segment = Column(String)
    country = Column(String)
    state = Column(String)
    region = Column(String)
    category = Column(String)
    sub_category = Column(String)
    quantity = Column(Integer)
    discount = Column(Float)
    sales = Column(Float)
    profit = Column(Float)

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    ship_mode = Column(String)
    segment = Column(String)
    category = Column(String)
    sub_category = Column(String)
    region = Column(String)
    quantity = Column(Integer)
    discount = Column(Float)
    predicted_sales = Column(Float)
    model_used = Column(String)
    created_at = Column(DateTime, server_default=func.now())