from pydantic import BaseModel


class PlaceReq(BaseModel):
    location: tuple[float, float] = (34.726, 135.236)
    radius: int | None = 1000


class Place(BaseModel):
    name: str
    addr: str
    lat: float
    lng: float
    photo_ref: str | None


class User(BaseModel):
    user_id: str
    username: str


# class UserInDB(User):
#     hashed_password: str
