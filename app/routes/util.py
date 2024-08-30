from fastapi import HTTPException, status
from app.database import cols
import numpy as np
import base64
from io import BytesIO
from PIL import Image
from app.models.enums import LabelClasses
import requests
from tensorflow.keras.preprocessing import image
from app.config.settings import get_settings


settings = get_settings()

target_size = (224, 224)


# Function to preprocess and predict on a single image array
def predict_single_image(model, img_array):
    img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    predictions = model.predict(img_array)
    predicted_class_index = np.argmax(predictions, axis=1)[0]
    return predicted_class_index


def predict_images(model, images: list[dict]):

    predictions = []

    try:

        for item in images:

            image_str = item["image_str"]

            image_data = base64.b64decode(image_str)
            img = Image.open(BytesIO(image_data))

            # Convert the image to RGB if it has an alpha channel
        if img.mode == 'RGBA':
            img = img.convert('RGB')

            img_array = image.img_to_array(img.resize(target_size))

            # Make prediction
            predicted_class_index = predict_single_image(model, img_array)

            label = None

            if settings.debug:

                print("Predicted class index: ", predicted_class_index)

            if predicted_class_index == 1:
                label = LabelClasses.NORTH_CENTRAL

            elif predicted_class_index == 2:
                label = LabelClasses.NORTH_EAST

            elif predicted_class_index == 3:
                label = LabelClasses.NORTH_WEST

            elif predicted_class_index == 4:

                label = LabelClasses.SOUTH_EAST

            elif predicted_class_index == 5:
                label = LabelClasses.SOUTH_SOUTH

            elif predicted_class_index == 6:
                label = LabelClasses.SOUTH_WEST

            else:
                label = LabelClasses.OTHER

            # if predicted_class_index == 0:
            #     label = LabelClasses.AFRICAN

            # elif predicted_class_index == 1:
            #     label = LabelClasses.AMERICAN

            # elif predicted_class_index == 2:
            #     label = LabelClasses.ASIAN

            # elif predicted_class_index == 3:

            #     label = LabelClasses.EUROPEAN

            # else:
            #     label = LabelClasses.OTHER

            # Append prediction result
            predictions.append({
                "label": label,
                "image_id": item["image_id"],
                "prediction_request_id": item["prediction_request_id"]
            })

        return predictions

    except Exception as e:

        if settings.debug:
            print("Error predicting images: ", e)

        return predictions


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
