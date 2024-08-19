from pydantic import BaseModel, Field
from pydantic_settings import SettingsConfigDict
from app.utils.helpers import get_uuid4, get_utc_timestamp
from .enums import LabelClasses, Genders


class PredictionData(BaseModel):
    id: str
    image_string: str = Field(alias="imageString")
    age : int = Field(alias="age", ge=0, le=200)
    gender : Genders = Field()

    model_config = SettingsConfigDict(populate_by_name=True)


class PredictionRequest(BaseModel):
    creator:  str = Field(alias="creator")
    uid: str = Field(default_factory=get_uuid4)
    image_id:  str = Field(min_length=1, alias="imageId")
    created_at: float = Field(
        default_factory=get_utc_timestamp, alias="createdAt")
    result_id:  str | None = Field(default=None, alias="resultId")

    model_config = SettingsConfigDict(populate_by_name=True)


class ResultItem(BaseModel):
    image_id:  str = Field(alias="imageId")
    label_class:  LabelClasses = Field(alias="labelClass")
    image_string: str | None = Field(None, alias="imageString")

    model_config = SettingsConfigDict(populate_by_name=True)


class PredictionResult(BaseModel):
    uid: str = Field(default_factory=get_uuid4)
    created_at: float = Field(
        default_factory=get_utc_timestamp, alias="createdAt")
    prediction_request_id:  str = Field(alias="predictionRequestId")
    result: ResultItem

    model_config = SettingsConfigDict(populate_by_name=True)
