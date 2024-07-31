import os
from uuid import uuid4
from fastapi import HTTPException
from datetime import datetime, timezone
from fastapi import status as status_codes
from app.config.settings import get_settings
import time
import requests
import phonenumbers


settings = get_settings()


def debug_log(*args):
    if settings.debug:
        print("Debug-> ", args)


def is_phone_number(value):
    """checks whether  a phone number is valid or not"""

    try:
        res = phonenumbers.parse(value)
        return phonenumbers.is_valid_number(res)
    except phonenumbers.NumberParseException:
        return False


def make_url(frag, surfix="", base_url=""):

    if not base_url:
        return "{0}{1}".format(frag, surfix)

    return "{0}{1}{2}".format(base_url, frag, surfix)


def make_request(url, method, headers={}, body=None):
    _headers = {
        "accept": "application/json",
        "content-type": "application/json",
    }

    _headers.update(headers)

    response = requests.request(
        method=method, url=url, headers=_headers, json=body)

    status = response.status_code
    ok = response.ok

    if not ok:

        return ok, status, None

    data = response.json()

    return ok, status, data


def handle_response(ok, status, data, silent=True):
    if not ok:

        if not silent:
            raise HTTPException(400)

    if not (status >= status_codes.HTTP_200_OK and status < status_codes.HTTP_300_MULTIPLE_CHOICES):

        if not silent:
            raise HTTPException(400)

        return False

    if status == status_codes.HTTP_401_UNAUTHORIZED:

        if not silent:
            raise HTTPException(400)

        return False

    return True


def get_uuid4():
    return str(uuid4().hex)


def get_random_string(length: int = 32):
    return os.urandom(length).hex()


def get_utc_timestamp() -> float:
    return datetime.now(tz=timezone.utc).timestamp()


def get_utc_timestamp_with_zero_hours_mins_secs() -> float:
    now = datetime.now(tz=timezone.utc)
    return datetime(now.year, now.month, now.day, 0, 0, 0, 0, tzinfo=timezone.utc).timestamp()


def get_id(n=12):
    return os.urandom(n).hex()


def is_age_in_range(utc_float_time, min_age, max_age):
    # Calculate the current time in seconds since the epoch
    current_time = time.time()

    # Calculate the age in seconds
    age = current_time - utc_float_time

    # Convert age to years (assuming an average year has 365.25 days)
    age_years = age / (365.25 * 24 * 60 * 60)

    # Check if age is within the specified range
    return min_age <= age_years <= max_age
