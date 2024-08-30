from enum import Enum, unique, StrEnum


@unique
class Genders(StrEnum):
    male = "M"
    female = "F"


class OperationTypes(StrEnum):
    signup = "SIGNUP"
    password_reset = "PASSWORD_RESET"
    email_verify = "EMAIL_VERIFY"
    email_change = "EMAIL_CHANGE"
    phone_change = "PHONE_CHANGE"
    phone_verify = "PHONE_VERIFY"
    phone_reset = "PHONE_RESET"


@unique
class LabelClasses2(str, Enum):
    AFRICAN = "AFRICAN"
    ASIAN = "ASIAN"
    AMERICAN = "AMERICAN"
    EUROPEAN = "EUROPEAN"
    OTHER = "OTHER"


@unique
class LabelClasses(str, Enum):
    NORTH_CENTRAL = "North Central"
    NORTH_EAST = "North East"
    NORTH_WEST = "North West"
    SOUTH_EAST = "South East"
    SOUTH_SOUTH = "South South"
    SOUTH_WEST = "South West"
    OTHER = "Other"
