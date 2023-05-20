import logging
import pickle
from mytypes import User

USER_DB = {}


def init_db():
    global USER_DB
    try:
        with open('users.pkl', 'rb') as inp:
            USER_DB = pickle.load(inp)
    except OSError:
        logging.warning('No datastore exists, create a new one')
        __save_db()


def __save_db():
    return
    with open('users.pkl', 'wb') as outp:  # Overwrites any existing file.
        pickle.dump(USER_DB, outp, pickle.HIGHEST_PROTOCOL)


def get_user(user_id: str) -> User:
    return USER_DB.get(user_id)


def update_user(new_user: User):
    global USER_DB
    logging.info(f'updating user: {new_user}')
    USER_DB.update({
        new_user.user_id: new_user
    })
    __save_db()


