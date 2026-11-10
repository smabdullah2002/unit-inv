from datetime import datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.unit import UnitType


class UnitBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unit name, e.g. Kilogram",
        examples=["Kilogram"],
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Unit code, e.g. kg",
        examples=["kg"],
    )
    type: UnitType = Field(
        ...,
        description="Unit type (weight, volume, count)",
        examples=[UnitType.weight],
    )
    is_active: bool = Field(
        default=True,
        description="Whether the unit is active",
        examples=[True],
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Unit name cannot be empty or only whitespace")
        return trimmed

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not cleaned:
            raise ValueError("Unit code cannot be empty or only whitespace")
        return cleaned


class UnitCreate(UnitBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Kilogram",
                "code": "kg",
                "type": "weight",
                "is_active": True,
            }
        }
    )


class UnitUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50, examples=["Liter"])
    code: Optional[str] = Field(None, min_length=1, max_length=10, examples=["l"])
    type: Optional[UnitType] = Field(None, examples=[UnitType.volume])
    is_active: Optional[bool] = Field(None, examples=[False])

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Unit name cannot be empty or only whitespace")
            return trimmed
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip().lower()
            if not cleaned:
                raise ValueError("Unit code cannot be empty or only whitespace")
            return cleaned
        return v

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "UnitUpdate":
        if self.name is None and self.code is None and self.type is None and self.is_active is None:
            raise ValueError("At least one field must be provided for update")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Gram",
                "code": "g",
                "type": "weight",
                "is_active": True,
            }
        }
    )


class UnitOut(BaseModel):
    id: UUID = Field(..., examples=["123e4567-e89b-12d3-a456-426614174000"])
    branch_id: UUID = Field(..., examples=["123e4567-e89b-12d3-a456-426614174001"])
    name: str = Field(..., examples=["Kilogram"])
    code: str = Field(..., examples=["kg"])
    type: UnitType = Field(..., examples=[UnitType.weight])
    is_active: bool = Field(..., examples=[True])
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "branch_id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "Kilogram",
                "code": "kg",
                "type": "weight",
                "is_active": True,
                "created_at": "2026-11-10T12:00:00Z",
                "updated_at": "2026-11-10T12:00:00Z",
            }
        },
    )


class UnitListQuery(BaseModel):
    type: Optional[UnitType] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None
    branch_id: Optional[UUID] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Literal["name", "code", "created_at"] = "name"
    order: Literal["asc", "desc"] = "asc"

