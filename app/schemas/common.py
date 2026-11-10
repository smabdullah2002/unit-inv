from typing import Generic, List, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int = Field(..., description="Total count of items matching the query")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")

