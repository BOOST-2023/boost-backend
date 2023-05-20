from pydantic import BaseModel
from enum import Enum
import random


def random_string(length: int = 16):
    return "".join(
        random.choices(string.ascii_letters + string.digits, k=length)
    )


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
    place_type: str


class Review(BaseModel):
    author: str
    profile_photo: str
    published_time: int
    published_time_readable: str
    content: str


class PlaceDetails(Place):
    opening_time: list[str] | None
    opening_now: bool | None
    phone: str | None
    photo_refs: list[str] | None
    types: list[str] | None
    reviews: list[Review] | None


class Coupon(BaseModel):
    ref_id: str = random_string()
    title: str
    description: str  # 説明
    place: Place
    discount_rate: float | None  # xx % off
    constant_discount: int | None  # ￥xx off
    from_days: int
    until_days: int
    used: bool = False


class Mission(BaseModel):
    ref_id: str = random_string()
    title: str
    description: str  # 説明
    mission_type: int  # 1 for use coupon! 4 for sharing to friends
    target_coupon_ref_id: str | None
    from_days: int


class User(object):
    user_id: str
    username: str
    last_location: tuple[float, float] | None
    days: int = 0
    coupons: list[Coupon] = []
    missions: list[Mission] = []

    # update_user = None

    def __init__(self, **data):
        super().__init__()
        from datastore import update_user

        self.update_user = update_user
        self.user_id = data.get('user_id')
        self.username = data.get('username')
        self.days = 0
        self.coupons = []

    def update_last_location(self, new_location: PlaceReq):
        # update both coupons and missions when location changes
        self.last_location = new_location.location
        self.update_coupons()
        self.update_missions()
        self.update_user(self)

    def update_days(self, new_day: int | None = None):
        if new_day is None:
            new_day = self.days + 1
        self.days = new_day
        self.update_user(self)

    def update_coupons(self):
        # TODO: generate random mission here

        # self.coupons = new_coupons
        self.update_user(self)

    def update_missions(self):
        # TODO: generate random mission here

        self.update_user(self)

    def use_coupon(self, ref_id: str):  # mark a coupon as used. True for success
        # find corresponding coupon first
        target = None
        for c in self.coupons:
            if c.ref_id == ref_id:
                target = c
                break

        if target is None:
            # not found
            return False

        target.used = True
        self.update_user(self)
        return True



class PlaceType(str, Enum):
    tourist_attraction = "tourist_attraction"
    food = "food"
