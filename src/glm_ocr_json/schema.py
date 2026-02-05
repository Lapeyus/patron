from typing import List, Optional
import re
from pydantic import BaseModel, Field, field_validator, model_validator


DURATION_KEYWORDS = {
    "1 hora": ["1 hora", "1hr", "1 hr", "1h", "una hora"],
    "2 horas": ["2 horas", "2hr", "2 hrs", "2h", "dos horas"],
    "3 horas": ["3 horas", "3hr", "3 hrs", "3h", "tres horas"],
    "Toda la noche": [
        "toda la noche",
        "toda la noche completa",
        "overnight",
        "noche completa",
        "de 9:00 pm a 7:00 am",
        "de 9 pm a 7 am",
        "de 7 pm a 8 am",
        "de 9 pm a 6 am",
        "de 9pm a 7am",
    ],
}


def normalize_duration_label(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = re.sub(r"\s+", " ", str(value).strip().lower())
    for canonical, patterns in DURATION_KEYWORDS.items():
        for pattern in patterns:
            if pattern in normalized:
                return canonical
    return None


class Price(BaseModel):
    duration: Optional[str] = Field(None, description="Duration of service, e.g. '1 hour', '2 hours'")
    amount: int = Field(..., description="Numeric amount")
    currency: str = Field(..., description="Currency code, e.g. 'USD', 'CRC'")

    @field_validator('currency', mode='before')
    @classmethod
    def normalize_currency(cls, v):
        if isinstance(v, str):
            v_upper = v.upper().strip()
            # Common OCR hallucinations for Colones/CRC in this context
            if v_upper in ('EUR', 'EURO', 'E'): 
                return 'CRC'
            if 'COLON' in v_upper:
                return 'CRC'
            if '$' in v_upper or 'DOL' in v_upper or 'USD' in v_upper:
                return 'USD'
        return v

    @field_validator('duration', mode='before')
    @classmethod
    def normalize_duration(cls, v):
        canonical = normalize_duration_label(v)
        if canonical:
            return canonical
        return v

class Contact(BaseModel):
    whatsapp: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    social: Optional[str] = None

class Attributes(BaseModel):
    height: Optional[str] = None
    weight: Optional[str] = None
    measurements: Optional[str] = None
    hair_color: Optional[str] = None
    eye_color: Optional[str] = None
    implants: Optional[bool] = None

class StandardPrices(BaseModel):
    one_hour: Optional[int] = None
    two_hours: Optional[int] = None
    three_hours: Optional[int] = None
    overnight: Optional[int] = None

class ProfileSchema(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    location: Optional[str] = None
    prices: List[Price] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)
    contact: Contact = Field(default_factory=Contact)
    attributes: Attributes = Field(default_factory=Attributes)
    raw_text: str = Field(..., description="Summary of the profile text")
    standard_prices: StandardPrices = Field(default_factory=StandardPrices)

    @model_validator(mode="after")
    def populate_standard_prices(cls, model: "ProfileSchema") -> "ProfileSchema":
        mapping = {
            "1 hora": "one_hour",
            "2 horas": "two_hours",
            "3 horas": "three_hours",
            "Toda la noche": "overnight",
        }
        for price in model.prices:
            label = normalize_duration_label(price.duration)
            if not label:
                continue
            attr = mapping.get(label)
            if not attr:
                continue
            if getattr(model.standard_prices, attr) is None:
                setattr(model.standard_prices, attr, price.amount)
        return model
