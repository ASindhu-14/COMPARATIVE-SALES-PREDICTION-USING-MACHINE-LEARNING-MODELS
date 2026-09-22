from backend.database import Base, engine
from backend.models import Transaction, Prediction

# This looks at every class that inherits from Base (Transaction,
# Prediction) and creates a matching table in the actual database --
# if a table already exists, it's left alone, never overwritten.
Base.metadata.create_all(bind=engine)

print("Tables created successfully.")