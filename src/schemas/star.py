from typing import Optional

from pydantic import BaseModel


class StarCreateSchema(BaseModel):
    name: str

    class Config:
        from_attributes = True


class StarListSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class StarUpdateSchema(BaseModel):
    name: Optional[str] = None

    model_config = {"from_attributes": True}
