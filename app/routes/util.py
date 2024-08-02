from fastapi import HTTPException, status
from app.database import cols


def fetch_email_and_name(user: dict) -> tuple[str, str]:

    email = user["email"]
    name = user["first_name"]

    return email, name


async def fetch_user(id:  str,  is_uid:  bool = False):

    user = None

    if is_uid:
        user = await cols.users.find_one({"uid": id})

        return user

    user = await cols.users.find_one({"email": id})

    return user


def raise_bad_reqest(msg: str = "You request is invalid.", headers: dict = {}):
    raise HTTPException(status.HTTP_400_BAD_REQUEST, msg, headers)


def raise_unauthorized(msg: str = "You are not allowed to access this resource.", headers: dict = {}):
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, msg, headers)


def raise_forbidden_reqest(msg: str = "Your request is denied.", headers: dict = {}):
    raise HTTPException(status.HTTP_403_FORBIDDEN, msg, headers)


def raise_not_found(msg: str = "The resource you requested does not exist.", headers: dict = {}):
    raise HTTPException(status.HTTP_404_NOT_FOUND, msg, headers)


def raise_server_error(msg: str = "An error occured while processing your request.", headers: dict = {}):
    raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, msg, headers)


def debug_log(*msg):
    print(f"DEBUG: {msg}")
