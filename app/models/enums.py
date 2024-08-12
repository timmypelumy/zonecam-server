from enum import Enum, unique, StrEnum


class UserType(StrEnum):
    organization = "ORGANIZATION"
    individual = "INDIVIDUAL"


class OperationTypes(StrEnum):
    signup = "SIGNUP"
    password_reset = "PASSWORD_RESET"
    email_verify = "EMAIL_VERIFY"
    email_change = "EMAIL_CHANGE"
    phone_change = "PHONE_CHANGE"
    phone_verify = "PHONE_VERIFY"
    phone_reset = "PHONE_RESET"


@unique
class LabelClasses(str, Enum):
    AFRICAN = "AFRICAN"
    ASIAN = "ASIAN"
    AMERICAN = "AMERICAN"
    EUROPEAN = "EUROPEAN"
    OTHER = "OTHER"
