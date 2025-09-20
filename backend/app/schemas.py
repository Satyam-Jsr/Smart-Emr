from typing import Optional

try:
    # Pydantic v2
    from pydantic import BaseModel
    class ConfigBase:
        model_config = {"from_attributes": True}

    class PatientSchema(BaseModel, ConfigBase):
        id: int
        name: str
        age: int
        last_visit: Optional[str] = None

    class PatientCreate(BaseModel):
        name: str
        age: int

except Exception:
    # Fallback for older pydantic versions
    from pydantic import BaseModel
    class PatientSchema(BaseModel):
        id: int
        name: str
        age: int
        last_visit: Optional[str] = None

        class Config:
            orm_mode = True

    class PatientCreate(BaseModel):
        name: str
        age: int

__all__ = ["PatientSchema", "PatientCreate"]
