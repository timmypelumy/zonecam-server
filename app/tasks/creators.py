from pydantic import EmailStr
from huey.exceptions import CancelExecution
from .setup import huey
from app.config.settings import get_settings
from app.utils.emails.send_email import dispatch_email
from app.config.settings import get_settings
from app.database import cols
from app.models.predictor import PredictionResult, ResultItem
from datetime import timedelta
from app.utils.helpers import predict_image
from tensorflow.keras.models import load_model


settings = get_settings()

model = None


try:
    model = load_model(settings.ml_model_path)
    print("Model loaded successfully")
except Exception as e:
    raise Exception("Error loading model: ", e)


@huey.task(retries=1, retry_delay=20, name="task_predict_images", expires=timedelta(minutes=5))
def task_predict_image(data:  dict):

    x = predict_image(model, data)

    if x is None:
        raise CancelExecution()

    r = PredictionResult(prediction_request_id=x["prediction_request_id"], result=ResultItem(
            image_string=data["image_str"],
            image_id=x["image_id"], label_class=x["label"]))

  
    cols.prediction_results.insert_one(r.model_dump())

    if settings.debug:

        print("Prediction: ", r)


@huey.task(retries=2,  retry_delay=15, name="task_send_email")
def task_send_email(email_type:  str, email_to:  EmailStr | list[EmailStr], email_data:  dict):

    email_data.update({
        "support_email": settings.support_email
    })

    try:

        dispatch_email(email_to, email_type, email_data)

    except:

        raise CancelExecution()
