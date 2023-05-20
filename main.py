from typing import Union, Annotated
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

import os, logging, random, string, googlemaps, uvicorn, aiohttp

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                    )

GMAPKEY = os.environ.get("GMAPKEY")
gmaps = googlemaps.Client(key=GMAPKEY)

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


@app.get("/")
async def read_root():  # token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": "token"}


class PlaceReq(BaseModel):
    location: tuple[float, float] = (34.726, 135.236)
    radius: int | None = 1000


class Place(BaseModel):
    name: str
    addr: str
    lat: float
    lng: float
    photo_ref: str | None


class PlaceList():
    to_sent: list[Place]


@app.get("/placephoto/{photo_ref}")
async def get_place_photo(photo_ref: str):
    results = gmaps.places_photo(photo_ref, max_width=512)
    with aiohttp.ClientSession() as session:
        async with session.get("http://schoolido.lu/api/cards/788/") as resp:
            data = await resp.json()
            card = data["card_image"]
            async with session.get(card) as resp2:
                test = await resp2.read()
                with open("cardtest2.png", "wb") as f:
                    f.write(test)
    print(results.read())
    return 'results'



@app.post("/places")
async def get_places(place_req: PlaceReq):
    results = gmaps.places_nearby(location=place_req.location, radius=place_req.radius, type='restaurant')
    places = PlaceList()
    places.to_sent = []
    for result in results["results"]:
        # Get the name and address of the restaurant
        try:
            photo_ref = result["photos"][0]["photo_reference"]
        except KeyError:
            photo_ref = None
        place = Place(
            name=result["name"],
            addr=result["vicinity"],
            lat=result["geometry"]["location"]["lat"],
            lng=result["geometry"]["location"]["lng"],
            photo_ref=photo_ref,
        )

        # Print the name and address
        print(place)
        places.to_sent.append(place)
    return places


def fake_decode_token(token):
    return User(
        username=token + "fakedecoded", email="john@example.com", full_name="John Doe"
    )


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    return user


@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


class LoginReq(BaseModel):
    user_id: str | None
    username: str | None


@app.post("/login")
async def login(login_req: LoginReq):
    _user_id = login_req.user_id

    if (not _user_id) and login_req.username:  # new user
        _user_id = ''.join(random.choices(string.ascii_lowercase, k=16))
        fake_users_db.update({
            _user_id: {
                "username": login_req.username
            }
        })
        return {"access_token": _user_id, "token_type": "bearer"}
    elif (not _user_id) and not login_req.username:
        raise HTTPException(status_code=400, detail="Invalid request")
    elif _user_id:
        user_dict = fake_users_db.get(_user_id)
        if user_dict is not None:  # user exists
            return {"access_token": _user_id, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=400, detail="User does not exist")


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "token": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "token": "fakehashedsecret2",
        "disabled": True,
    },
}

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)