from pydantic import BaseModel


class PlaceReq(BaseModel):
    location: tuple[float, float] = (34.726, 135.236)
    radius: int | None = 1000


class Place(BaseModel):
    ref_id: str
    name: str
    addr: str
    lat: float  # 緯度
    lng: float  # 経度
    photo_ref: str | None


class User(BaseModel):
    user_id: str
    username: str


class Coupon(BaseModel):
    place: Place
    discount_rate: float | None  # xx % off
    constant_discount: int | None  # ￥xx off
    description: str  # 説明
    title: str


# class UserInDB(User):
#     hashed_password: str
