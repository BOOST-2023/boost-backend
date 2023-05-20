import aiohttp
import googlemaps
import logging
import os
import uvicorn
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware


from mytypes import Place, PlaceReq, User#, UserInDB

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                    )

GMAPKEY = os.environ.get("GMAPKEY")
gmaps = googlemaps.Client(key=GMAPKEY)

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="logintest")

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
        image_url = f'https://maps.googleapis.com/maps/api/place/photo?photo_reference={photo_ref}&maxheight={300}&key={GMAPKEY}'
        async with session.get(image_url) as resp:
            c_types = resp.headers.get('Content-Type')
            image = await resp.read()

    # print(image)
    return Response(content=image, media_type=c_types)


@app.post("/places")
async def get_places(place_req: PlaceReq) -> list[Place]:
    results = gmaps.places_nearby(location=place_req.location, radius=place_req.radius, type='restaurant')
    places = []
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
        # print(place)
        places.append(place)
    return places


def fake_decode_token(token):
    def get_user(db, username: str):
        if username in db:
            user_dict = db[username]
            return user_dict #UserInDB(**user_dict)

    # This doesn't provide any security at all
    # Check the next version
    user = get_user(fake_users_db, token)
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


@app.post("/logintest")
async def logintest(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
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
    if not user_id:
        user_data = None
    else:
        user_data = fake_users_db.get(user_id)

    if not user_data:
        # TODO create new account
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    user = User(**user_data)  # ** means unpacking the dict
    return {"access_token": user.user_id, "token_type": "bearer", "username": user.username}


@app.get("/users/me")
async def read_users_me(
        current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user


fake_users_db = {
    "114514": {
        "username": "senpai",
    },
    "alice": {
        "username": "alice",
    },
}

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)
