import os
from uuid import uuid4
from fastapi import HTTPException
from datetime import datetime, timezone
from fastapi import status as status_codes
from app.config.settings import get_settings
import time
import requests
import phonenumbers
from tensorflow.keras.preprocessing import image
from app.models.enums import LabelClasses
import requests
import numpy as np
import base64
from io import BytesIO
from PIL import Image


settings = get_settings()

target_size = (224, 224)



# Function to preprocess and predict on a single image array
def predict_single_image(model, img_array, age, gender):
    img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    age = np.array([age])
    gender = np.array([gender])
    predictions = model.predict([img_array, age, gender])
    predicted_class_index = np.argmax(predictions, axis=1)
    return predicted_class_index


def predict_image(model, input_data: dict):


    try:
        image_str = input_data["image_str"]

        image_data = base64.b64decode(image_str)
        img = Image.open(BytesIO(image_data))

        # Convert the image to RGB if it has an alpha channel
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        img_array = image.img_to_array(img.resize(target_size))

        age = input_data["age"]

        gender = input_data["gender"]

        # Make prediction
        predicted_class_index = predict_single_image(model, img_array, age, gender)

        label = None

        if settings.debug:

            print("Predicted class index: ", predicted_class_index)

        if predicted_class_index == 0:
            label = LabelClasses.WHITE

        elif predicted_class_index == 1:
            label = LabelClasses.BLACK

        elif predicted_class_index == 2:
            label = LabelClasses.ASIAN

        elif predicted_class_index == 3:

            label = LabelClasses.INDIAN

        elif predicted_class_index == 4:
            label = LabelClasses.OTHERS

        #  prediction result
        r = {
            "label": label,
            "image_id": input_data["image_id"],
            "prediction_request_id": input_data["prediction_request_id"]
        }

        return r

    except Exception as e:

        if settings.debug:
            print("Error predicting images: ", e)

        return None



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
