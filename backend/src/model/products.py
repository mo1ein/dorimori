from pydantic import BaseModel
from datetime import datetime


# todo: fix these types none is set?
class ProductPayload(BaseModel):
    id: int
    name: str
    description: str
    material: str | None = None
    rating: float | None = None
    images: list[str]
    code: str
    brand_id: int | None = None
    brand_name: str | None = None
    category_id: int | None = None
    category_name: str | None = None
    gender_id: int | None = None
    gender_name: str | None = None
    shop_id: int
    shop_name: str
    link: str | None
    status: str
    colors: list[str] | None
    sizes: list[str] | None
    region: str
    currency: str
    current_price: float | None
    old_price: float | None
    off_percent: int | None
    update_date: datetime


class ProductPoint(BaseModel):
    id: int
    vector: list[float] | None
    payload: ProductPayload


class ListProductPoint(BaseModel):
    points: list[ProductPoint]
