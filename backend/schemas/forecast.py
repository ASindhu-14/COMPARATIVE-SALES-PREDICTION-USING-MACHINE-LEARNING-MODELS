#schemas/forecast.py
from datetime import date

from pydantic import BaseModel, model_validator


class ForecastRequest(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("End date cannot be earlier than start date.")

        return self