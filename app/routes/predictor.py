from fastapi import APIRouter, Depends
from app.models.users import User
from app.models.predictor import *
from .deps import get_auth_user
from app.database import cols
from app.tasks.creators import task_predict_image


router = APIRouter(tags=["Predictor"])


@router.post("/results", response_model=list[PredictionResult])
async def get_prediction_results(prediction_requests_ids:  list[str], user:  User = Depends(get_auth_user)):

    query = {"prediction_request_id": {"$in": prediction_requests_ids}}

    cursor = cols.prediction_results.find(query)

    items = [PredictionResult(**x) for x in await cursor.to_list(length=None)]

    return items


@router.post("/predict", response_model=PredictionRequest)
async def predict_maize_disease(input_data:  PredictionData, user:  User = Depends(get_auth_user)):

    r = PredictionRequest(image_id=input_data.id, creator=user.uid)

    data = {
        "prediction_request_id": r.uid,
        "image_str": input_data.image_string,
        "image_id": input_data.id,
        "age": input_data.age,
        "gender": 1 if input_data.gender == Genders.female else 0
    }

    await cols.prediction_requests.insert_one(r.model_dump())

    task_predict_image(data)

    return r
