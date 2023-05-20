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
    ref_id: str
    title: str
    description: str  # 説明
    place: Place
    discount_rate: float | None  # xx % off
    constant_discount: int | None  # ￥xx off
    from_days: int
    until_days: int


class Mission(BaseModel):
    ref_id: str
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

    def update_last_location(self, new_location: tuple[float, float]):
        self.last_location = new_location
        self.update_user(self)

    def update_days(self, new_day: int | None):
        if new_day is None:
            new_day = self.days + 1
        self.days = new_day
        self.update_user(self)

    def update_coupons(self, new_coupons: list[Coupon]):
        # TODO: generate random mission here

        # self.coupons = new_coupons
        self.update_user(self)

    def update_missions(self):
        # TODO: generate random mission here

        self.update_user(self)

# class UserInDB(User):
#     hashed_password: str
