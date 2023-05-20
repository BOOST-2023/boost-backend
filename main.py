import aiohttp
import googlemaps
import logging
import os
import uvicorn
import random
import string
import gimei
from typing import Annotated
import random

from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

from mytypes import Place, PlaceReq, User, Coupon, PlaceDetails, Review
from datastore import init_db, get_user, update_user

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

GMAPKEY = os.environ.get("GMAPKEY")
gmaps = googlemaps.Client(key=GMAPKEY)

jap_name = gimei.Gimei()

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="loginform")

origins = [
    '*'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():  # token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": "token"}


@app.get("/placephoto/{photo_ref}")
async def get_place_photo(photo_ref: str) -> Response:
    # results = gmaps.places_photo(photo_ref, max_width=512)
    async with aiohttp.ClientSession() as session:
        image_url = f"https://maps.googleapis.com/maps/api/place/photo?photo_reference={photo_ref}&maxheight={300}&key={GMAPKEY}"
        async with session.get(image_url) as resp:
            c_types = resp.headers.get("Content-Type")
            image = await resp.read()

    # print(image)
    return Response(content=image, media_type=c_types)


@app.get("/placedetails/{ref_id}")
async def get_placedetails(ref_id: str) -> PlaceDetails:
    results = gmaps.place(
        place_id=ref_id, language='ja', #region="jp"
    )
    result = results["result"]
    # Get the name and address of the restaurant
    place = PlaceDetails(
        ref_id=result["place_id"],
        name=result["name"],
        addr=result["vicinity"],
        lat=result["geometry"]["location"]["lat"],
        lng=result["geometry"]["location"]["lng"],
        photo_ref=None,
        opening_time=result["opening_hours"]["weekday_text"],
        opening_now=result["opening_hours"]["open_now"],
        phone=result.get('international_phone_number'),
        types=result.get('types'),
        photo_refs=[photo.get('photo_reference') for photo in result.get('photos')],
        reviews=[Review(
            author=rev.get('author_name'),
            profile_photo=rev.get('profile_photo_url'),
            published_time=rev.get('time'),
            published_time_readable=rev.get('relative_time_description'),
            content=rev.get('text')
        ) for rev in result.get('reviews')],
    )

    # Print the name and address
    # print(place)
    return place


@app.post("/places")
async def get_places(place_req: PlaceReq) -> list[Place]:
    results = gmaps.places_nearby(
        location=place_req.location, radius=place_req.radius, type="restaurant"
    )
    places = []
    for result in results["results"]:
        # Get the name and address of the restaurant
        try:
            photo_ref = result["photos"][0]["photo_reference"]
        except KeyError:
            photo_ref = None
        place = Place(
            ref_id=result["reference"],
            name=result["name"],
            addr=result["vicinity"],
            lat=result["geometry"]["location"]["lat"],
            lng=result["geometry"]["location"]["lng"],
            photo_ref=photo_ref,
        )

        # Print the name and address
        # print(place)
        places.append(place)
    return places


def fake_decode_token(token):
    # def get_user(db, username: str):
    #     if username in db:
    #         user_dict = db[username]
    #         return user_dict  # UserInDB(**user_dict)

    # This doesn't provide any security at all
    # Check the next version
    user = get_user(token)
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
        current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user


@app.post("/loginform")
async def logintest(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    # logging.debug(form_data.username)
    return await login(form_data.username)
    user_data = fake_users_db.get(form_data.username)
    if not user_data:
        # TODO create new account
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    user = UserInDB(**user_data)  # ** means unpacking the dict
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}


@app.get("/login/{user_id}")
async def login(user_id: str | None):
    if user_id == '0':
        # TODO create new account
        new_user_id = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        new_username = gimei.Gimei().name.hiragana
        update_user(User(**{
            "user_id": new_user_id,
            "username": new_username
        }))
        user_data = get_user(new_user_id)
    else:
        user_data = get_user(user_id)
        if not user_data:
            # Account not exist
            raise HTTPException(status_code=400, detail="Account not exist")

    # user = User(**user_data)  # ** means unpacking the dict
    return {
        "access_token": user_data.user_id,
        "token_type": "bearer",
        "username": user_data.username,
    }


@app.get("/users/me")
async def read_users_me(
        current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user


@app.get("/coupons")
async def get_random_coupon(current_user: Annotated[User, Depends(get_current_active_user)]):
    place_list = get_places(place_req=place_req)
    random_place = random.choice(place_list)
    random_constant_discount = 100  # 100円割引券
    return Coupon(
        place=random_place,
        constant_discount=random_constant_discount,

    )


fake_users_db = {
    "114514": {
        "user_id": "114514",
        "username": "senpai",
    },
    "alice": {
        "user_id": "...",
    },
}

if __name__ == "__main__":
    init_db()
    uvicorn.run(app, host="127.0.0.1", port=8000)
