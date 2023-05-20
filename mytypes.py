from pydantic import BaseModel
from enum import Enum
import random, string
import GPTcoupons

DAILY_MISSION_LENGTH = 31  # Day 0 to 30, total 31 days


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
    place_type: str  # restaurant, cafe, supermarket


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
    content: str  # 説明
    place: Place | None
    from_days: int
    used: bool = False
    type: str  # restaurant, cafe, supermarket, special


class Mission(BaseModel):
    ref_id: str = random_string()
    title: str
    content: str  # 説明
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
    saved_places: list[Place] = []

    # update_user = None

    def __init__(self, **data):
        super().__init__()
        from datastore import update_user

        self.update_user = update_user
        self.user_id = data.get('user_id')
        self.username = data.get('username')
        self.days = 0
        self.coupons = []

    def update_saved_places(self, new_places: list[Place]):  # save food places for generating coupons
        self.saved_places = new_places

    def update_last_location(self, new_location: PlaceReq):
        # update both coupons and missions when location changes
        self.last_location = new_location.location
        self.update_coupons()
        self.update_missions()
        self.update_user(self)

    def update_days(self, new_day: int | None = None):
        # TODO: Reset after 31 days
        if new_day is None:
            new_day = self.days + 1
        self.days = new_day
        self.update_missions()
        self.update_user(self)

    def update_coupons(self):
        #  generate random coupons here
        daily_coupon_amount = 3  # generate 3 coupons for one single day
        coupon_list = []
        for day_n in range(self.days, DAILY_MISSION_LENGTH):
            # generate the coupon from now to the last day
            for coupon_n in range(daily_coupon_amount):
                lucky_place = random.choice(self.saved_places)  # restaurant, cafe, supermarket
                if lucky_place.place_type == 'restaurant':
                    random_gpt_coupon = random.choice(GPTcoupons.restaurant_coupons)
                elif lucky_place.place_type == 'cafe':
                    random_gpt_coupon = random.choice(GPTcoupons.cafe_coupons)
                elif lucky_place.place_type == 'supermarket':
                    random_gpt_coupon = random.choice(GPTcoupons.restaurant_coupons)
                else:
                    random_gpt_coupon = random.choice(GPTcoupons.restaurant_coupons)

                new_coupon = Coupon(**{
                    'title': random_gpt_coupon['title'],
                    'content': random_gpt_coupon['content'],
                    'from_days': day_n,
                    'place': lucky_place,
                    'type': lucky_place.place_type
                })
                coupon_list.append(new_coupon)

            # 30% possibility to give away a special coupon
            if random.random() < 0.3:
                random_gpt_coupon = random.choice(GPTcoupons.special_coupons)
                new_coupon = Coupon(**{
                    'title': random_gpt_coupon['title'],
                    'content': random_gpt_coupon['content'],
                    'from_days': day_n,
                    'place': None,
                    'type': 'special'
                })
                coupon_list.append(new_coupon)

        # copy the old coupons before this day
        old_coupon_list = []
        for c in self.coupons:
            if c.from_days < self.days:
                old_coupon_list.append(c)
        new_coupons = old_coupon_list + coupon_list
        self.coupons = new_coupons
        self.update_user(self)

    def find_available_coupon_by_day(self, day: int) -> list[Coupon]:
        result = []
        for c in self.coupons:
            if c.from_days <= day and not c.used:
                result.append(c)
        return result

    def update_missions(self):
        # generate random mission here
        title_coupon_choice = [
            'クーポン券でお得になるチャンス！今すぐ使ってみましょう！',
            'クーポン券で幸せになれる方法！使わないと損ですよ！',
            'クーポン券で新しい発見をしよう！使ってみると驚きます！',
            'クーポン券で楽しくなる秘訣！使ってみると笑顔になれます！',
            'クーポン券で美しくなる方法！使ってみると魅力的になれます！',
        ]
        daily_mission_amount = 2  # generate 3 coupons for one single day
        mission_list = []
        for day_n in range(self.days, DAILY_MISSION_LENGTH):
            # 70% for coupon mission, 30% for sharing mission
            for mission_n in range(daily_mission_amount):
                if random.random() > 0.3:
                    lucky_coupon = random.choice(self.find_available_coupon_by_day(day_n))
                    new_mission = Mission(**{
                        'title': random.choice(title_coupon_choice),
                        'content': lucky_coupon.title,
                        'mission_type': 1,
                        'target_coupon_ref_id': lucky_coupon.ref_id,
                        'from_days': day_n
                    })
                else:
                    new_mission = Mission(**{
                        'title': '友たちを誘いましょう',
                        'content': '友たちを誘って，大きなことが始まる予感！',
                        'mission_type': 4,
                        'target_coupon_ref_id': None,
                        'from_days': day_n
                    })
                mission_list.append(new_mission)

        # copy the old coupons before this day
        old_mission_list = []
        for m in self.missions:
            if m.from_days < self.days:
                old_mission_list.append(m)
        new_missions = old_mission_list + mission_list

        self.missions = new_missions
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
